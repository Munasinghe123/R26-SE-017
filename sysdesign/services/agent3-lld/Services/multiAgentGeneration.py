from __future__ import annotations

from dataclasses import dataclass

from graph.candidate import CandidateState
from Services.diagramOrchestrator import OrchestrationResult
from Services.expertReview import ExpertReviewResult
from Services.agenticReconciliation import AgenticReconciliationResult


@dataclass
class MultiAgentGenerationResult:
    orchestration: OrchestrationResult
    expert_review: ExpertReviewResult
    selected_candidate: CandidateState | None
    initial_validation_result: dict | None = None
    reconciliation: AgenticReconciliationResult | None = None
    final_validation_report: dict | None = None
