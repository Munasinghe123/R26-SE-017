import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig
from graph.candidate_graph import run_candidate_graph
from llm.provider import LLMResponse


VALID_CLASS = (
    '{"class_diagram":{"classes":['
    '{"name":"Order","attributes":["id"],"methods":["createOrder()"]},'
    '{"name":"OrderRepository","attributes":["storage"],"methods":["saveOrder()"]}'
    '],"relationships":[{"source":"OrderRepository","target":"Order","type":"association","cardinality":"1"}]}}'
)
INVALID_CLASS = (
    '{"class_diagram":{"classes":[{"name":"Order","attributes":[],"methods":[]}],"relationships":[]}}'
)
VALID_ER = (
    '{"er_diagram":{"entities":['
    '{"name":"Order","attributes":["id"],"primary_key":"id"}'
    '],"relationships":[]}}'
)
INVALID_ER = (
    '{"er_diagram":{"entities":[{"name":"Order","attributes":["id"],"primary_key":""}],"relationships":[]}}'
)
VALID_SEQUENCE = (
    '{"sequence_diagrams":[{"name":"Create Order","description":"Create order flow",'
    '"participants":["Order","OrderRepository"],'
    '"messages":[{"from":"Order","to":"OrderRepository","message":"saveOrder()"}]}]}'
)
VALID_SEQUENCE_FOR_ORDER_NO_METHODS = (
    '{"sequence_diagrams":[{"name":"Inspect Order","description":"Order participant only",'
    '"participants":["Order"],"messages":[]}]}'
)
INVALID_SEQUENCE = (
    '{"sequence_diagrams":[{"name":"Create Order","description":"Create order flow",'
    '"participants":["Order","OrderRepository"],'
    '"messages":[{"from":"Order","to":"OrderRepository","message":"missingMethod()"}]}]}'
)
ORDER_MANAGEMENT_CLASS = (
    '{"class_diagram":{"classes":['
    '{"name":"Customer","attributes":["customer_id"],"methods":["submitCheckout(customer_id, cart_items)"]},'
    '{"name":"FrontendUI","attributes":[],"methods":["submitCheckout(request)","successResponse(message)"]},'
    '{"name":"OrderController","attributes":[],"methods":["submitCheckout(request)","validateCartNotEmpty()","calculateTotalPrice()"]},'
    '{"name":"Order","attributes":["order_id","customer_id","total_price","status"],"methods":["validateCartNotEmpty()","calculateTotalPrice()"]},'
    '{"name":"DatabaseRepository","attributes":[],"methods":["createOrder(order)","createCartItem(cartItem)"]}'
    '],"relationships":[]}}'
)
ORDER_MANAGEMENT_ER_OLD_SCHEMA = (
    '{"er_diagram":{"entities":['
    '{"name":"Customer","attributes":["customer_id"],"primary_key":"customer_id"},'
    '{"name":"Order","attributes":["order_id","customer_id","total_price","status"],"primary_key":"order_id"},'
    '{"name":"CartItem","attributes":["cart_item_id","order_id","product_id","quantity"],"primary_key":"cart_item_id"}'
    '],"relationships":['
    '{"source":"Customer","target":"Order","type":"one-to-many","evidence":"A customer can have multiple orders."},'
    '{"source":"Order","target":"CartItem","type":"one-to-many","evidence":"An order contains one or more cart items."}'
    ']}}'
)
ORDER_MANAGEMENT_ER_NEW_SCHEMA = (
    '{"er_diagram":{"entities":['
    '{"name":"Customer","attributes":["customer_id"],"primary_key":"customer_id"},'
    '{"name":"Order","attributes":["order_id","customer_id","total_price","status"],"primary_key":"order_id"},'
    '{"name":"CartItem","attributes":["cart_item_id","order_id","product_id","quantity"],"primary_key":"cart_item_id"}'
    '],"relationships":['
    '{"name":"places","source":"Customer","target":"Order","type":"one-to-many","source_multiplicity":"1","target_multiplicity":"0..*","evidence":"A customer can have multiple orders, and each order belongs to one customer."},'
    '{"name":"contains","source":"Order","target":"CartItem","type":"one-to-many","source_multiplicity":"1","target_multiplicity":"1..*","evidence":"An order contains one or more cart items, and each cart item belongs to one order."}'
    ']}}'
)
ORDER_MANAGEMENT_SEQUENCE = (
    '{"sequence_diagrams":[{"name":"Submit Checkout","description":"Checkout flow",'
    '"participants":["Customer","FrontendUI","OrderController","Order","DatabaseRepository"],'
    '"participant_types":{"Customer":"actor","FrontendUI":"boundary","OrderController":"control","Order":"entity","DatabaseRepository":"participant"},'
    '"messages":['
    '{"from":"Customer","to":"FrontendUI","message":"submitCheckout(customer_id, cart_items)"},'
    '{"from":"FrontendUI","to":"OrderController","message":"submitCheckout(request)"},'
    '{"from":"OrderController","to":"Order","message":"validateCartNotEmpty()"},'
    '{"from":"OrderController","to":"Order","message":"calculateTotalPrice()"},'
    '{"from":"OrderController","to":"DatabaseRepository","message":"createOrder(order)"},'
    '{"from":"OrderController","to":"FrontendUI","message":"successResponse(message)"}'
    '],"logic_blocks":[{"block_type":"loop","condition":"for each cart item","messages":['
    '{"from":"OrderController","to":"DatabaseRepository","message":"createCartItem(cartItem)"}'
    '],"logic_blocks":[]}]}]}'
)
ORDER_MANAGEMENT_SEQUENCE_INVALID_LOOP_AND_ORDER = (
    '{"sequence_diagrams":[{"name":"Submit Checkout","description":"Checkout flow",'
    '"participants":["Customer","FrontendUI","OrderController","Order","DatabaseRepository"],'
    '"participant_types":{"Customer":"actor","FrontendUI":"boundary","OrderController":"control","Order":"entity","DatabaseRepository":"participant"},'
    '"messages":['
    '{"from":"Customer","to":"FrontendUI","message":"submitCheckout(customer_id, cart_items)"},'
    '{"from":"FrontendUI","to":"OrderController","message":"submitCheckout(request)"},'
    '{"from":"OrderController","to":"FrontendUI","message":"successResponse(message)"},'
    '{"from":"OrderController","to":"DatabaseRepository","message":"createCartItem(cartItem)"}'
    '],"logic_blocks":[{"block_type":"alt","condition":"for each cart item","messages":['
    '{"from":"OrderController","to":"DatabaseRepository","message":"createCartItem(cartItem)"}'
    '],"logic_blocks":[]}]}]}'
)


