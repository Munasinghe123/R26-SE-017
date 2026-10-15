import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import mock_open, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateState  # noqa: E402
from Services.diagramOrchestrator import OrchestrationResult  # noqa: E402
from Services.expertReview import ExpertReviewResult  # noqa: E402
from Services.agenticReconciliation import AgenticReconciliationResult  # noqa: E402
from Services.multiAgentGeneration import MultiAgentGenerationResult  # noqa: E402
from Services.umlService import UMLService  # noqa: E402
from schemas.ir_schema import IntermediateRepresentation  # noqa: E402
from utils.irMapper import convert_to_ir  # noqa: E402


FINAL_IR = {
    "class_diagram": {
        "classes": [
            {
                "name": "Order",
                "attributes": ["id"],
                "methods": ["createOrder()"],
            },
            {
                "name": "OrderRepository",
                "attributes": ["storage"],
                "methods": ["saveOrder()"],
            },
        ],
        "relationships": [
            {
                "source": "OrderRepository",
                "target": "Order",
                "type": "association",
                "cardinality": "1",
            }
        ],
    },
    "er_diagram": {
        "entities": [
            {
                "name": "Order",
                "attributes": ["id"],
                "primary_key": "id",
            }
        ],
        "relationships": [],
    },
    "sequence_diagrams": [
        {
            "name": "Create Order",
            "description": "Create order flow",
            "participants": ["Order", "OrderRepository"],
            "messages": [
                {
                    "from": "Order",
                    "to": "OrderRepository",
                    "message": "saveOrder()",
                }
            ],
        }
    ],
}


def candidate_state(status="valid", final_ir=None, class_validation=None):
    return CandidateState(
        candidate_id="candidate_1",
        provider="fake",
        model="fake-model",
        status=status,
        class_diagram=(final_ir or FINAL_IR).get("class_diagram"),
        er_diagram=(final_ir or FINAL_IR).get("er_diagram"),
        sequence_diagrams=(final_ir or FINAL_IR).get("sequence_diagrams"),
        class_validation=class_validation or {
            "passed": True,
            "errors": [],
            "warnings": [],
            "total_checks": 2,
            "passed_checks": 2,
        },
        er_validation={
            "passed": True,
            "errors": [],
            "warnings": [],
            "total_checks": 1,
            "passed_checks": 1,
        },
        sequence_validation={
            "passed": True,
            "errors": [],
            "warnings": [],
            "total_checks": 2,
            "passed_checks": 2,
        },
        final_ir=final_ir or FINAL_IR,
    )


