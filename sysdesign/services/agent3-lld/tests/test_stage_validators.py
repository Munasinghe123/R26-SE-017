import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from validators.stage_validators import (  # noqa: E402
    validate_class_diagram,
    validate_er_diagram,
    validate_sequence_diagrams,
)


CLASS_DIAGRAM = {
    "classes": [
        {
            "name": "OrderService",
            "attributes": [],
            "methods": ["createOrder()", "cancelOrder()"],
        },
        {
            "name": "OrderRepository",
            "attributes": [],
            "methods": ["saveOrder()", "findOrder()"],
        },
        {
            "name": "Order",
            "attributes": ["orderId", "status"],
            "methods": [],
        },
    ],
    "relationships": [
        {
            "source": "OrderService",
            "target": "OrderRepository",
            "type": "dependency",
            "cardinality": "",
        }
    ],
}

ORDER_MANAGEMENT_CLASS_DIAGRAM = {
    "classes": [
        {
            "name": "Customer",
            "attributes": ["customer_id"],
            "methods": ["submitCheckout(customer_id, cart_items)"],
        },
        {
            "name": "FrontendUI",
            "attributes": [],
            "methods": ["submitCheckout(request)", "successResponse(message)"],
        },
        {
            "name": "OrderController",
            "attributes": [],
            "methods": [
                "submitCheckout(request)",
                "validateCartNotEmpty()",
                "calculateTotalPrice()",
            ],
        },
        {
            "name": "Order",
            "attributes": ["order_id", "customer_id", "total_price"],
            "methods": ["validateCartNotEmpty()", "calculateTotalPrice()"],
        },
        {
            "name": "DatabaseRepository",
            "attributes": [],
            "methods": ["createOrder(order)", "createCartItem(cartItem)"],
        },
    ],
    "relationships": [],
}


def rule_ids(result):
    return {error["rule_id"] for error in result["errors"]}


def codes(result):
    return {error["code"] for error in result["errors"]}