class FakeProvider:
    def __init__(self, outputs=None, error_on_call=None):
        self.outputs = list(outputs or [VALID_CLASS, VALID_ER, VALID_SEQUENCE])
        self.error_on_call = error_on_call
        self.calls = []

    def complete(self, *, model, messages, temperature, max_tokens):
        call_number = len(self.calls) + 1
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if self.error_on_call == call_number:
            raise RuntimeError("provider unavailable")
        return LLMResponse(
            content=self.outputs.pop(0),
            provider="fake",
            model=model,
            input_tokens=call_number,
            output_tokens=call_number + 10,
            total_tokens=call_number + 20,
            latency_ms=float(call_number * 100),
        )


def candidate_config():
    return CandidateConfig(
        candidate_id="candidate_x",
        provider="fake",
        model="model-x",
        temperature=0.1,
        max_tokens=1234,
    )


def graph_state(outputs=None, error_on_call=None):
    provider = FakeProvider(outputs=outputs, error_on_call=error_on_call)
    return run_candidate_graph(
        candidate_config(),
        "Build ordering.",
        ["REQ-001"],
        provider,
    ), provider


class CandidateLangGraphTests(unittest.TestCase):
    def test_valid_candidate_pipeline(self):
        state, provider = graph_state()

        self.assertEqual(state.status, "valid")
        self.assertIsNotNone(state.final_ir)
        self.assertEqual(len(provider.calls), 3)

    def test_class_validation_failure_followed_by_successful_repair(self):
        state, provider = graph_state([
            INVALID_CLASS,
            VALID_CLASS,
            VALID_ER,
            VALID_SEQUENCE,
        ])

        self.assertEqual(state.status, "valid")
        self.assertEqual(state.repair_metadata["class"]["repair_attempts"], 1)
        self.assertTrue(state.repair_metadata["class"]["repair_success"])
        self.assertEqual(len(provider.calls), 4)

    def test_er_validation_failure_followed_by_successful_repair(self):
        state, provider = graph_state([
            VALID_CLASS,
            INVALID_ER,
            VALID_ER,
            VALID_SEQUENCE,
        ])

        self.assertEqual(state.status, "valid")
        self.assertEqual(state.repair_metadata["er"]["repair_attempts"], 1)
        self.assertTrue(state.repair_metadata["er"]["repair_success"])
        self.assertEqual(len(provider.calls), 4)

    def test_sequence_validation_failure_followed_by_successful_repair(self):
        state, provider = graph_state([
            VALID_CLASS,
            VALID_ER,
            INVALID_SEQUENCE,
            VALID_SEQUENCE,
        ])

        self.assertEqual(state.status, "valid")
        self.assertEqual(state.repair_metadata["sequence"]["repair_attempts"], 1)
        self.assertTrue(state.repair_metadata["sequence"]["repair_success"])
        self.assertEqual(len(provider.calls), 4)

    def test_repair_attempts_exhausted_continue_with_invalid_artifact(self):
        state, provider = graph_state([
            INVALID_CLASS,
            INVALID_CLASS,
            INVALID_CLASS,
            VALID_ER,
            VALID_SEQUENCE_FOR_ORDER_NO_METHODS,
        ])

        self.assertEqual(state.status, "invalid")
        self.assertIsNotNone(state.final_ir)
        self.assertEqual(state.repair_metadata["class"]["repair_attempts"], 2)
        self.assertFalse(state.repair_metadata["class"]["repair_success"])
        self.assertEqual(len(provider.calls), 5)

    def test_malformed_class_response_fails_without_er_or_sequence(self):
        state, provider = graph_state(["not json", VALID_ER, VALID_SEQUENCE])

        self.assertEqual(state.status, "failed")
        self.assertEqual(state.parse_errors[0]["stage"], "class")
        self.assertIsNone(state.er_diagram)
        self.assertEqual(len(provider.calls), 1)

    def test_malformed_er_response_fails_without_sequence(self):
        state, provider = graph_state([VALID_CLASS, "not json", VALID_SEQUENCE])

        self.assertEqual(state.status, "failed")
        self.assertEqual(state.parse_errors[0]["stage"], "er")
        self.assertIsNone(state.sequence_diagrams)
        self.assertEqual(len(provider.calls), 2)

    def test_provider_failure_marks_candidate_failed(self):
        state, provider = graph_state(error_on_call=2)

        self.assertEqual(state.status, "failed")
        self.assertEqual(state.provider_errors[0]["stage"], "er")
        self.assertEqual(state.provider_errors[0]["error_type"], "RuntimeError")
        self.assertEqual(len(provider.calls), 2)

    def test_repair_failure_continues_with_invalid_artifact(self):
        state, provider = graph_state(
            [VALID_CLASS, INVALID_ER, VALID_SEQUENCE],
            error_on_call=3,
        )

        self.assertEqual(state.status, "invalid")
        self.assertIsNotNone(state.final_ir)
        self.assertEqual(state.repair_metadata["er"]["repair_attempts"], 1)
        self.assertEqual(
            state.repair_metadata["er"]["repair_errors"][0]["error_type"],
            "RuntimeError",
        )
        self.assertEqual(len(provider.calls), 4)

    def test_stage_metrics_are_preserved(self):
        state, _ = graph_state()

        self.assertEqual(state.metrics.model_call_count, 3)
        self.assertEqual(state.metrics.total_tokens, 66)
        self.assertEqual(state.metrics.total_latency_ms, 600.0)
        self.assertEqual(state.metrics.stages["class"].provider, "fake")
        self.assertEqual(state.metrics.stages["er"].model, "model-x")
        self.assertEqual(state.metrics.stages["sequence"].model_call_count, 1)

    def test_final_status_and_final_ir_parity_for_invalid_candidate(self):
        state, _ = graph_state([
            INVALID_CLASS,
            INVALID_CLASS,
            INVALID_CLASS,
            INVALID_ER,
            INVALID_ER,
            INVALID_ER,
            INVALID_SEQUENCE,
            INVALID_SEQUENCE,
            INVALID_SEQUENCE,
        ])

        self.assertEqual(state.status, "invalid")
        self.assertEqual(set(state.final_ir.keys()), {
            "class_diagram",
            "er_diagram",
            "sequence_diagrams",
        })

    def test_new_er_schema_survives_complete_candidate_pipeline(self):
        state, _ = graph_state([
            ORDER_MANAGEMENT_CLASS,
            ORDER_MANAGEMENT_ER_NEW_SCHEMA,
            ORDER_MANAGEMENT_SEQUENCE,
        ])

        self.assertEqual(state.status, "valid")
        self.assertIsNotNone(state.final_ir)
        relationships = state.final_ir["er_diagram"]["relationships"]
        self.assertEqual(relationships[0]["name"], "places")
        self.assertEqual(relationships[0]["source_multiplicity"], "1")
        self.assertEqual(relationships[0]["target_multiplicity"], "0..*")
        self.assertEqual(relationships[1]["name"], "contains")
        self.assertEqual(relationships[1]["target_multiplicity"], "1..*")

    def test_er_repair_preserves_new_relationship_fields(self):
        state, _ = graph_state([
            ORDER_MANAGEMENT_CLASS,
            ORDER_MANAGEMENT_ER_OLD_SCHEMA,
            ORDER_MANAGEMENT_ER_NEW_SCHEMA,
            ORDER_MANAGEMENT_SEQUENCE,
        ])

        self.assertEqual(state.status, "valid")
        self.assertTrue(state.repair_metadata["er"]["repair_success"])
        repaired_relationship = state.er_diagram["relationships"][1]
        self.assertEqual(repaired_relationship["name"], "contains")
        self.assertEqual(repaired_relationship["source_multiplicity"], "1")
        self.assertEqual(repaired_relationship["target_multiplicity"], "1..*")

    def test_sequence_repair_corrects_invalid_loop_and_success_order(self):
        state, _ = graph_state([
            ORDER_MANAGEMENT_CLASS,
            ORDER_MANAGEMENT_ER_NEW_SCHEMA,
            ORDER_MANAGEMENT_SEQUENCE_INVALID_LOOP_AND_ORDER,
            ORDER_MANAGEMENT_SEQUENCE,
        ])

        self.assertEqual(state.status, "valid")
        self.assertTrue(state.repair_metadata["sequence"]["repair_success"])
        block = state.sequence_diagrams[0]["logic_blocks"][0]
        self.assertEqual(block["block_type"], "loop")
        self.assertEqual(block["messages"][0]["message"], "createCartItem(cartItem)")


if __name__ == "__main__":
    unittest.main()