class UMLServiceMultiAgentTests(unittest.TestCase):
    def test_generate_uml_invokes_current_multi_agent_generation_path(self):
        with patch.object(UMLService, "_generate_uml_multi_agent", return_value={"mode": "multi_agent"}) as multi_agent:
            result = UMLService.generate_uml("requirements", ["REQ-001"])

        self.assertEqual(result, {"mode": "multi_agent"})
        multi_agent.assert_called_once_with(
            requirements="requirements",
            requirement_ids=["REQ-001"],
            project_id=None,
        )

    def test_generate_candidates_internal_delegates_to_candidate_service_collection(self):
        fake_result = object()
        with patch(
            "Services.umlService.CandidateService.run_all_candidates_internal",
            return_value=fake_result,
        ) as run_all:
            result = UMLService.generate_candidates_internal("requirements", ["REQ-001"])

        self.assertIs(result, fake_result)
        run_all.assert_called_once_with(
            requirements="requirements",
            requirement_ids=["REQ-001"],
        )

    def test_multi_agent_selected_candidate_final_ir_becomes_structured_data(self):
        selected = candidate_state()
        multi_result = multi_agent_result(selected)

        with _mock_png_rendering(), \
             patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_result):
            result = UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

        self.assertEqual(result["structured_data"], selected.final_ir)
        self.assertEqual(result["selected_candidate_id"], "candidate_1")
        self.assertEqual(result["iterations_used"], 2)
        self.assertTrue(set([
            "structured_data",
            "validation",
            "pngs",
            "files",
            "plantuml",
            "iterations_used",
            "multi_agent",
        ]).issubset(result.keys()))
        self.assertEqual(result["multi_agent"]["expert_review"]["reason"], "selected")
        self.assertEqual(result["validation"]["stage_validation"], result_validation_for(selected))

    def test_multi_agent_can_render_candidate_1_2_or_3_selection(self):
        for candidate_id in ["candidate_1", "candidate_2", "candidate_3"]:
            selected = candidate_state_for(candidate_id)
            with _mock_png_rendering(), \
                 patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_agent_result(selected)):
                result = UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

            self.assertEqual(result["selected_candidate_id"], candidate_id)
            self.assertEqual(result["structured_data"], selected.final_ir)

    def test_multi_agent_fallback_selected_candidate_renders_normally(self):
        selected = candidate_state_for("candidate_2")
        multi_result = multi_agent_result(
            selected,
            expert_review=ExpertReviewResult(
                selected_candidate_id="candidate_2",
                reason="fallback",
                confidence=None,
                fallback_used=True,
            ),
        )

        with _mock_png_rendering(), \
             patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_result):
            result = UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

        self.assertEqual(result["selected_candidate_id"], "candidate_2")
        self.assertTrue(result["multi_agent"]["expert_review"]["fallback_used"])
        self.assertIn("@startuml", result["plantuml"]["class"])

    def test_multi_agent_invalid_but_usable_selected_candidate_returns_validation_errors(self):
        invalid_validation = {
            "passed": False,
            "errors": [{
                "rule_id": "CLASS-EMPTY",
                "severity": "high",
                "message": "Class is invalid.",
            }],
            "warnings": [],
            "total_checks": 1,
            "passed_checks": 0,
        }
        selected = candidate_state_for(
            "candidate_2",
            status="invalid",
            class_validation=invalid_validation,
        )

        with _mock_png_rendering(), \
             patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_agent_result(selected)):
            result = UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

        self.assertEqual(result["structured_data"], selected.final_ir)
        self.assertFalse(result["validation"]["passed"])
        self.assertEqual(result["validation"]["errors"][0]["rule_id"], "FINAL-TEST")
        self.assertEqual(result["validation"]["stage_validation"]["errors"][0]["rule_id"], "CLASS-EMPTY")

    def test_multi_agent_all_three_failed_raises_without_rendering(self):
        multi_result = multi_agent_result(
            selected=None,
            expert_review=ExpertReviewResult(
                selected_candidate_id=None,
                reason="all failed",
                confidence=0,
                fallback_used=True,
            ),
        )

        with patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_result), \
             patch.object(UMLService, "_build_rendered_response") as render:
            with self.assertRaisesRegex(ValueError, "no usable candidate"):
                UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

        render.assert_not_called()

    def test_multi_agent_selected_candidate_without_final_ir_raises_clear_error(self):
        selected = candidate_state(status="failed")
        selected.final_ir = None
        selected.provider_errors = [{
            "stage": "class",
            "message": "provider unavailable",
            "error_type": "RuntimeError",
        }]

        with patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_agent_result(selected)), \
             patch.object(UMLService, "_build_rendered_response") as render:
            with self.assertRaisesRegex(ValueError, "class provider execution"):
                UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

        render.assert_not_called()

    def test_multi_agent_plantuml_generation_receives_only_selected_candidate_ir(self):
        selected = candidate_state_for("candidate_3")

        with _mock_agentic_reconciliation(selected), \
             patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_agent_result(selected)), \
             patch.object(UMLService, "_build_rendered_response", return_value={"ok": True}) as render:
            result = UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

        self.assertEqual(result["selected_candidate_id"], "candidate_3")
        render.assert_called_once_with(
            parsed_json=selected.final_ir,
            validation_report=final_validation_report_for(selected),
            iterations_used=2,
            project_id=None,
        )

    def test_multi_agent_final_validation_uses_selected_candidate_ir(self):
        selected = candidate_state_for("candidate_2")

        with patch.object(UMLService, "generate_multi_agent_internal", return_value=multi_agent_result(selected)), \
             patch.object(UMLService, "_build_rendered_response", return_value={"ok": True}), \
             patch("Services.umlService.convert_to_ir", return_value=IntermediateRepresentation()) as mapper, \
             patch("Services.umlService.ValidationService.validate", return_value=validation_service_result()) as validate, \
             patch("Services.umlService.AgenticReconciliationService.reconcile", return_value=reconciliation_result_for(selected)) as reconcile:
            UMLService._generate_uml_multi_agent("requirements", ["REQ-001"])

        mapper.assert_called_once_with(selected.final_ir)
        validate.assert_called_once_with(
            mapper.return_value,
            requirement_ids=["REQ-001"],
        )
        reconcile.assert_called_once()
        self.assertEqual(reconcile.call_args.kwargs["initial_validation_result"], validation_service_result())

    def test_build_rendered_response_preserves_current_response_contract(self):
        with _mock_png_rendering():
            result = UMLService._build_rendered_response(
                parsed_json=FINAL_IR,
                validation_report={"passed": True},
                iterations_used=1,
            )

        self.assertEqual(result["structured_data"], FINAL_IR)
        self.assertEqual(result["validation"], {"passed": True})
        self.assertEqual(result["iterations_used"], 1)
        self.assertEqual(set(result.keys()), {
            "structured_data",
            "validation",
            "pngs",
            "files",
            "plantuml",
            "iterations_used",
            "cloudinary_urls",
        })
        self.assertIn("@startuml", result["plantuml"]["class"])
        self.assertIn("@startchen", result["plantuml"]["er"])
        self.assertIn("@startuml", result["plantuml"]["sequence"][0]["plantuml"])


