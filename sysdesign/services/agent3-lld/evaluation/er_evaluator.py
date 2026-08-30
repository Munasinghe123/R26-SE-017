from typing import Any


class EREvaluator:
    """
    Reference-based evaluation for ER Diagrams.

    Evaluates:
        - Entities
        - Attributes
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
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive > 0
            else 0.0
        )

        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative > 0
            else 0.0
        )

        f1 = (
            2 * precision * recall / (precision + recall)
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

        generated_entities = generated.get(
            "entities",
            []
        ) or []

        reference_entities = reference.get(
            "entities",
            []
        ) or []

        # ---------------------------------------------------------
        # Entities
        # ---------------------------------------------------------

        generated_entity_names = {
            self._normalize(entity.get("name"))
            for entity in generated_entities
            if entity.get("name")
        }

        reference_entity_names = {
            self._normalize(entity.get("name"))
            for entity in reference_entities
            if entity.get("name")
        }

        entity_result = self._prf(
            generated_entity_names,
            reference_entity_names
        )

        # ---------------------------------------------------------
        # Attributes
        # ---------------------------------------------------------

        generated_attributes = set()

        for entity in generated_entities:
            entity_name = self._normalize(
                entity.get("name")
            )

            for attribute in entity.get(
                "attributes",
                []
            ) or []:

                if isinstance(attribute, dict):
                    attribute_name = attribute.get(
                        "name",
                        ""
                    )
                else:
                    attribute_name = str(attribute)

                if attribute_name:
                    generated_attributes.add(
                        f"{entity_name}.{self._normalize(attribute_name)}"
                    )

        reference_attributes = set()

        for entity in reference_entities:
            entity_name = self._normalize(
                entity.get("name")
            )

            for attribute in entity.get(
                "attributes",
                []
            ) or []:

                if isinstance(attribute, dict):
                    attribute_name = attribute.get(
                        "name",
                        ""
                    )
                else:
                    attribute_name = str(attribute)

                if attribute_name:
                    reference_attributes.add(
                        f"{entity_name}.{self._normalize(attribute_name)}"
                    )

        attribute_result = self._prf(
            generated_attributes,
            reference_attributes
        )

        # ---------------------------------------------------------
        # Relationships
        # ---------------------------------------------------------

        generated_relationships = set()

        for entity in generated_entities:
            source = self._normalize(
                entity.get("name")
            )

            for relationship in entity.get(
                "relationships",
                []
            ) or []:

                target = self._normalize(
                    relationship.get("target", "")
                )

                relationship_type = self._normalize(
                    relationship.get(
                        "rel_type",
                        relationship.get("type", "")
                    )
                )

                if source and target:
                    generated_relationships.add(
                        f"{source}->{target}:{relationship_type}"
                    )

        reference_relationships = set()

        for entity in reference_entities:
            source = self._normalize(
                entity.get("name")
            )

            for relationship in entity.get(
                "relationships",
                []
            ) or []:

                target = self._normalize(
                    relationship.get("target", "")
                )

                relationship_type = self._normalize(
                    relationship.get(
                        "rel_type",
                        relationship.get("type", "")
                    )
                )

                if source and target:
                    reference_relationships.add(
                        f"{source}->{target}:{relationship_type}"
                    )

        relationship_result = self._prf(
            generated_relationships,
            reference_relationships
        )

        # ---------------------------------------------------------
        # Overall ER score
        # ---------------------------------------------------------

        f1_scores = [
            entity_result["f1"],
            attribute_result["f1"],
            relationship_result["f1"],
        ]

        overall_f1 = (
            sum(f1_scores) / len(f1_scores)
            if f1_scores
            else 0.0
        )

        return {
            "entities": entity_result,
            "attributes": attribute_result,
            "relationships": relationship_result,
            "overall_f1": round(overall_f1, 4),
        }