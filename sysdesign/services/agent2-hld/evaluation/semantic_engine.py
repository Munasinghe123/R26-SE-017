"""
Evaluation — Semantic Engine

Frozen sentence-transformer singleton for deterministic semantic matching.
Used by RTS (requirement-component traceability) and CoS (responsibility cohesion).

Model: all-MiniLM-L6-v2 (384-dim embeddings, ~80MB)
Determinism: torch.use_deterministic_algorithms(True)
"""

import os
import logging
import numpy as np
from typing import Union

logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_engine_instance = None


class SemanticEngine:
    """Thread-safe, deterministic semantic embedding engine."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        import torch
        torch.use_deterministic_algorithms(True)
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading semantic model: {model_name}")
        self._model = SentenceTransformer(model_name)
        self._model.eval()
        self._cache: dict[str, np.ndarray] = {}
        # get_embedding_dimension() is the new name in sentence-transformers >= 3.x
        # getattr fallback keeps compatibility with older installs
        _dim_fn = getattr(self._model, "get_embedding_dimension", None) \
               or getattr(self._model, "get_sentence_embedding_dimension", None)
        logger.info(f"Semantic engine ready (dim={_dim_fn() if _dim_fn else '?'})")


    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string → 384-dim vector (cached)."""
        key = text.strip().lower()
        if key not in self._cache:
            vec = self._model.encode(key, convert_to_numpy=True, normalize_embeddings=True)
            self._cache[key] = vec.astype(np.float32)
        return self._cache[key]

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts → (N, 384) array."""
        normalized = [t.strip().lower() for t in texts]
        uncached = [t for t in normalized if t not in self._cache]

        if uncached:
            vecs = self._model.encode(uncached, convert_to_numpy=True, normalize_embeddings=True)
            for t, v in zip(uncached, vecs):
                self._cache[t] = v.astype(np.float32)

        return np.array([self._cache[t] for t in normalized])

    def cosine_sim(self, text_a: str, text_b: str) -> float:
        """Cosine similarity between two texts (range [-1, 1], typically [0, 1])."""
        vec_a = self.embed(text_a)
        vec_b = self.embed(text_b)
        # Vectors are already L2-normalized, so dot product = cosine similarity
        return float(np.dot(vec_a, vec_b))

    def pairwise_cohesion(self, texts: list[str]) -> float:
        """Mean pairwise cosine similarity across a list of texts.

        Returns 1.0 for single-text inputs (trivially cohesive).
        Returns 0.0 for empty inputs.
        """
        if len(texts) <= 1:
            return 1.0 if texts else 0.0

        vecs = self.embed_batch(texts)
        # Pairwise cosine sim matrix (vecs are normalized → dot product)
        sim_matrix = vecs @ vecs.T
        n = len(texts)

        # Extract upper triangle (excluding diagonal)
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                total += float(sim_matrix[i, j])
                count += 1

        return total / count if count > 0 else 1.0

    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()


def get_engine() -> SemanticEngine:
    """Get or create the global SemanticEngine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SemanticEngine()
    return _engine_instance