def _mock_png_rendering():
    response = SimpleNamespace(status_code=200, content=b"PNG")
    return _PatchGroup([
        patch("Services.umlService.requests.get", return_value=response),
        patch("builtins.open", mock_open()),
        patch("Services.umlService.upload_png_to_cloudinary", return_value="https://cloudinary.test/diagram.png"),
        patch("Services.umlService.ValidationService.validate", return_value=validation_service_result()),
        patch("Services.umlService.AgenticReconciliationService.reconcile", side_effect=lambda **kwargs: reconciliation_result_for_ir(kwargs["selected_final_ir"])),
    ])


def _mock_final_validation():
    return patch("Services.umlService.ValidationService.validate", return_value=validation_service_result())


def _mock_agentic_reconciliation(candidate):
    return patch("Services.umlService.AgenticReconciliationService.reconcile", return_value=reconciliation_result_for(candidate))


class _PatchGroup:
    def __init__(self, patchers):
        self.patchers = patchers
        self.started = []

    def __enter__(self):
        for patcher in self.patchers:
            self.started.append(patcher.start())
        return self.started

    def __exit__(self, exc_type, exc, tb):
        for patcher in reversed(self.patchers):
            patcher.stop()


def candidate_state_for(candidate_id: str, status="valid", class_validation=None):
    state = candidate_state(status=status, class_validation=class_validation)
    state.candidate_id = candidate_id
    state.model = f"fake-model-{candidate_id}"
    state.provider = "fake"
    return state


def multi_agent_result(selected, expert_review=None):
    candidates = {
        "candidate_1": candidate_state_for("candidate_1"),
        "candidate_2": candidate_state_for("candidate_2"),
        "candidate_3": candidate_state_for("candidate_3"),
    }
    if selected is not None:
        candidates[selected.candidate_id] = selected

    orchestration = OrchestrationResult(
        candidates=candidates,
        total_agents=3,
        completed_agents=3,
        valid_agents=sum(1 for candidate in candidates.values() if candidate.status == "valid"),
        invalid_agents=sum(1 for candidate in candidates.values() if candidate.status == "invalid"),
        failed_agents=sum(1 for candidate in candidates.values() if candidate.status == "failed"),
        total_model_calls=9,
        total_tokens=99,
        total_latency_ms=900.0,
    )
    expert_review = expert_review or ExpertReviewResult(
        selected_candidate_id=selected.candidate_id if selected else None,
        reason="selected",
        confidence=0.8,
        fallback_used=False,
    )
    return MultiAgentGenerationResult(
        orchestration=orchestration,
        expert_review=expert_review,
        selected_candidate=selected,
    )


