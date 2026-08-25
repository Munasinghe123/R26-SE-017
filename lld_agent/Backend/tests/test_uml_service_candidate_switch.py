import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import mock_open, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateState
from Services.umlService import UMLService


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


class UMLServiceCandidateSwitchTests(unittest.TestCase):
    def test_feature_flag_false_invokes_legacy_generation_path(self):
        with patch("Services.umlService.USE_CANDIDATE_PIPELINE", False), \
             patch.object(UMLService, "_generate_uml_legacy", return_value={"mode": "legacy"}) as legacy, \
             patch.object(UMLService, "_generate_uml_candidate") as candidate:
            result = UMLService.generate_uml("requirements", ["REQ-001"])

        self.assertEqual(result, {"mode": "legacy"})
        legacy.assert_called_once_with(requirements="requirements", requirement_ids=["REQ-001"])
        candidate.assert_not_called()

    def test_feature_flag_true_invokes_candidate_generation_path(self):
        with patch("Services.umlService.USE_CANDIDATE_PIPELINE", True), \
             patch.object(UMLService, "_generate_uml_candidate", return_value={"mode": "candidate"}) as candidate, \
             patch.object(UMLService, "_generate_uml_legacy") as legacy:
            result = UMLService.generate_uml("requirements", ["REQ-001"])

        self.assertEqual(result, {"mode": "candidate"})
        candidate.assert_called_once_with(requirements="requirements", requirement_ids=["REQ-001"])
        legacy.assert_not_called()

    def test_candidate_final_ir_becomes_structured_data_and_response_contract_is_preserved(self):
        with _mock_png_rendering(), \
             patch("Services.umlService.CandidateService.run_candidate_internal", return_value=candidate_state()):
            result = UMLService._generate_uml_candidate("requirements", ["REQ-001"])

        self.assertEqual(result["structured_data"], FINAL_IR)
        self.assertEqual(result["iterations_used"], 1)
        self.assertEqual(set(result.keys()), {
            "structured_data",
            "validation",
            "pngs",
            "files",
            "plantuml",
            "iterations_used",
        })

    def test_candidate_output_is_passed_through_existing_plantuml_generation(self):
        with _mock_png_rendering(), \
             patch("Services.umlService.CandidateService.run_candidate_internal", return_value=candidate_state()):
            result = UMLService._generate_uml_candidate("requirements", ["REQ-001"])

        self.assertIn("@startuml", result["plantuml"]["class"])
        self.assertIn("@startchen", result["plantuml"]["er"])
        self.assertIn("@startuml", result["plantuml"]["sequence"][0]["plantuml"])
        self.assertEqual(result["pngs"]["class"], "UE5H")

    def test_invalid_candidate_returns_diagrams_and_validation_errors(self):
        invalid_validation = {
            "passed": False,
            "errors": [
                {
                    "rule_id": "CLASS-EMPTY",
                    "severity": "high",
                    "message": "Class 'Order' has no attributes or methods.",
                }
            ],
            "warnings": [],
            "total_checks": 2,
            "passed_checks": 1,
        }
        invalid_candidate = candidate_state(status="invalid", class_validation=invalid_validation)

        with _mock_png_rendering(), \
             patch("Services.umlService.CandidateService.run_candidate_internal", return_value=invalid_candidate):
            result = UMLService._generate_uml_candidate("requirements", ["REQ-001"])

        self.assertEqual(result["structured_data"], FINAL_IR)
        self.assertFalse(result["validation"]["passed"])
        self.assertEqual(result["validation"]["errors"][0]["rule_id"], "CLASS-EMPTY")
        self.assertIn("@startuml", result["plantuml"]["class"])

    def test_failed_candidate_raises_clear_backend_error(self):
        failed = CandidateState(
            candidate_id="candidate_1",
            provider="fake",
            model="fake-model",
            status="failed",
            provider_errors=[{
                "stage": "class",
                "message": "secret provider detail",
                "error_type": "RuntimeError",
            }],
        )

        with patch("Services.umlService.CandidateService.run_candidate_internal", return_value=failed), \
             patch.object(UMLService, "_build_rendered_response") as render:
            with self.assertRaisesRegex(ValueError, "class provider execution"):
                UMLService._generate_uml_candidate("requirements", ["REQ-001"])

        render.assert_not_called()

    def test_candidate_pipeline_mode_does_not_invoke_old_langgraph(self):
        with _mock_png_rendering(), \
             patch("Services.umlService.CandidateService.run_candidate_internal", return_value=candidate_state()) as run_candidate, \
             patch("Services.umlService.build_uml_graph") as build_graph:
            result = UMLService._generate_uml_candidate("requirements", ["REQ-001"])

        self.assertEqual(result["structured_data"], FINAL_IR)
        run_candidate.assert_called_once()
        build_graph.assert_not_called()

    def test_legacy_mode_does_not_invoke_candidate_service(self):
        fake_graph = SimpleNamespace(
            invoke=lambda state: {
                "parsed_json": FINAL_IR,
                "validation_result": {
                    "report": {
                        "passed": True,
                        "consistency_score": 100,
                        "total_checks": 1,
                        "passed_checks": 1,
                        "errors": [],
                        "traceability_matrix": [],
                        "overdesign_flags": [],
                        "naming_violations": [],
                        "naming_violations_fixed": 0,
                    }
                },
                "iterations_used": 2,
            }
        )

        with _mock_png_rendering(), \
             patch("Services.umlService.build_uml_graph", return_value=fake_graph), \
             patch("Services.umlService.CandidateService.run_candidate_internal") as run_candidate:
            result = UMLService._generate_uml_legacy("requirements", ["REQ-001"])

        self.assertEqual(result["structured_data"], FINAL_IR)
        self.assertEqual(result["iterations_used"], 2)
        run_candidate.assert_not_called()

    def test_invalid_candidate_does_not_trigger_semantic_retry(self):
        invalid_validation = {
            "passed": False,
            "errors": [
                {
                    "rule_id": "CLASS-EMPTY",
                    "severity": "high",
                    "message": "Class is invalid.",
                }
            ],
            "warnings": [],
            "total_checks": 1,
            "passed_checks": 0,
        }
        invalid_candidate = candidate_state(status="invalid", class_validation=invalid_validation)

        with _mock_png_rendering(), \
             patch("Services.umlService.CandidateService.run_candidate_internal", return_value=invalid_candidate) as run_candidate:
            result = UMLService._generate_uml_candidate("requirements", ["REQ-001"])

        self.assertFalse(result["validation"]["passed"])
        run_candidate.assert_called_once()


def _mock_png_rendering():
    response = SimpleNamespace(status_code=200, content=b"PNG")
    return _PatchGroup([
        patch("Services.umlService.requests.get", return_value=response),
        patch("Services.umlService.os.makedirs"),
        patch("builtins.open", mock_open()),
    ])


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


if __name__ == "__main__":
    unittest.main()
