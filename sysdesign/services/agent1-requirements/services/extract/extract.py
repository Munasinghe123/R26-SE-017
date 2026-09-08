"""
Multi-Stage Requirements Extraction Engine

Orchestrates the 4-stage extraction pipeline:
  Stage 1: Evidence Extraction (high recall, raw atomic stakeholder statements)
  Stage 2: Requirement Normalization (atomic requirements, traceability, clarification detection)
  Stage 3: Independent Classification (FR, NFR with ISO quality attributes, Uncertain)
  Stage 4: Deterministic Programmatic Checks (pure Python schema, traceability, duplicate & classification validation)
"""

import json
from typing import Dict, Any, List

from .stage1_evidence import extract_evidence
from .stage2_normalization import normalize_requirements
from .stage3_classification import classify_requirements
from .stage4_quality_checks import (
    run_deterministic_quality_checks,
    assemble_canonical_requirements
)

# Explicit alias to avoid collisions with HITL normalize_requirements
normalize_evidence = normalize_requirements


def extract_requirements(transcript: str) -> Dict[str, Any]:
    """
    Master entry point for the 4-stage requirements extraction pipeline.
    Ensures complete backward compatibility with any direct caller.
    """
    print("\n" + "="*60)
    print("STARTING MULTI-STAGE REQUIREMENTS EXTRACTION PIPELINE")
    print("="*60)

    if not transcript or not transcript.strip():
        print("[Extraction Pipeline] Empty transcript received.")
        return {
            "specified_requirements": {"functional": [], "non_functional": [], "uncertain": []},
            "functional": [],
            "non_functional": [],
            "uncertain": [],
            "evidence_candidates": [],
            "extraction_quality_report": {"passed": True, "total_input_candidates": 0}
        }

    # Stage 1: Evidence Extraction
    evidence_candidates = extract_evidence(transcript)

    if not evidence_candidates:
        print("[Extraction Pipeline WARNING] No evidence candidates extracted from transcript.")
        return {
            "specified_requirements": {"functional": [], "non_functional": [], "uncertain": []},
            "functional": [],
            "non_functional": [],
            "uncertain": [],
            "evidence_candidates": [],
            "extraction_quality_report": {"passed": False, "warnings": ["No evidence candidates extracted."]}
        }

    # Stage 2: Requirement Normalization
    normalized_requirements = normalize_requirements(evidence_candidates)

    if not normalized_requirements:
        print("[Extraction Pipeline WARNING] No requirements normalized from evidence.")
        return {
            "specified_requirements": {"functional": [], "non_functional": [], "uncertain": []},
            "functional": [],
            "non_functional": [],
            "uncertain": [],
            "evidence_candidates": evidence_candidates,
            "extraction_quality_report": {"passed": False, "warnings": ["Normalization yielded 0 requirements."]}
        }

    # Stage 3: Independent Classification
    classified_requirements = classify_requirements(normalized_requirements)

    # Stage 4: Deterministic Quality Checks & Canonical Assembly
    valid_requirements, report = run_deterministic_quality_checks(
        evidence_candidates,
        classified_requirements
    )

    canonical_result = assemble_canonical_requirements(
        valid_requirements,
        evidence_candidates,
        report
    )

    print("\n" + "="*60)
    print("MULTI-STAGE REQUIREMENTS EXTRACTION PIPELINE COMPLETED")
    print("="*60)

    return canonical_result


__all__ = [
    "extract_requirements",
    "extract_evidence",
    "normalize_requirements",
    "normalize_evidence",
    "classify_requirements",
    "run_deterministic_quality_checks",
    "assemble_canonical_requirements",
]
