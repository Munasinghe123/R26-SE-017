"""
HLA Agent — Multi-Model LLM Architectural Generation Subsystem
=============================================================================
Academic Reference & Architectural Design:
- Concurrency Model: Multi-threaded asynchronous dispatch via concurrent.futures.ThreadPoolExecutor
- Synthesis Strategy: Multi-Model Diversity Mesh (LLaMA 3.3 70B, Qwen 2.5 Coder 32B, DeepSeek V3)
- Exploration vs Exploitation:
    * Candidate 1: Exploitation (seed=42, temp=0.10) -> High-conformity canonical synthesis
    * Candidate 2: Exploration  (seed=137, temp=0.55) -> Diverse structural alternative (ATAM trade-off)
- Resilience: Exponential backoff with non-retryable error classification and OpenRouter fallback routing
=============================================================================
"""

import time
import json
import logging
from typing import Optional

from config import (
    MODELS,
    MAX_CANDIDATES_PER_MODEL,
    GENERATION_OPTIONS,
    GENERATION_SEEDS,
    MAX_GENERATION_RETRIES,
)
from providers import get_provider_for_model

logger = logging.getLogger(__name__)


def _is_non_retryable_error(error: Exception) -> bool:
    """
    Classify exceptions to avoid wasting retries on non-transient failures.
    
    Transient (retryable): 429 Rate Limits, 503 Upstream Overload, Network Timeouts.
    Deterministic (non-retryable): 401 Auth Errors, 402 Insufficient Balance, 404 Route Not Found.
    """
    text = str(error).lower()

    # Rate-limiting, temporary upstream issues, and timeouts should ALWAYS be retried
    if any(m in text for m in ["rate-limited", "rate limit", "429", "temporarily", "timeout", "service unavailable"]):
        return False

    status = getattr(error, "status_code", None)
    if status in {401, 402, 403, 404}:
        return True

    non_retryable_markers = [
        "insufficient balance",
        "invalid api key",
        "authentication",
        "permission",
        "not found",
    ]
    return any(marker in text for marker in non_retryable_markers)


class GenerationResult:
    """Holds the result of one LLM generation attempt."""

    def __init__(self, model: str, candidate_num: int, raw_text: str,
                 success: bool, duration_ms: float, error: Optional[str] = None,
                 provider_name: str = "", attempts: Optional[list] = None):
        self.model = model
        self.candidate_num = candidate_num
        self.raw_text = raw_text
        self.success = success
        self.duration_ms = duration_ms
        self.error = error
        self.provider_name = provider_name
        self.attempts = attempts or []

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "candidate_num": self.candidate_num,
            "raw_text": self.raw_text,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "provider_name": self.provider_name,
            "attempts": self.attempts,
        }


def generate_single(model: str, prompt: str, candidate_num: int, options_override: dict | None = None) -> GenerationResult:
    """
    Generate a single architecture candidate from one model.

    Args:
        model: Model name (e.g., "meta-llama/llama-3.1-8b-instruct:free")
        prompt: Full structured prompt
        candidate_num: Which candidate number this is (1-based)
        options_override: Optional generation options (e.g., custom seed/temp)

    Returns:
        GenerationResult with raw text or error
    """
    provider = get_provider_for_model(model)
    last_error = "Unknown error"
    attempts = []

    options = {**GENERATION_OPTIONS}
    if candidate_num <= len(GENERATION_SEEDS):
        options["seed"] = GENERATION_SEEDS[candidate_num - 1]
    if options_override:
        options.update(options_override)

    for attempt in range(1, MAX_GENERATION_RETRIES + 1):
        try:
            logger.info(
                f"[{provider.provider_name}/{model}] Generating candidate {candidate_num}, "
                f"attempt {attempt}/{MAX_GENERATION_RETRIES} (seed={options.get('seed')})..."
            )

            start_time = time.time()
            attempts.append({
                "attempt": attempt,
                "status": "started",
                "timestamp": time.time(),
            })

            raw_text = provider.generate(prompt, model, options)

            duration_ms = (time.time() - start_time) * 1000

            if not raw_text:
                logger.warning(f"[{model}] Empty response on attempt {attempt}")
                attempts[-1]["status"] = "empty"
                continue

            attempts[-1]["status"] = "success"
            attempts[-1]["duration_ms"] = round(duration_ms, 2)
            attempts[-1]["chars"] = len(raw_text)

            logger.info(
                f"[{model}] Candidate {candidate_num} generated in {duration_ms:.0f}ms "
                f"({len(raw_text)} chars)"
            )

            return GenerationResult(
                model=model,
                candidate_num=candidate_num,
                raw_text=raw_text,
                success=True,
                duration_ms=duration_ms,
                provider_name=provider.provider_name,
                attempts=attempts,
            )

        except Exception as e:
            last_error = str(e)
            logger.error(f"[{model}] Attempt {attempt} failed: {e}")
            if attempts:
                attempts[-1]["status"] = "failed"
                attempts[-1]["error"] = str(e)

            if _is_non_retryable_error(e):
                logger.error(f"[{model}] Non-retryable error detected, aborting retries.")
                break

            if attempt < MAX_GENERATION_RETRIES:
                time.sleep(2 * attempt)  # Exponential backoff

    return GenerationResult(
        model=model,
        candidate_num=candidate_num,
        raw_text="",
        success=False,
        duration_ms=0,
        error=last_error,
        provider_name=provider.provider_name,
        attempts=attempts,
    )


