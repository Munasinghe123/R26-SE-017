import asyncio
from collections.abc import Mapping, Sequence

from graph.candidate import CandidateConfig
from Services.diagramOrchestrator import OrchestrationResult, _build_orchestration_result
from Services.multiAgentGeneration import MultiAgentGenerationResult
from llm.provider import LLMProvider

async def arun_ensemble_graph(
    requirements: str,
    requirement_ids: list[str],
    candidate_configs: Sequence[CandidateConfig],
    providers: Mapping[str, LLMProvider]
) -> OrchestrationResult:
    from Services.candidateService import CandidateService

    async def _run_candidate(config):
        agent = CandidateService.build_candidate_agent(config, providers.get(config.provider))
        return config.candidate_id, await agent.agenerate(requirements, requirement_ids)

    results = await asyncio.gather(*[_run_candidate(c) for c in candidate_configs])
    candidates = {cid: state for cid, state in results}
    return _build_orchestration_result(len(candidate_configs), candidates)

from concurrent.futures import ThreadPoolExecutor
import time

def run_ensemble_graph(
    requirements: str,
    requirement_ids: list[str],
    candidate_configs: Sequence[CandidateConfig],
    providers: Mapping[str, LLMProvider]
) -> OrchestrationResult:
    from Services.candidateService import CandidateService

    print(f"\n{'='*60}\n[LLD-Agent] [PHASE 1] Spawning {len(candidate_configs)} Parallel Candidate Agents...")
    for c in candidate_configs:
        print(f"  -> {c.candidate_id}: Model = {c.model}")
    print(f"{'='*60}")

    def _generate_one(config):
        t0 = time.time()
        agent = CandidateService.build_candidate_agent(config, providers.get(config.provider))
        res = agent.generate(requirements, requirement_ids)
        dur = time.time() - t0
        cls_count = len(res.class_diagram.get("classes", [])) if res.class_diagram else 0
        seq_count = len(res.sequence_diagrams or [])
        er_count = len(res.er_diagram.get("entities", [])) if res.er_diagram else 0
        print(f"  [OK] [{config.candidate_id}] Complete in {dur:.1f}s -- Classes: {cls_count}, Sequences: {seq_count}, ER Tables: {er_count}")
        return config.candidate_id, res

    with ThreadPoolExecutor(max_workers=max(len(candidate_configs), 1)) as executor:
        results = list(executor.map(_generate_one, candidate_configs))

    candidates = {cid: state for cid, state in results}
    return _build_orchestration_result(len(candidate_configs), candidates)

async def arun_multi_agent_graph(
    requirements: str,
    requirement_ids: list[str],
    candidate_configs: Sequence[CandidateConfig],
) -> MultiAgentGenerationResult:
    from Services.expertReviewService import ExpertReviewService
    from Services.validationService import ValidationService
    from Services.agenticReconciliation import AgenticReconciliationService
    
    # 1. Generate Candidates
    orchestration = await arun_ensemble_graph(requirements, requirement_ids, candidate_configs, {})
    
    # 2. Expert Review
    expert_review = await ExpertReviewService.areview_candidates_internal(requirements, orchestration)
    
    selected_candidate = orchestration.candidates.get(expert_review.selected_candidate_id)
    if not selected_candidate:
        selected_candidate = next(iter(orchestration.candidates.values()))
        
    # 3. Initial Validation
    initial_validation = ValidationService.validate(
        parsed_json={
            "class_diagram": selected_candidate.class_diagram,
            "sequence_diagrams": selected_candidate.sequence_diagrams,
            "er_diagram": selected_candidate.er_diagram
        },
        requirement_ids=requirement_ids,
    )
    
    # 4. Agentic Reconciliation
    reconciliation = await AgenticReconciliationService.areconcile(
        requirements=requirements,
        requirement_ids=requirement_ids,
        selected_final_ir={
            "class_diagram": selected_candidate.class_diagram,
            "sequence_diagrams": selected_candidate.sequence_diagrams,
            "er_diagram": selected_candidate.er_diagram
        },
        initial_validation_result=initial_validation
    )
    
    return MultiAgentGenerationResult(
        orchestration=orchestration,
        expert_review=expert_review,
        selected_candidate=selected_candidate,
        initial_validation_result=initial_validation,
        reconciliation=reconciliation
    )

def run_multi_agent_graph(
    requirements: str,
    requirement_ids: list[str],
    candidate_configs: Sequence[CandidateConfig],
) -> MultiAgentGenerationResult:
    from Services.expertReviewService import ExpertReviewService
    from Services.validationService import ValidationService
    from Services.agenticReconciliation import AgenticReconciliationService
    
    # 1. Generate Candidates
    orchestration = run_ensemble_graph(requirements, requirement_ids, candidate_configs, {})
    
    # 2. Expert Review
    print(f"\n[LLD-Agent] [PHASE 2] Expert Reviewer evaluating candidates...")
    expert_review = ExpertReviewService.review_candidates_internal(requirements, orchestration)
    
    selected_candidate = orchestration.candidates.get(expert_review.selected_candidate_id)
    if not selected_candidate:
        selected_candidate = next(iter(orchestration.candidates.values()))
    
    print(f"  [WINNER] Selected: {selected_candidate.candidate_id} ({selected_candidate.model})")
    print(f"  [REASON] {expert_review.reason[:140]}...")
        
    # 3. Initial Validation
    print(f"\n[LLD-Agent] [PHASE 3] Deterministic AST & Consistency Validation...")
    initial_validation = ValidationService.validate(
        parsed_json={
            "class_diagram": selected_candidate.class_diagram,
            "sequence_diagrams": selected_candidate.sequence_diagrams,
            "er_diagram": selected_candidate.er_diagram
        },
        requirement_ids=requirement_ids,
    )
    passed = initial_validation.get("report", {}).get("passed", False)
    print(f"  [AST] Initial Validation: {'PASSED [OK]' if passed else 'Issues flagged [WARN]'}")
    
    # 4. Agentic Reconciliation
    print(f"\n[LLD-Agent] [PHASE 4] Agentic Self-Repair Loop (Max Iterations: 2)...")
    reconciliation = AgenticReconciliationService.reconcile(
        requirements=requirements,
        requirement_ids=requirement_ids,
        selected_final_ir={
            "class_diagram": selected_candidate.class_diagram,
            "sequence_diagrams": selected_candidate.sequence_diagrams,
            "er_diagram": selected_candidate.er_diagram
        },
        initial_validation_result=initial_validation
    )
    print(f"  [RECONCILIATION] Outcome: {reconciliation.status.upper()} (Iterations used: {reconciliation.iterations})")
    print(f"{'='*60}\n")
    
    return MultiAgentGenerationResult(
        orchestration=orchestration,
        expert_review=expert_review,
        selected_candidate=selected_candidate,
        initial_validation_result=initial_validation,
        reconciliation=reconciliation
    )
