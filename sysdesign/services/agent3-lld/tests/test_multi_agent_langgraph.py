import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig, CandidateMetrics, CandidateState
from graph.ensemble_graph import run_multi_agent_graph
from llm.provider import LLMResponse
from Services.agenticReconciliation import MAX_AGENT_ITERATIONS
from Services.expertRepair import ExpertRepairResult
from Services.expertReview import ExpertReviewResult
from Services.multiAgentGeneration import MultiAgentGenerationResult
from Services.umlService import UMLService


VALID_IR = {
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
            "name": "Order",
            "attributes": ["id"],
            "primary_key": "id",
            "requirement_ids": ["REQ-001"],
        }],
        "relationships": [],
    },
    "sequence_diagrams": [{
        "name": "Save Order",
        "description": "Save order",
        "requirement_ids": ["REQ-001"],
        "participants": ["Order"],
        "messages": [{"from": "Order", "to": "Order", "message": "saveOrder()"}],
    }],
}
ORDER_MANAGEMENT_IR = {
    "class_diagram": {
        "classes": [
            {"name": "Customer", "attributes": ["customer_id"], "methods": ["submitCheckout(customer_id, cart_items)"]},
            {"name": "FrontendUI", "attributes": [], "methods": ["submitCheckout(request)", "successResponse(message)"]},
            {"name": "OrderController", "attributes": [], "methods": ["submitCheckout(request)", "validateCartNotEmpty()", "calculateTotalPrice()"]},
            {"name": "Order", "attributes": ["order_id", "customer_id", "total_price", "status"], "methods": ["validateCartNotEmpty()", "calculateTotalPrice()"]},
            {"name": "DatabaseRepository", "attributes": [], "methods": ["createOrder(order)", "createCartItem(cartItem)"]},
        ],
        "relationships": [],
    },
    "er_diagram": {
        "entities": [
            {"name": "Customer", "attributes": ["customer_id"], "primary_key": "customer_id"},
            {"name": "Order", "attributes": ["order_id", "customer_id", "total_price", "status"], "primary_key": "order_id"},
            {"name": "CartItem", "attributes": ["cart_item_id", "order_id", "product_id", "quantity"], "primary_key": "cart_item_id"},
        ],
        "relationships": [
            {"name": "places", "source": "Customer", "target": "Order", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "0..*", "evidence": "A customer can have multiple orders, and each order belongs to one customer."},
            {"name": "contains", "source": "Order", "target": "CartItem", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "1..*", "evidence": "An order contains one or more cart items, and each cart item belongs to one order."},
        ],
    },
    "sequence_diagrams": [{
        "name": "Submit Checkout",
        "description": "Checkout flow",
        "participants": ["Customer", "FrontendUI", "OrderController", "Order", "DatabaseRepository"],
        "participant_types": {"Customer": "actor", "FrontendUI": "boundary", "OrderController": "control", "Order": "entity", "DatabaseRepository": "participant"},
        "messages": [
            {"from": "Customer", "to": "FrontendUI", "message": "submitCheckout(customer_id, cart_items)"},
            {"from": "FrontendUI", "to": "OrderController", "message": "submitCheckout(request)"},
            {"from": "OrderController", "to": "Order", "message": "validateCartNotEmpty()"},
            {"from": "OrderController", "to": "Order", "message": "calculateTotalPrice()"},
            {"from": "OrderController", "to": "DatabaseRepository", "message": "createOrder(order)"},
            {"from": "OrderController", "to": "FrontendUI", "message": "successResponse(message)"},
        ],
        "logic_blocks": [{
            "block_type": "loop",
            "condition": "for each cart item",
            "messages": [{"from": "OrderController", "to": "DatabaseRepository", "message": "createCartItem(cartItem)"}],
            "logic_blocks": [],
        }],
    }],
}