class StageValidatorTests(unittest.TestCase):
    def test_valid_class_passes(self):
        result = validate_class_diagram(CLASS_DIAGRAM)

        self.assertTrue(result["passed"])
        self.assertTrue(result["valid"])
        self.assertEqual(result["stage"], "class")

    def test_bad_class_relationship_endpoint_fails(self):
        diagram = {
            **CLASS_DIAGRAM,
            "relationships": [{
                "source": "OrderService",
                "target": "MissingRepository",
                "type": "dependency",
                "cardinality": "",
            }],
        }

        result = validate_class_diagram(diagram)

        self.assertFalse(result["passed"])
        self.assertIn("UNKNOWN_CLASS_RELATIONSHIP_TARGET", codes(result))

    def test_invalid_relationship_type_and_cardinality_fail(self):
        diagram = {
            **CLASS_DIAGRAM,
            "relationships": [{
                "source": "OrderService",
                "target": "OrderRepository",
                "type": "uses",
                "cardinality": "many",
            }],
        }

        result = validate_class_diagram(diagram)

        self.assertIn("CLASS-REL-TYPE", rule_ids(result))
        self.assertIn("CLASS-REL-CARDINALITY", rule_ids(result))

    def test_er_primary_key_missing_from_attributes_fails(self):
        er_diagram = {
            "entities": [{
                "name": "Order",
                "attributes": ["customerId", "status"],
                "primary_key": "orderId",
            }],
            "relationships": [],
        }

        result = validate_er_diagram(er_diagram, CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("PRIMARY_KEY_ATTRIBUTE_MISSING", codes(result))

    def test_valid_er_primary_key_passes(self):
        er_diagram = {
            "entities": [{
                "name": "Order",
                "attributes": ["orderId", "status"],
                "primary_key": "orderId",
            }],
            "relationships": [],
        }

        result = validate_er_diagram(er_diagram, CLASS_DIAGRAM)

        self.assertTrue(result["passed"])

    def test_er_relationship_requires_semantic_name_separate_from_type(self):
        er_diagram = {
            "entities": [
                {"name": "Customer", "attributes": ["customer_id"], "primary_key": "customer_id"},
                {"name": "Order", "attributes": ["order_id"], "primary_key": "order_id"},
            ],
            "relationships": [{
                "name": "one-to-many",
                "source": "Customer",
                "target": "Order",
                "type": "one-to-many",
                "source_multiplicity": "1",
                "target_multiplicity": "0..*",
                "evidence": "A customer can have multiple orders.",
            }],
        }

        result = validate_er_diagram(er_diagram, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("CARDINALITY_LABEL_USED_AS_RELATIONSHIP_NAME", codes(result))

    def test_er_relationship_multiplicity_values_are_validated(self):
        er_diagram = {
            "entities": [
                {"name": "Customer", "attributes": ["customer_id"], "primary_key": "customer_id"},
                {"name": "Order", "attributes": ["order_id"], "primary_key": "order_id"},
            ],
            "relationships": [{
                "name": "places",
                "source": "Customer",
                "target": "Order",
                "type": "one-to-many",
                "source_multiplicity": "exactly one",
                "target_multiplicity": "many",
                "evidence": "A customer can have multiple orders.",
            }],
        }

        result = validate_er_diagram(er_diagram, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("UNSUPPORTED_ER_MULTIPLICITY", codes(result))

    def test_er_one_or_more_cannot_be_zero_or_more(self):
        er_diagram = {
            "entities": [
                {"name": "Order", "attributes": ["order_id"], "primary_key": "order_id"},
                {"name": "CartItem", "attributes": ["cart_item_id"], "primary_key": "cart_item_id"},
            ],
            "relationships": [{
                "name": "contains",
                "source": "Order",
                "target": "CartItem",
                "type": "one-to-many",
                "source_multiplicity": "1",
                "target_multiplicity": "0..*",
                "evidence": "An order contains one or more cart items.",
            }],
        }

        result = validate_er_diagram(er_diagram, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("ONE_OR_MORE_MODELED_AS_ZERO_OR_MORE", codes(result))

    def test_nested_sequence_invalid_receiver_fails(self):
        sequence = [{
            "name": "Create Order",
            "participants": ["OrderService"],
            "logic_blocks": [{
                "block_type": "alt",
                "condition": "valid",
                "messages": [{
                    "from": "OrderService",
                    "to": "MissingRepository",
                    "message": "saveOrder()",
                }],
            }],
            "messages": [],
        }]

        result = validate_sequence_diagrams(sequence, CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("UNDECLARED_MESSAGE_RECEIVER", codes(result))

    def test_nested_sequence_invalid_method_fails(self):
        sequence = [{
            "name": "Create Order",
            "participants": ["OrderService", "OrderRepository"],
            "logic_blocks": [{
                "block_type": "alt",
                "condition": "valid",
                "messages": [{
                    "from": "OrderService",
                    "to": "OrderRepository",
                    "message": "missingMethod()",
                }],
            }],
            "messages": [],
        }]

        result = validate_sequence_diagrams(sequence, CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("UNKNOWN_RECEIVER_METHOD", codes(result))

    def test_for_each_condition_must_use_loop_not_alt(self):
        sequence = [{
            "name": "Submit Checkout",
            "participants": ["OrderController", "DatabaseRepository"],
            "logic_blocks": [{
                "block_type": "alt",
                "condition": "for each cart item",
                "messages": [{
                    "from": "OrderController",
                    "to": "DatabaseRepository",
                    "message": "createCartItem(cartItem)",
                }],
            }],
            "messages": [],
        }]

        result = validate_sequence_diagrams(sequence, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("ITERATION_MUST_USE_LOOP", codes(result))

    def test_for_every_condition_must_use_loop_not_alt(self):
        sequence = [{
            "name": "Submit Checkout",
            "participants": ["OrderController", "DatabaseRepository"],
            "logic_blocks": [{
                "block_type": "alt",
                "condition": "for every cart item",
                "messages": [{
                    "from": "OrderController",
                    "to": "DatabaseRepository",
                    "message": "createCartItem(cartItem)",
                }],
            }],
            "messages": [],
        }]

        result = validate_sequence_diagrams(sequence, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("ITERATION_MUST_USE_LOOP", codes(result))

    def test_alt_remains_valid_for_genuine_conditional_alternative(self):
        sequence = [{
            "name": "Submit Checkout",
            "participants": ["OrderController", "Order"],
            "logic_blocks": [{
                "block_type": "alt",
                "condition": "cart is empty",
                "messages": [{
                    "from": "OrderController",
                    "to": "Order",
                    "message": "validateCartNotEmpty()",
                }],
            }],
            "messages": [],
        }]

        result = validate_sequence_diagrams(sequence, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertTrue(result["passed"])

    def test_success_cannot_precede_mandatory_loop_work(self):
        sequence = [{
            "name": "Submit Checkout",
            "participants": ["OrderController", "FrontendUI", "DatabaseRepository"],
            "messages": [
                {
                    "from": "OrderController",
                    "to": "FrontendUI",
                    "message": "successResponse(message)",
                },
                {
                    "from": "OrderController",
                    "to": "DatabaseRepository",
                    "message": "createCartItem(cartItem)",
                },
            ],
            "logic_blocks": [],
        }]

        result = validate_sequence_diagrams(sequence, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("SUCCESS_BEFORE_MANDATORY_OPERATION", codes(result))

    def test_required_main_flow_message_ordering_allows_required_loop_before_success(self):
        sequence = [{
            "name": "Submit Checkout",
            "participants": ["Customer", "FrontendUI", "OrderController", "Order", "DatabaseRepository"],
            "participant_types": {"Customer": "actor"},
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
                "messages": [{
                    "from": "OrderController",
                    "to": "DatabaseRepository",
                    "message": "createCartItem(cartItem)",
                }],
            }],
        }]

        result = validate_sequence_diagrams(sequence, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertTrue(result["passed"])
        self.assertNotIn("SUCCESS_BEFORE_MANDATORY_OPERATION", codes(result))

    def test_required_main_flow_message_ordering_rejects_out_of_order_operations(self):
        sequence = [{
            "name": "Submit Checkout",
            "participants": ["Customer", "FrontendUI", "OrderController", "Order", "DatabaseRepository"],
            "participant_types": {"Customer": "actor"},
            "messages": [
                {"from": "Customer", "to": "FrontendUI", "message": "submitCheckout(customer_id, cart_items)"},
                {"from": "FrontendUI", "to": "OrderController", "message": "submitCheckout(request)"},
                {"from": "OrderController", "to": "Order", "message": "calculateTotalPrice()"},
                {"from": "OrderController", "to": "Order", "message": "validateCartNotEmpty()"},
                {"from": "OrderController", "to": "DatabaseRepository", "message": "createOrder(order)"},
                {"from": "OrderController", "to": "DatabaseRepository", "message": "createCartItem(cartItem)"},
                {"from": "OrderController", "to": "FrontendUI", "message": "successResponse(message)"},
            ],
            "logic_blocks": [],
        }]

        result = validate_sequence_diagrams(sequence, ORDER_MANAGEMENT_CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("MAIN_FLOW_MESSAGE_ORDER_VIOLATION", codes(result))

    def test_declared_external_participant_is_handled_correctly(self):
        sequence = [{
            "name": "Create Order",
            "participants": ["Customer", "OrderService"],
            "participant_types": {
                "Customer": "actor",
                "OrderService": "control",
            },
            "messages": [{
                "from": "Customer",
                "to": "OrderService",
                "message": "createOrder()",
            }],
        }]

        result = validate_sequence_diagrams(sequence, CLASS_DIAGRAM)

        self.assertTrue(result["passed"])
        self.assertEqual(result["warnings"][0]["code"], "DECLARED_EXTERNAL_PARTICIPANT")

    def test_undeclared_participant_fails(self):
        sequence = [{
            "name": "Create Order",
            "participants": ["OrderService"],
            "messages": [{
                "from": "OrderService",
                "to": "OrderRepository",
                "message": "saveOrder()",
            }],
        }]

        result = validate_sequence_diagrams(sequence, CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("UNDECLARED_MESSAGE_RECEIVER", codes(result))

    def test_valid_internal_participant_passes(self):
        sequence = [{
            "name": "Create Order",
            "participants": ["OrderService", "OrderRepository"],
            "messages": [{
                "from": "OrderService",
                "to": "OrderRepository",
                "message": "saveOrder()",
            }],
        }]

        result = validate_sequence_diagrams(sequence, CLASS_DIAGRAM)

        self.assertTrue(result["passed"])

    def test_sequence_method_must_exist_on_receiving_class(self):
        sequence = [{
            "name": "Create Order",
            "participants": ["OrderService", "OrderRepository"],
            "messages": [{
                "from": "OrderService",
                "to": "OrderRepository",
                "message": "createOrder()",
            }],
        }]

        result = validate_sequence_diagrams(sequence, CLASS_DIAGRAM)

        self.assertFalse(result["passed"])
        self.assertIn("SEQ-METHOD", rule_ids(result))


if __name__ == "__main__":
    unittest.main()
