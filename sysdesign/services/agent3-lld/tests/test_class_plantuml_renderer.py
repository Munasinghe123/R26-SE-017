import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from utils.irGenerator import generate_class_plantuml  # noqa: E402


def class_diagram_with_relationships(relationships):
    return {
        "classes": [
            {"name": "FrontendUI", "attributes": [], "methods": ["submitOrder()"]},
            {"name": "OrderController", "attributes": [], "methods": ["createOrder()"]},
            {"name": "DatabaseRepository", "attributes": [], "methods": ["saveOrder()"]},
            {"name": "Order", "attributes": ["id"], "methods": ["cancelOrder()"]},
            {"name": "SpecialOrder", "attributes": ["priority"], "methods": []},
            {"name": "OrderLine", "attributes": ["quantity"], "methods": []},
        ],
        "relationships": relationships,
    }


class ClassPlantUMLRendererTests(unittest.TestCase):
    def test_dependency_direction_points_from_source_to_target(self):
        plantuml = generate_class_plantuml(class_diagram_with_relationships([
            {
                "source": "FrontendUI",
                "target": "OrderController",
                "type": "dependency",
                "cardinality": "",
            }
        ]))

        self.assertIn("FrontendUI ..> OrderController", plantuml)
        self.assertNotIn("FrontendUI <.. OrderController", plantuml)

    def test_dependency_ignores_accidental_cardinality(self):
        plantuml = generate_class_plantuml(class_diagram_with_relationships([
            {
                "source": "OrderController",
                "target": "DatabaseRepository",
                "type": "dependency",
                "cardinality": "1",
            }
        ]))

        self.assertIn("OrderController ..> DatabaseRepository", plantuml)
        self.assertNotIn('OrderController "1" ..> "1" DatabaseRepository', plantuml)
        self.assertNotIn('OrderController "1"', plantuml)
        self.assertNotIn('"1" DatabaseRepository', plantuml)

    def test_multiple_dependency_chain_keeps_source_target_direction(self):
        plantuml = generate_class_plantuml(class_diagram_with_relationships([
            {
                "source": "FrontendUI",
                "target": "OrderController",
                "type": "dependency",
                "cardinality": "1",
            },
            {
                "source": "OrderController",
                "target": "DatabaseRepository",
                "type": "dependency",
                "cardinality": "1",
            },
        ]))

        self.assertIn("FrontendUI ..> OrderController", plantuml)
        self.assertIn("OrderController ..> DatabaseRepository", plantuml)
        self.assertNotIn("<..", plantuml)

    def test_non_dependency_relationship_mappings_are_preserved(self):
        plantuml = generate_class_plantuml(class_diagram_with_relationships([
            {
                "source": "OrderController",
                "target": "Order",
                "type": "association",
                "cardinality": "1",
            },
            {
                "source": "Order",
                "target": "OrderLine",
                "type": "composition",
                "cardinality": "1..*",
            },
            {
                "source": "DatabaseRepository",
                "target": "Order",
                "type": "aggregation",
                "cardinality": "0..*",
            },
            {
                "source": "SpecialOrder",
                "target": "Order",
                "type": "inheritance",
                "cardinality": "1",
            },
        ]))

        self.assertIn('OrderController "1" -- "1" Order', plantuml)
        self.assertIn('Order "1" *-- "*" OrderLine', plantuml)
        self.assertIn('DatabaseRepository "1" o-- "0..*" Order', plantuml)
        self.assertIn('SpecialOrder "1" <|-- "1" Order', plantuml)


if __name__ == "__main__":
    unittest.main()