class FakeExpertProvider:
    def __init__(self, content=None, error=None):
        self.content = content or '{"selected_candidate_id":"candidate_1","reason":"selected","confidence":0.8}'
        self.error = error
        self.calls = []

    def complete(self, *, model, messages, temperature, max_tokens):
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if self.error:
            raise self.error
        return LLMResponse(
            content=self.content,
            provider="fake-expert",
            model=model,
            input_tokens=1,
            output_tokens=2,
            total_tokens=3,
            latency_ms=4.0,
        )


class FakeRepairService:
    def __init__(self, repaired_outputs):
        self.repaired_outputs = list(repaired_outputs)
        self.calls = []

    def repair(self, **kwargs):
        self.calls.append(kwargs)
        if not self.repaired_outputs:
            return ExpertRepairResult(final_ir=kwargs["final_ir"])
        output = self.repaired_outputs.pop(0)
        if isinstance(output, Exception):
            return ExpertRepairResult(
                final_ir=None,
                error={"error_type": output.__class__.__name__, "message": str(output)},
            )
        return ExpertRepairResult(
            final_ir=output,
            metrics={"provider": "fake", "model": "repair-model"},
        )


def configs():
    return [
        CandidateConfig("candidate_1", "provider-1", "model-1"),
        CandidateConfig("candidate_2", "provider-2", "model-2"),
        CandidateConfig("candidate_3", "provider-3", "model-3"),
    ]


def candidate(candidate_id, status="valid", final_ir=None, passed_checks=3):
    return CandidateState(
        candidate_id=candidate_id,
        provider=f"provider-{candidate_id}",
        model=f"model-{candidate_id}",
        status=status,
        class_diagram=(final_ir or VALID_IR)["class_diagram"],
        er_diagram=(final_ir or VALID_IR)["er_diagram"],
        sequence_diagrams=(final_ir or VALID_IR)["sequence_diagrams"],
        class_validation={"passed": status == "valid", "errors": [], "warnings": [], "total_checks": 1, "passed_checks": int(status == "valid")},
        er_validation={"passed": status == "valid", "errors": [], "warnings": [], "total_checks": 1, "passed_checks": int(status == "valid")},
        sequence_validation={"passed": status == "valid", "errors": [], "warnings": [], "total_checks": 1, "passed_checks": passed_checks},
        final_ir=deepcopy(final_ir or VALID_IR) if status != "failed" else None,
        metrics=CandidateMetrics(total_tokens=30, total_latency_ms=30.0, model_call_count=3),
    )