def generate_all(requirements: dict, models: list = None,
                 candidates_per_model: int = None,
                 progress_callback=None) -> list[GenerationResult]:
    """
    Concurrent Multi-Model Synthesis Coordinator.
    
    Academic Rationale:
    Instead of sequential generation (which would take ~6x longer and bottleneck the pipeline),
    this function spawns worker threads via Python's ThreadPoolExecutor to query all model backends
    simultaneously. For 3 models with 2 candidates each (6 candidate slots total):
      - Slot 1 (Primary / Candidate 1): Focuses on optimal requirement alignment (Temp=0.10, Seed=42)
      - Slot 2 (Alternative / Candidate 2): Introduces architectural variation for ATAM trade-off (Temp=0.55, Seed=137)

    Args:
        requirements: Requirements dict containing FRs, NFRs, constraints, and business goals
        models: List of model identifiers (defaulting to LLaMA 3.3, Qwen 2.5 Coder, DeepSeek V3)
        candidates_per_model: Number of candidates per model family (defaults to 2)
        progress_callback: Optional progress listener streaming live generation state

    Returns:
        List of GenerationResult objects containing raw text, latency, and execution metadata
    """
    models = models or MODELS
    candidates_per_model = candidates_per_model or MAX_CANDIDATES_PER_MODEL

    from prompt.builder import build_architecture_prompt
    from concurrent.futures import ThreadPoolExecutor

    # Step 1: Pre-assemble generation tasks across the Model x Candidate matrix (e.g. 3 x 2 = 6 tasks)
    tasks = []
    for model in models:
        for candidate_num in range(1, candidates_per_model + 1):
            prompt = build_architecture_prompt(requirements, candidate_num=candidate_num)
            tasks.append((model, prompt, candidate_num))

    total = len(tasks)
    logger.info(f"Triggering parallel candidate generation for {total} tasks...")

    # Step 2: Define worker closure executing individual HTTP REST calls to OpenRouter
    def run_task(task_args):
        model, prompt, candidate_num = task_args
        if progress_callback:
            progress_callback(model, candidate_num, total, "generating")
        
        # Temperature Calibration:
        # Candidate 1 = 0.10 (strict determinism, minimal hallucination, canonical best-fit)
        # Candidate 2 = 0.55 (structural diversity, alternative architectural patterns)
        opts = {"temperature": 0.55} if candidate_num > 1 else None
        result = generate_single(model, prompt, candidate_num, options_override=opts)
        
        if progress_callback:
            status = "success" if result.success else "failed"
            progress_callback(model, candidate_num, total, status)
        return result

    # Step 3: Dispatch I/O-bound LLM API calls concurrently across thread pool
    with ThreadPoolExecutor(max_workers=min(total, 8)) as executor:
        results = list(executor.map(run_task, tasks))

    successful = sum(1 for r in results if r.success)
    logger.info(
        f"Generation complete: {successful}/{total} candidates generated successfully"
    )

    return results


def regenerate_single(model: str, prompt: str, candidate_num: int,
                      feedback: str) -> GenerationResult:
    """
    Regenerate a single candidate with feedback appended to the prompt.

    Args:
        model: Model name
        prompt: Original structured prompt
        candidate_num: Candidate number
        feedback: Feedback string from evaluation

    Returns:
        GenerationResult with improved architecture (hopefully)
    """
    enhanced_prompt = (
        f"{prompt}\n\n"
        f"⚠️ IMPORTANT — PREVIOUS ATTEMPT WAS REJECTED. Address these issues:\n"
        f"{feedback}\n"
        f"Generate an IMPROVED architecture that fixes these specific problems.\n"
        f"RESPOND WITH ONLY THE JSON. NO OTHER TEXT."
    )

    return generate_single(model, enhanced_prompt, candidate_num)


def check_models_available(models: list = None) -> dict:
    """
    Check which models are available by querying their specific providers.

    Returns:
        Dict of model_name → bool (available or not)
    """
    models = models or MODELS
    result = {}
    for m in models:
        try:
            provider = get_provider_for_model(m)
            # Call check_available on the specific provider for this model
            avail = provider.check_available([m])
            result[m] = avail.get(m, False)
        except Exception as e:
            logger.error(f"Failed to check model availability for {m}: {e}")
            result[m] = False
    return result

