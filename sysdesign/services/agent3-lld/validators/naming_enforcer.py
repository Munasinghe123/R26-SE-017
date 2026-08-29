import re
import logging
from typing import Optional
from schemas.ir_schema import IntermediateRepresentation
from schemas.api_models import NamingViolation

logger = logging.getLogger(__name__)


# ============================================================
# Naming Convention Rules
# ============================================================

def is_pascal_case(name: str) -> bool:
    """Check if name is PascalCase (e.g., OrderService)."""
    return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name)) and not name.isupper()


def is_camel_case(name: str) -> bool:
    """Check if name is camelCase (e.g., processPayment)."""
    return bool(re.match(r'^[a-z][a-zA-Z0-9]*$', name))


def is_snake_case(name: str) -> bool:
    """Check if name is snake_case (e.g., order_items)."""
    return bool(re.match(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$', name))


def to_pascal_case(name: str) -> str:
    """Convert to PascalCase."""
    if "_" in name:
        return "".join(word.capitalize() for word in name.split("_"))
    if name[0].islower():
        return name[0].upper() + name[1:]
    return name


def to_camel_case(name: str) -> str:
    """Convert to camelCase."""
    if "_" in name:
        parts = name.split("_")
        return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])
    if name[0].isupper():
        return name[0].lower() + name[1:]
    return name


def to_snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case."""
    # Insert underscore before uppercase letters
    s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    return s1.lower()


# ============================================================
# Synonym Detector
# ============================================================

class SynonymDetector:
    """
    Detects when the same concept uses different names across diagrams.
    Uses TF-IDF + cosine similarity to cluster similar terms.
    """

    def __init__(self, similarity_threshold: float = 0.7):
        self.threshold = similarity_threshold

    def find_similar_terms(self, terms: list[str]) -> list[tuple[str, str, float]]:
        """
        Find pairs of terms that are suspiciously similar.
        Returns: list of (term1, term2, similarity_score) tuples.
        """
        if len(terms) < 2:
            return []

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            logger.warning("scikit-learn not installed. Skipping synonym detection.")
            return []

        # Tokenize names by splitting camelCase/PascalCase/snake_case
        tokenized = []
        for term in terms:
            # Split by underscores, then by camelCase boundaries
            tokens = re.sub(r'([a-z])([A-Z])', r'\1 \2', term)
            tokens = tokens.replace("_", " ").lower()
            tokenized.append(tokens)

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        try:
            tfidf_matrix = vectorizer.fit_transform(tokenized)
        except ValueError:
            return []

        # Compute pairwise cosine similarity
        sim_matrix = cosine_similarity(tfidf_matrix)

        # Find pairs above threshold
        similar_pairs = []
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                score = sim_matrix[i][j]
                if score >= self.threshold and terms[i] != terms[j]:
                    similar_pairs.append((terms[i], terms[j], round(score, 3)))

        return similar_pairs


# ============================================================
# Global Naming Enforcer
# ============================================================

class NamingEnforcer:
    """
    Module 3: Enforces uniform naming conventions across all LLD artifacts.
    - Class names → PascalCase
    - Method names → camelCase
    - ER table names → snake_case
    - ER column names → snake_case

    Also detects potential synonym issues across diagrams.
    """

    def __init__(self):
        self.synonym_detector = SynonymDetector()

    def enforce(self, ir: IntermediateRepresentation) -> tuple[IntermediateRepresentation, list[NamingViolation]]:
        """
        Enforce naming conventions on the IR.
        Returns the corrected IR and a list of violations found.
        """
        violations: list[NamingViolation] = []

        # ------------------------------------------
        # 1. Class names → PascalCase
        # ------------------------------------------
        name_mapping = {}  # old → new for renaming references
        for cls in ir.classes:
            if not is_pascal_case(cls.name):
                old_name = cls.name
                new_name = to_pascal_case(cls.name)
                violations.append(NamingViolation(
                    location=f"Class: {old_name}",
                    current_name=old_name,
                    expected_name=new_name,
                    convention="PascalCase",
                    auto_fixed=True,
                ))
                name_mapping[old_name] = new_name
                cls.name = new_name

        # ------------------------------------------
        # 2. Method names → camelCase
        # ------------------------------------------
        for cls in ir.classes:
            for method in cls.methods:
                if not is_camel_case(method.name):
                    old_name = method.name
                    new_name = to_camel_case(method.name)
                    violations.append(NamingViolation(
                        location=f"Class '{cls.name}' method: {old_name}",
                        current_name=old_name,
                        expected_name=new_name,
                        convention="camelCase",
                        auto_fixed=True,
                    ))
                    method.name = new_name

        # ------------------------------------------
        # 3. ER table names → snake_case
        # ------------------------------------------
        entity_name_mapping = {}
        for entity in ir.entities:
            if not is_snake_case(entity.name):
                old_name = entity.name
                new_name = to_snake_case(entity.name)
                violations.append(NamingViolation(
                    location=f"Entity: {old_name}",
                    current_name=old_name,
                    expected_name=new_name,
                    convention="snake_case",
                    auto_fixed=True,
                ))
                entity_name_mapping[old_name] = new_name
                entity.name = new_name

        # ------------------------------------------
        # 4. ER column names → snake_case
        # ------------------------------------------
        for entity in ir.entities:
            for attr in entity.attributes:
                if not is_snake_case(attr.name):
                    old_name = attr.name
                    new_name = to_snake_case(attr.name)
                    violations.append(NamingViolation(
                        location=f"Entity '{entity.name}' column: {old_name}",
                        current_name=old_name,
                        expected_name=new_name,
                        convention="snake_case",
                        auto_fixed=True,
                    ))
                    attr.name = new_name

        # ------------------------------------------
        # 5. Update references (Sequence participants, relationships)
        # ------------------------------------------
        if name_mapping:
            for seq in ir.sequences:
                seq.participants = [
                    name_mapping.get(p, p) for p in seq.participants
                ]
                for msg in seq.messages:
                    msg.from_participant = name_mapping.get(msg.from_participant, msg.from_participant)
                    msg.to_participant = name_mapping.get(msg.to_participant, msg.to_participant)

            for cls in ir.classes:
                for rel in cls.relationships:
                    rel.target = name_mapping.get(rel.target, rel.target)

        if entity_name_mapping:
            for entity in ir.entities:
                for rel in entity.relationships:
                    rel.target = entity_name_mapping.get(rel.target, rel.target)
                # Also fix FK constraint references
                for attr in entity.attributes:
                    if attr.constraint.startswith("FK"):
                        for old, new in entity_name_mapping.items():
                            attr.constraint = attr.constraint.replace(old, new)

        # ------------------------------------------
        # 6. Synonym detection across diagrams
        # ------------------------------------------
        all_terms = []
        all_terms.extend(cls.name for cls in ir.classes)
        all_terms.extend(entity.name for entity in ir.entities)
        for seq in ir.sequences:
            all_terms.extend(seq.participants)

        similar_pairs = self.synonym_detector.find_similar_terms(list(set(all_terms)))
        for term1, term2, score in similar_pairs:
            violations.append(NamingViolation(
                location=f"Potential synonym: '{term1}' ↔ '{term2}'",
                current_name=f"{term1} / {term2}",
                expected_name=f"Use one consistent name (similarity: {score})",
                convention="Global Consistency",
                auto_fixed=False,
            ))

        logger.info(
            f"Naming enforcement complete: {len(violations)} violations found, "
            f"{sum(1 for v in violations if v.auto_fixed)} auto-fixed"
        )

        return ir, violations