def validation_result(passed, message="Method is missing.", rule_id="CV-001"):
    return {
        "report": {
            "passed": passed,
            "consistency_score": 100.0 if passed else 50.0,
            "total_checks": 1,
            "passed_checks": int(passed),
            "errors": [] if passed else [{
                "rule_id": rule_id,
                "severity": "critical",
                "message": message,
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


def patch_candidates(states):
    candidates = {state.candidate_id: state for state in states}
    return patch(
        "graph.ensemble_graph.run_candidate_graph",
        side_effect=lambda **kwargs: deepcopy(candidates[kwargs["config"].candidate_id]),
    )


class MultiAgentLangGraphTests(unittest.TestCase):
    def test_successful_expert_selection_builds_multi_agent_result(self):
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(
                    '{"selected_candidate_id":"candidate_2","reason":"best","confidence":0.9}'
                ),
            )

        self.assertIsInstance(result, MultiAgentGenerationResult)
        self.assertEqual(result.expert_review.selected_candidate_id, "candidate_2")
        self.assertEqual(result.selected_candidate.candidate_id, "candidate_2")
        self.assertEqual(result.reconciliation.status, "passed")
        self.assertEqual(result.reconciliation.iterations, 1)

    def test_expert_provider_failure_falls_back(self):
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2", "invalid"),
            candidate("candidate_3", "failed"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=[],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(error=RuntimeError("expert unavailable")),
            )

        self.assertTrue(result.expert_review.fallback_used)
        self.assertEqual(result.expert_review.selected_candidate_id, "candidate_1")
        self.assertIn("expert unavailable", result.expert_review.reason)

    def test_malformed_expert_output_falls_back(self):
        with patch_candidates([
            candidate("candidate_1", "invalid"),
            candidate("candidate_2"),
            candidate("candidate_3", "failed"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=[],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider("not json"),
            )

        self.assertTrue(result.expert_review.fallback_used)
        self.assertEqual(result.expert_review.selected_candidate_id, "candidate_2")

    def test_unknown_expert_candidate_id_falls_back(self):
        with patch_candidates([
            candidate("candidate_1", "invalid"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=[],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(
                    '{"selected_candidate_id":"candidate_99","reason":"bad","confidence":0.2}'
                ),
            )

        self.assertTrue(result.expert_review.fallback_used)
        self.assertEqual(result.expert_review.selected_candidate_id, "candidate_2")
        self.assertIn("unknown candidate", result.expert_review.reason)

    def test_one_failed_candidate_does_not_prevent_valid_selection(self):
        with patch_candidates([
            candidate("candidate_1", "failed"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=[],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(
                    '{"selected_candidate_id":"candidate_2","reason":"best","confidence":0.8}'
                ),
            )

        self.assertEqual(result.orchestration.failed_agents, 1)
        self.assertEqual(result.selected_candidate.candidate_id, "candidate_2")

    def test_final_validation_accepts_without_repair(self):
        repair = FakeRepairService([VALID_IR])
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ) as validate:
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(),
                repair_service=repair,
            )

        self.assertEqual(validate.call_count, 1)
        self.assertEqual(repair.calls, [])
        self.assertEqual(result.reconciliation.status, "passed")
        self.assertEqual(result.initial_validation_result, validation_result(True))

    def test_one_repair_then_success(self):
        repaired = {**VALID_IR, "marker": "repair_1"}
        repair = FakeRepairService([repaired])
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            side_effect=[validation_result(False), validation_result(True)],
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(),
                repair_service=repair,
            )

        self.assertEqual(len(repair.calls), 1)
        self.assertEqual(result.reconciliation.status, "passed")
        self.assertEqual(result.reconciliation.iterations, 2)
        self.assertEqual(result.reconciliation.final_ir["marker"], "repair_1")
        self.assertEqual([entry["agent"] for entry in result.reconciliation.agent_trace], [
            "final_validator",
            "expert_decision",
            "expert_repair",
            "final_validator",
        ])

    def test_multiple_repairs_then_success(self):
        repair = FakeRepairService([
            {**VALID_IR, "marker": "repair_1"},
            {**VALID_IR, "marker": "repair_2"},
        ])
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            side_effect=[
                validation_result(False),
                validation_result(False, message="Still missing method."),
                validation_result(True),
            ],
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(),
                repair_service=repair,
            )

        self.assertEqual(len(repair.calls), 2)
        self.assertEqual(result.reconciliation.status, "passed")
        self.assertEqual(result.reconciliation.iterations, 3)
        self.assertEqual(result.reconciliation.final_ir["marker"], "repair_2")

    def test_repair_failure_stops_reconciliation(self):
        repair = FakeRepairService([RuntimeError("repair unavailable")])
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(False),
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(),
                repair_service=repair,
            )

        self.assertEqual(result.reconciliation.status, "repair_not_possible")
        self.assertEqual(result.reconciliation.stop_reason, "repair_failed")
        self.assertEqual(len(repair.calls), 1)
        self.assertEqual(result.reconciliation.repair_metadata["attempts"][0]["status"], "failed")

    def test_max_iterations_stops_without_terminal_repair(self):
        repair = FakeRepairService([
            {**VALID_IR, "marker": "repair_1"},
            {**VALID_IR, "marker": "repair_2"},
            {**VALID_IR, "marker": "repair_3"},
        ])
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(False),
        ) as validate:
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(),
                repair_service=repair,
            )

        self.assertEqual(result.reconciliation.status, "max_iterations_reached")
        self.assertEqual(result.reconciliation.iterations, MAX_AGENT_ITERATIONS)
        self.assertEqual(validate.call_count, MAX_AGENT_ITERATIONS)
        self.assertEqual(len(repair.calls), MAX_AGENT_ITERATIONS - 1)
        self.assertEqual(
            result.reconciliation.agent_trace[-1]["action"],
            "MAX_ITERATIONS_REACHED",
        )

    def test_result_public_shape_and_metadata_are_preserved(self):
        repair = FakeRepairService([{**VALID_IR, "marker": "repair_1"}])
        with patch_candidates([
            candidate("candidate_1"),
            candidate("candidate_2"),
            candidate("candidate_3"),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            side_effect=[validation_result(False), validation_result(True)],
        ):
            result = run_multi_agent_graph(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(),
                repair_service=repair,
            )

        self.assertIsInstance(result.orchestration.candidates, dict)
        self.assertIsInstance(result.expert_review, ExpertReviewResult)
        self.assertIsInstance(result.selected_candidate, CandidateState)
        self.assertEqual(result.expert_review.reason, "selected")
        self.assertEqual(result.reconciliation.repair_metadata["attempts"][0]["iteration"], 1)
        self.assertEqual(result.reconciliation.iterations, 2)

    def test_uml_service_multi_agent_internal_delegates_to_multi_agent_graph(self):
        expected = MultiAgentGenerationResult(
            orchestration=None,
            expert_review=ExpertReviewResult("candidate_1", "selected", 0.8),
            selected_candidate=None,
        )

        with patch("Services.umlService.CandidateService.get_candidate_configs", return_value=configs()), \
             patch("Services.umlService.run_multi_agent_graph", return_value=expected) as graph:
            result = UMLService.generate_multi_agent_internal("requirements", ["REQ-001"])

        graph.assert_called_once_with(
            requirements="requirements",
            requirement_ids=["REQ-001"],
            candidate_configs=configs(),
        )
        self.assertIs(result, expected)

    def test_order_management_new_er_schema_can_select_usable_candidate(self):
        with patch_candidates([
            candidate("candidate_1", final_ir=ORDER_MANAGEMENT_IR),
            candidate("candidate_2", "invalid", final_ir=ORDER_MANAGEMENT_IR),
            candidate("candidate_3", "failed", final_ir=ORDER_MANAGEMENT_IR),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = run_multi_agent_graph(
                requirements="Order Management",
                requirement_ids=[],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(
                    '{"selected_candidate_id":"candidate_1","reason":"usable","confidence":0.9}'
                ),
            )

        self.assertEqual(result.orchestration.valid_agents, 1)
        self.assertIsNotNone(result.selected_candidate)
        self.assertEqual(result.selected_candidate.candidate_id, "candidate_1")
        relationships = result.selected_candidate.final_ir["er_diagram"]["relationships"]
        self.assertEqual(relationships[0]["name"], "places")
        self.assertEqual(relationships[0]["target_multiplicity"], "0..*")
        self.assertEqual(relationships[1]["target_multiplicity"], "1..*")

    def test_fallback_selection_works_with_order_management_new_er_schema(self):
        with patch_candidates([
            candidate("candidate_1", "invalid", final_ir=ORDER_MANAGEMENT_IR),
            candidate("candidate_2", final_ir=ORDER_MANAGEMENT_IR),
            candidate("candidate_3", "failed", final_ir=ORDER_MANAGEMENT_IR),
        ]), patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = run_multi_agent_graph(
                requirements="Order Management",
                requirement_ids=[],
                candidate_configs=configs(),
                expert_review_provider=FakeExpertProvider(error=RuntimeError("expert unavailable")),
            )

        self.assertTrue(result.expert_review.fallback_used)
        self.assertEqual(result.expert_review.selected_candidate_id, "candidate_2")
        self.assertIsNotNone(result.selected_candidate)
        self.assertEqual(
            result.selected_candidate.final_ir["er_diagram"]["relationships"][1]["target_multiplicity"],
            "1..*",
        )


if __name__ == "__main__":
    unittest.main()
