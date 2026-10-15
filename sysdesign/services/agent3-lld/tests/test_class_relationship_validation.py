import copy
import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig, run_candidate  # noqa: E402
from llm.provider import LLMResponse  # noqa: E402
from validators.stage_validators import validate_class_diagram  # noqa: E402


def class_diagram(relationships):
    return {
        "classes": [
            {"name": "FrontendUI", "attributes": [], "methods": ["submitOrder()"]},
            {"name": "OrderController", "attributes": [], "methods": ["createOrder()"]},
            {"name": "Order", "attributes": ["id"], "methods": []},
            {"name": "OrderRepository", "attributes": [], "methods": ["saveOrder()"]},
        ],
        "relationships": relationships,
    }


def rule_ids(result):
    return {error["rule_id"] for error in result["errors"]}


class FakeProvider:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def complete(self, *, model, messages, temperature, max_tokens):
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        return LLMResponse(
            content=self.outputs.pop(0),
            provider="fake",
            model=model,
        )


class ClassRelationshipValidationTests(unittest.TestCase):
    def test_valid_dependency_without_cardinality_passes(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "FrontendUI",
                "target": "OrderController",
                "type": "dependency",
                "cardinality": "",
            }
        ]))

        self.assertTrue(result["passed"])
        self.assertEqual(result["errors"], [])

    def test_dependency_with_cardinality_fails(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "FrontendUI",
                "target": "OrderController",
                "type": "dependency",
                "cardinality": "1",
            }
        ]))

        self.assertFalse(result["passed"])
        self.assertIn("CLASS-DEPENDENCY-CARDINALITY", rule_ids(result))

    def test_missing_source_fails(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "MissingUI",
                "target": "OrderController",
                "type": "dependency",
                "cardinality": "",
            }
        ]))

        self.assertFalse(result["passed"])
        self.assertIn("CLASS-REL-SOURCE", rule_ids(result))

    def test_missing_target_fails(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "OrderController",
                "target": "MissingRepository",
                "type": "dependency",
                "cardinality": "",
            }
        ]))

        self.assertFalse(result["passed"])
        self.assertIn("CLASS-REL-TARGET", rule_ids(result))

    def test_unsupported_relationship_type_fails(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "OrderController",
                "target": "Order",
                "type": "uses",
                "cardinality": "",
            }
        ]))

        self.assertFalse(result["passed"])
        self.assertIn("CLASS-REL-TYPE", rule_ids(result))

    def test_invalid_cardinality_value_fails(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "OrderController",
                "target": "Order",
                "type": "association",
                "cardinality": "many",
            }
        ]))

        self.assertFalse(result["passed"])
        self.assertIn("CLASS-REL-CARDINALITY", rule_ids(result))

    def test_valid_association_with_supported_cardinality_passes(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "OrderRepository",
                "target": "Order",
                "type": "association",
                "cardinality": "1",
            }
        ]))

        self.assertTrue(result["passed"])
        self.assertEqual(result["errors"], [])

    def test_inheritance_with_cardinality_fails(self):
        result = validate_class_diagram(class_diagram([
            {
                "source": "OrderController",
                "target": "FrontendUI",
                "type": "inheritance",
                "cardinality": "1",
            }
        ]))

        self.assertFalse(result["passed"])
        self.assertIn("CLASS-INHERITANCE-CARDINALITY", rule_ids(result))

    def test_validation_does_not_mutate_relationship_ir(self):
        diagram = class_diagram([
            {
                "source": "FrontendUI",
                "target": "OrderController",
                "type": "dependency",
                "cardinality": "1",
            }
        ])
        original = copy.deepcopy(diagram)

        validate_class_diagram(diagram)

        self.assertEqual(diagram, original)

    def test_candidate_pipeline_records_dependency_cardinality_failure(self):
        invalid_class = (
            '{"class_diagram":{"classes":['
            '{"name":"FrontendUI","attributes":[],"methods":["submitOrder()"]},'
            '{"name":"OrderController","attributes":[],"methods":["createOrder()"]}'
            '],"relationships":['
            '{"source":"FrontendUI","target":"OrderController","type":"dependency","cardinality":"1"}'
            ']}}'
        )
        valid_er = '{"er_diagram":{"entities":[],"relationships":[]}}'
        valid_sequence = (
            '{"sequence_diagrams":[{"name":"Create Order","description":"Create order flow",'
            '"participants":["FrontendUI","OrderController"],'
            '"messages":[{"from":"FrontendUI","to":"OrderController","message":"createOrder()"}]}]}'
        )
        provider = FakeProvider([invalid_class, invalid_class, invalid_class, valid_er, valid_sequence])

        state = run_candidate(
            CandidateConfig("candidate_x", "fake", "model-x"),
            "Build ordering.",
            ["REQ-001"],
            provider,
        )

        self.assertEqual(len(provider.calls), 5)
        self.assertEqual(state.status, "invalid")
        self.assertFalse(state.class_validation["passed"])
        self.assertEqual(state.repair_metadata["class"]["repair_attempts"], 2)
        self.assertIn("CLASS-DEPENDENCY-CARDINALITY", rule_ids(state.class_validation))
        self.assertEqual(
            state.class_diagram["relationships"][0]["cardinality"],
            "1",
        )


if __name__ == "__main__":
    unittest.main()
