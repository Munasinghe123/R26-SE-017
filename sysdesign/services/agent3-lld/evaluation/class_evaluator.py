from typing import Any


class ClassEvaluator:
    """
    Reference-based evaluation for Class Diagrams.

    Compares generated ClassIR data against a reference ClassIR
    and calculates Precision, Recall and F1 for:
        - Classes
        - Attributes
        - Methods
        - Relationships
    """

    @staticmethod
    def _normalize(value: Any) -> str:
        return str(value).strip().lower()

    @staticmethod
    def _prf(
        generated: set[str],
        reference: set[str]
    ) -> dict:

        true_positive = len(generated & reference)
        false_positive = len(generated - reference)
        false_negative = len(reference - generated)

        precision = (
            true_positive /
            (true_positive + false_positive)
            if true_positive + false_positive > 0
            else 0.0
        )

        recall = (
            true_positive /
            (true_positive + false_negative)
            if true_positive + false_negative > 0
            else 0.0
        )

        f1 = (
            2 * precision * recall /
            (precision + recall)
            if precision + recall > 0
            else 0.0
        )

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
        }

    def evaluate(
        self,
        generated: dict,
        reference: dict
    ) -> dict:

        generated_classes = generated.get("classes", [])
        reference_classes = reference.get("classes", [])

        # ---------------------------------------------------------
        # Classes
        # ---------------------------------------------------------

        generated_class_names = {
            self._normalize(cls.get("name"))
            for cls in generated_classes
            if cls.get("name")
        }

        reference_class_names = {
            self._normalize(cls.get("name"))
            for cls in reference_classes
            if cls.get("name")
        }

        class_result = self._prf(
            generated_class_names,
            reference_class_names
        )

        # ---------------------------------------------------------
        # Attributes
        # ---------------------------------------------------------

        generated_attributes = set()

        for cls in generated_classes:
            class_name = self._normalize(cls.get("name"))

            for attribute in cls.get("attributes", []) or []:
                generated_attributes.add(
                    f"{class_name}.{self._normalize(attribute)}"
                )

        reference_attributes = set()

        for cls in reference_classes:
            class_name = self._normalize(cls.get("name"))

            for attribute in cls.get("attributes", []) or []:
                reference_attributes.add(
                    f"{class_name}.{self._normalize(attribute)}"
                )

        attribute_result = self._prf(
            generated_attributes,
            reference_attributes
        )

        # ---------------------------------------------------------
        # Methods
        # ---------------------------------------------------------

        generated_methods = set()

        for cls in generated_classes:
            class_name = self._normalize(cls.get("name"))

            for method in cls.get("methods", []) or []:

                if isinstance(method, dict):
                    method_name = method.get("name", "")
                else:
                    method_name = str(method)

                if method_name:
                    generated_methods.add(
                        f"{class_name}.{self._normalize(method_name)}"
                    )

        reference_methods = set()

        for cls in reference_classes:
            class_name = self._normalize(cls.get("name"))

            for method in cls.get("methods", []) or []:

                if isinstance(method, dict):
                    method_name = method.get("name", "")
                else:
                    method_name = str(method)

                if method_name:
                    reference_methods.add(
                        f"{class_name}.{self._normalize(method_name)}"
                    )

        method_result = self._prf(
            generated_methods,
            reference_methods
        )

        # ---------------------------------------------------------
        # Relationships
        # ---------------------------------------------------------

        generated_relationships = set()

        for cls in generated_classes:
            source = self._normalize(cls.get("name"))

            for relationship in cls.get("relationships", []) or []:

                target = self._normalize(
                    relationship.get("target", "")
                )

                rel_type = self._normalize(
                    relationship.get("type", relationship.get("rel_type", ""))
                )

                cardinality = self._normalize(
                    relationship.get("cardinality", "")
                )

                if source and target:
                    generated_relationships.add(
                        f"{source}->{target}:{rel_type}:{cardinality}"
                    )

        reference_relationships = set()

        for cls in reference_classes:
            source = self._normalize(cls.get("name"))

            for relationship in cls.get("relationships", []) or []:

                target = self._normalize(
                    relationship.get("target", "")
                )

                rel_type = self._normalize(
                    relationship.get("type", relationship.get("rel_type", ""))
                )

                cardinality = self._normalize(
                    relationship.get("cardinality", "")
                )

                if source and target:
                    reference_relationships.add(
                        f"{source}->{target}:{rel_type}:{cardinality}"
                    )

        relationship_result = self._prf(
            generated_relationships,
            reference_relationships
        )

        # ---------------------------------------------------------
        # Overall Class Diagram score
        # ---------------------------------------------------------

        f1_scores = [
            class_result["f1"],
            attribute_result["f1"],
            method_result["f1"],
            relationship_result["f1"],
        ]

        overall_f1 = (
            sum(f1_scores) / len(f1_scores)
            if f1_scores
            else 0.0
        )

        return {
            "classes": class_result,
            "attributes": attribute_result,
            "methods": method_result,
            "relationships": relationship_result,
            "overall_f1": round(overall_f1, 4),
        }