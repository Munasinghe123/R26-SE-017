import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from Services.agenticReconciliation import (  # noqa: E402
    AgenticReconciliationService,
    decide_reconciliation_action,
)
from Services.expertRepair import ExpertRepairResult  # noqa: E402


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
            metrics={"provider": "fake", "model": "fake-repair"},
        )


def validation_result(passed, rule_id="CV-001", message="Method is missing.", severity="critical"):
    return {
        "report": {
            "passed": passed,
            "consistency_score": 100.0 if passed else 50.0,
            "total_checks": 1,
            "passed_checks": 1 if passed else 0,
            "errors": [] if passed else [{
                "rule_id": rule_id,
                "severity": severity,
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


class AgenticReconciliationTests(unittest.TestCase):
    def test_passing_initial_validation_does_not_repair(self):
        repair = FakeRepairService([VALID_IR])

        result = AgenticReconciliationService.reconcile(
            selected_final_ir=VALID_IR,
            requirements="REQ-001 Save orders.",
            requirement_ids=["REQ-001"],
            initial_validation_result=validation_result(True),
            repair_service=repair,
        )

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.iterations, 1)
        self.assertEqual(repair.calls, [])
        self.assertEqual(result.final_ir, VALID_IR)
        self.assertEqual(result.agent_trace[0]["agent"], "final_validator")

    def test_repair_loop_revalidates_and_returns_repaired_ir(self):
        repaired = {**VALID_IR, "er_diagram": {**VALID_IR["er_diagram"], "relationships": []}}
        repair = FakeRepairService([repaired])

        with patch(
            "Services.agenticReconciliation.ValidationService.validate",
            return_value=validation_result(True),
        ) as validate:
            result = AgenticReconciliationService.reconcile(
                selected_final_ir=VALID_IR,
                requirements="REQ-001 Save orders.",
                requirement_ids=["REQ-001"],
                initial_validation_result=validation_result(False),
                repair_service=repair,
            )

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.final_ir, repaired)
        self.assertEqual(len(repair.calls), 1)
        validate.assert_called_once()
        self.assertEqual(result.agent_trace[-1]["status"], "passed")

    def test_multiple_iterations_stop_on_third_pass(self):
        repair_1 = {**VALID_IR, "marker": "repair_1"}
        repair_2 = {**VALID_IR, "marker": "repair_2"}
        repair = FakeRepairService([repair_1, repair_2])

        validations = [
            validation_result(False, message="Still missing method."),
            validation_result(True),
        ]
        with patch(
            "Services.agenticReconciliation.ValidationService.validate",
            side_effect=validations,
        ):
            result = AgenticReconciliationService.reconcile(
                selected_final_ir=VALID_IR,
                requirements="REQ-001 Save orders.",
                requirement_ids=["REQ-001"],
                initial_validation_result=validation_result(False),
                repair_service=repair,
            )

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.iterations, 3)
        self.assertEqual(result.final_ir, repair_2)
        self.assertEqual(len(repair.calls), 2)

    def test_iteration_limit_stops_without_fourth_validation_or_repair(self):
        repair = FakeRepairService([
            {**VALID_IR, "marker": "repair_1"},
            {**VALID_IR, "marker": "repair_2"},
            {**VALID_IR, "marker": "repair_3"},
        ])

        with patch(
            "Services.agenticReconciliation.ValidationService.validate",
            side_effect=[validation_result(False), validation_result(False)],
        ) as validate:
            result = AgenticReconciliationService.reconcile(
                selected_final_ir=VALID_IR,
                requirements="REQ-001 Save orders.",
                requirement_ids=["REQ-001"],
                initial_validation_result=validation_result(False),
                repair_service=repair,
            )

        self.assertEqual(result.status, "max_iterations_reached")
        self.assertEqual(result.iterations, 3)
        self.assertEqual(len(repair.calls), 2)
        self.assertEqual(validate.call_count, 2)
        self.assertTrue(result.unresolved_issues)

    def test_semantic_gap_does_not_invoke_repair_for_actor_persistence(self):
        repair = FakeRepairService([VALID_IR])
        report = validation_result(
            False,
            rule_id="CV-003",
            message="Order.customer_id exists, but Customer exists only as an actor and is not defined as a persistent domain entity.",
            severity="high",
        )

        result = AgenticReconciliationService.reconcile(
            selected_final_ir=VALID_IR,
            requirements="Actor: Customer. Domain entity: Order.",
            requirement_ids=["REQ-001"],
            initial_validation_result=report,
            repair_service=repair,
        )

        self.assertEqual(result.status, "semantic_gap")
        self.assertEqual(repair.calls, [])
        self.assertNotIn(
            "Customer",
            [entity["name"] for entity in result.final_ir["er_diagram"]["entities"]],
        )

    def test_nested_payload_concept_is_semantic_gap(self):
        decision = decide_reconciliation_action(
            validation_result(
                False,
                rule_id="CV-003",
                message="cart_items is present in API payload but no persistent CartItem entity is defined.",
                severity="high",
            )["report"],
            current_ir=VALID_IR,
            requirements="API accepts cart_items[]. Persist Order only.",
            iteration=1,
        )

        self.assertEqual(decision.action, "SEMANTIC_GAP")

    def test_structural_primary_key_issue_is_repairable(self):
        decision = decide_reconciliation_action(
            validation_result(
                False,
                rule_id="CV-007",
                message="Entity Order has NO Primary Key defined.",
                severity="critical",
            )["report"],
            current_ir=VALID_IR,
            requirements="REQ-001 Persist Order with id.",
            iteration=1,
        )

        self.assertEqual(decision.action, "REPAIR")

    def test_trace_records_validator_decision_and_repair(self):
        repair = FakeRepairService([VALID_IR])

        with patch(
            "Services.agenticReconciliation.ValidationService.validate",
            return_value=validation_result(True),
        ):
            result = AgenticReconciliationService.reconcile(
                selected_final_ir=VALID_IR,
                requirements="REQ-001 Save orders.",
                requirement_ids=["REQ-001"],
                initial_validation_result=validation_result(False),
                repair_service=repair,
            )

        agents = [entry["agent"] for entry in result.agent_trace]
        self.assertIn("final_validator", agents)
        self.assertIn("expert_decision", agents)
        self.assertIn("expert_repair", agents)
        self.assertEqual(result.agent_trace[1]["action"], "REPAIR")


if __name__ == "__main__":
    unittest.main()
