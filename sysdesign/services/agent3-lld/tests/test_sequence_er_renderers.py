import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from utils.irGenerator import (  # noqa: E402
    _to_chen_cardinality,
    generate_er_plantuml,
    generate_sequence_plantuml,
)


ORDER_MANAGEMENT_SEQUENCE_IR = {
    "name": "Submit Checkout",
    "participants": ["Customer", "FrontendUI", "OrderController", "Order", "DatabaseRepository"],
    "participant_types": {
        "Customer": "actor",
        "FrontendUI": "boundary",
        "OrderController": "control",
        "Order": "entity",
        "DatabaseRepository": "participant",
    },
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
        "condition": "[for each cart item]",
        "messages": [{
            "from": "OrderController",
            "to": "DatabaseRepository",
            "message": "createCartItem(cartItem)",
        }],
    }],
}


ORDER_MANAGEMENT_ER_IR = {
    "entities": [
        {"name": "Customer", "attributes": ["customer_id"], "primary_key": "customer_id"},
        {"name": "Order", "attributes": ["order_id", "customer_id"], "primary_key": "order_id"},
        {"name": "CartItem", "attributes": ["cart_item_id", "order_id"], "primary_key": "cart_item_id"},
    ],
    "relationships": [
        {
            "name": "places",
            "source": "Customer",
            "target": "Order",
            "type": "one-to-many",
            "source_multiplicity": "1",
            "target_multiplicity": "0..*",
            "evidence": "A customer may place zero or more orders.",
        },
        {
            "name": "contains",
            "source": "Order",
            "target": "CartItem",
            "type": "one-to-many",
            "source_multiplicity": "1",
            "target_multiplicity": "1..*",
            "evidence": "An order contains one or more cart items.",
        },
    ],
}


class SequenceAndErRendererTests(unittest.TestCase):
    def test_chen_cardinality_conversion(self):
        self.assertEqual(_to_chen_cardinality("1"), "1")
        self.assertEqual(_to_chen_cardinality("0..1"), "(0,1)")
        self.assertEqual(_to_chen_cardinality("0..*"), "(0,N)")
        self.assertEqual(_to_chen_cardinality("1..*"), "(1,N)")

    def test_chen_cardinality_rejects_unsupported_values(self):
        with self.assertRaises(ValueError):
            _to_chen_cardinality("many")

    def test_sequence_renderer_preserves_loop_fragment_type_for_each(self):
        plantuml = generate_sequence_plantuml(ORDER_MANAGEMENT_SEQUENCE_IR)

        self.assertIn("loop [for each cart item]", plantuml)
        self.assertNotIn("alt [for each cart item]", plantuml)

    def test_sequence_renderer_preserves_loop_fragment_type_for_every(self):
        sequence = {
            **ORDER_MANAGEMENT_SEQUENCE_IR,
            "logic_blocks": [{
                **ORDER_MANAGEMENT_SEQUENCE_IR["logic_blocks"][0],
                "condition": "[for every cart item]",
            }],
        }

        plantuml = generate_sequence_plantuml(sequence)

        self.assertIn("loop [for every cart item]", plantuml)
        self.assertNotIn("alt [for every cart item]", plantuml)

    def test_sequence_renderer_keeps_genuine_alt_fragment(self):
        sequence = {
            **ORDER_MANAGEMENT_SEQUENCE_IR,
            "messages": [],
            "logic_blocks": [{
                "block_type": "alt",
                "condition": "[cart is empty]",
                "messages": [{
                    "from": "OrderController",
                    "to": "Order",
                    "message": "validateCartNotEmpty()",
                }],
            }],
        }

        plantuml = generate_sequence_plantuml(sequence)

        self.assertIn("alt [cart is empty]", plantuml)

    def test_sequence_renderer_places_success_after_loop_work(self):
        plantuml = generate_sequence_plantuml(ORDER_MANAGEMENT_SEQUENCE_IR)

        self.assertLess(plantuml.index("createOrder(order)"), plantuml.index("loop [for each cart item]"))
        self.assertLess(plantuml.index("createCartItem(cartItem)"), plantuml.index("successResponse(message)"))

    def test_er_renderer_uses_semantic_name_not_relationship_type(self):
        plantuml = generate_er_plantuml(ORDER_MANAGEMENT_ER_IR)[0]

        self.assertIn('relationship "places" as REL_0 {', plantuml)
        self.assertIn('relationship "contains" as REL_1 {', plantuml)
        self.assertNotIn('relationship "one-to-many"', plantuml)

    def test_er_renderer_preserves_precise_multiplicities(self):
        plantuml = generate_er_plantuml(ORDER_MANAGEMENT_ER_IR)[0]

        self.assertIn("REL_0-1- CUSTOMER", plantuml)
        self.assertIn("REL_0-(0,N)- ORDER", plantuml)
        self.assertIn("REL_1-1- ORDER", plantuml)
        self.assertIn("REL_1-(1,N)- CARTITEM", plantuml)

    def test_er_renderer_preserves_optional_one(self):
        plantuml = generate_er_plantuml({
            "entities": [
                {"name": "Customer", "attributes": ["customer_id"], "primary_key": "customer_id"},
                {"name": "Profile", "attributes": ["profile_id"], "primary_key": "profile_id"},
            ],
            "relationships": [{
                "name": "owns",
                "source": "Customer",
                "target": "Profile",
                "type": "one-to-one",
                "source_multiplicity": "1",
                "target_multiplicity": "0..1",
                "evidence": "A customer may have one profile.",
            }],
        })[0]

        self.assertIn("REL_0-(0,1)- PROFILE", plantuml)

    def test_er_renderer_preserves_exact_one(self):
        plantuml = generate_er_plantuml({
            "entities": [
                {"name": "Invoice", "attributes": ["invoice_id"], "primary_key": "invoice_id"},
                {"name": "Payment", "attributes": ["payment_id"], "primary_key": "payment_id"},
            ],
            "relationships": [{
                "name": "settles",
                "source": "Payment",
                "target": "Invoice",
                "type": "one-to-one",
                "source_multiplicity": "1",
                "target_multiplicity": "1",
                "evidence": "Each payment settles exactly one invoice.",
            }],
        })[0]

        self.assertIn("REL_0-1- INVOICE", plantuml)

    def test_order_management_er_plantuml_uses_valid_chen_notation(self):
        plantuml = generate_er_plantuml(ORDER_MANAGEMENT_ER_IR)[0]

        expected_lines = [
            "@startchen",
            '<style>',
            'entity "Customer" as CUSTOMER {',
            "    customer_id <<key>>",
            "}",
            'entity "Order" as ORDER {',
            "    order_id <<key>>",
            "    customer_id",
            "}",
            'entity "CartItem" as CARTITEM {',
            "    cart_item_id <<key>>",
            "    order_id",
            "}",
            'relationship "places" as REL_0 {',
            "}",
            'relationship "contains" as REL_1 {',
            "}",
            "REL_0-1- CUSTOMER",
            "REL_0-(0,N)- ORDER",
            "REL_1-1- ORDER",
            "REL_1-(1,N)- CARTITEM",
            "@endchen",
        ]

        for line in expected_lines:
            self.assertIn(line, plantuml)


if __name__ == "__main__":
    unittest.main()