def result_validation_for(candidate):
    errors = []
    total_checks = 0
    passed_checks = 0
    for stage, validation in {
        "class": candidate.class_validation,
        "er": candidate.er_validation,
        "sequence": candidate.sequence_validation,
    }.items():
        validation = validation or {}
        total_checks += int(validation.get("total_checks", 0) or 0)
        passed_checks += int(validation.get("passed_checks", 0) or 0)
        for error in validation.get("errors", []) or []:
            errors.append({**error, "stage": stage})
        for warning in validation.get("warnings", []) or []:
            errors.append({**warning, "stage": stage, "severity": "low"})

    return {
        "passed": candidate.status == "valid" and not any(
            error.get("severity") in ("critical", "high", "medium")
            for error in errors
        ),
        "consistency_score": round((passed_checks / total_checks * 100), 2) if total_checks else 0.0,
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "errors": errors,
        "traceability_matrix": [],
        "overdesign_flags": [],
        "naming_violations": [],
        "naming_violations_fixed": 0,
        "repair": candidate.repair_metadata,
    }


def validation_service_result():
    return {
        "report": {
            "passed": False,
            "consistency_score": 50.0,
            "total_checks": 2,
            "passed_checks": 1,
            "errors": [{
                "rule_id": "FINAL-TEST",
                "severity": "high",
                "message": "Final validation issue.",
                "suggestion": "",
                "educational_feedback": "",
            }],
            "traceability_matrix": [],
            "overdesign_flags": [],
            "naming_violations": [],
            "naming_violations_fixed": 0,
        },
        "errors": [],
        "expert_guidance": "",
    }


def final_validation_report_for(candidate):
    report = validation_service_result()["report"]
    return {
        **report,
        "expert_guidance": "",
        "stage_validation": result_validation_for(candidate),
        "repair": {
            "stage": candidate.repair_metadata,
            "agentic_reconciliation": reconciliation_result_for(candidate).repair_metadata,
        },
        "agent_trace": reconciliation_result_for(candidate).agent_trace,
        "agentic_reconciliation": reconciliation_result_for(candidate).metadata(),
    }


def reconciliation_result_for(candidate):
    return AgenticReconciliationResult(
        final_ir=candidate.final_ir,
        validation_report=validation_service_result()["report"],
        iterations=2,
        status="passed",
        stop_reason="validation_passed",
        repair_metadata={"attempts": [{"iteration": 1, "status": "completed"}]},
        agent_trace=[
            {"iteration": 1, "agent": "final_validator", "status": "failed", "issues": 1},
            {"iteration": 1, "agent": "expert_decision", "action": "REPAIR"},
            {"iteration": 1, "agent": "expert_repair", "status": "completed"},
            {"iteration": 2, "agent": "final_validator", "status": "passed", "issues": 0},
        ],
    )


def reconciliation_result_for_ir(final_ir):
    selected = candidate_state(final_ir=final_ir)
    return reconciliation_result_for(selected)


class IRMapperTraceabilityTests(unittest.TestCase):
    def test_convert_to_ir_preserves_requirement_ids(self):
        mapped = convert_to_ir({
            "class_diagram": {
                "classes": [{
                    "name": "Order",
                    "attributes": ["id"],
                    "methods": ["saveOrder()"],
                    "requirement_ids": ["REQ-001"],
                }],
                "relationships": [],
            },
            "er_diagram": {
                "entities": [{
                    "name": "order",
                    "attributes": ["id"],
                    "primary_key": "id",
                    "requirement_ids": ["REQ-002"],
                }],
                "relationships": [],
            },
            "sequence_diagrams": [{
                "name": "Save Order",
                "participants": ["Order"],
                "messages": [],
                "requirement_ids": ["REQ-003"],
            }],
        })

        self.assertEqual(mapped.classes[0].requirement_ids, ["REQ-001"])
        self.assertEqual(mapped.entities[0].requirement_ids, ["REQ-002"])
        self.assertEqual(mapped.sequences[0].requirement_ids, ["REQ-003"])


if __name__ == "__main__":
    unittest.main()
