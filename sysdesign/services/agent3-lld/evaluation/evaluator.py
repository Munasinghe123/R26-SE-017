from .syntax_evaluator import SyntaxEvaluator
from .class_evaluator import ClassEvaluator
from .sequence_evaluator import SequenceEvaluator
from .er_evaluator import EREvaluator
from .requirement_evaluator import RequirementEvaluator


class Evaluator:
    """
    Main evaluation orchestrator.

    Combines:
        - Syntax / renderability
        - Class Diagram evaluation
        - Sequence Diagram evaluation
        - ER Diagram evaluation
        - Requirement coverage
    """

    def __init__(self):
        self.syntax_evaluator = SyntaxEvaluator()
        self.class_evaluator = ClassEvaluator()
        self.sequence_evaluator = SequenceEvaluator()
        self.er_evaluator = EREvaluator()
        self.requirement_evaluator = RequirementEvaluator()

    def evaluate(
        self,
        generated: dict,
        reference: dict,
        requirements: list[dict]
    ) -> dict:

        # =========================================================
        # 1. SYNTAX / RENDERABILITY
        # =========================================================

        syntax_results = {}

        diagrams = generated.get(
            "diagrams",
            {}
        )

        for diagram_type in [
            "class",
            "sequence",
            "er"
        ]:

            plantuml_code = diagrams.get(
                diagram_type,
                ""
            )

            syntax_results[diagram_type] = (
                self.syntax_evaluator.evaluate(
                    plantuml_code
                )
            )

        syntax_scores = [
            result["score"]
            for result in syntax_results.values()
        ]

        syntax_score = (
            sum(syntax_scores) / len(syntax_scores)
            if syntax_scores
            else 0.0
        )

        # =========================================================
        # 2. CLASS DIAGRAM
        # =========================================================

        class_result = self.class_evaluator.evaluate(
            generated.get("ir", {}).get(
                "classes",
                []
            )
            if isinstance(
                generated.get("ir"),
                dict
            )
            else {
                "classes": []
            },

            reference.get(
                "class",
                {}
            )
        )

        # =========================================================
        # 3. SEQUENCE DIAGRAM
        # =========================================================

        sequence_result = self.sequence_evaluator.evaluate(
            generated.get("ir", {})
            if isinstance(
                generated.get("ir"),
                dict
            )
            else {},

            reference.get(
                "sequence",
                {}
            )
        )

        # =========================================================
        # 4. ER DIAGRAM
        # =========================================================

        er_result = self.er_evaluator.evaluate(
            generated.get("ir", {})
            if isinstance(
                generated.get("ir"),
                dict
            )
            else {},

            reference.get(
                "er",
                {}
            )
        )

        # =========================================================
        # 5. REQUIREMENT COVERAGE
        # =========================================================

        requirement_result = (
            self.requirement_evaluator.evaluate(
                requirements,
                generated.get("ir", {})
                if isinstance(
                    generated.get("ir"),
                    dict
                )
                else {}
            )
        )

        # =========================================================
        # 6. OVERALL STRUCTURAL SCORE
        # =========================================================

        diagram_f1_scores = [
            class_result.get(
                "overall_f1",
                0.0
            ),

            sequence_result.get(
                "overall_f1",
                0.0
            ),

            er_result.get(
                "overall_f1",
                0.0
            ),
        ]

        structural_f1 = (
            sum(diagram_f1_scores)
            / len(diagram_f1_scores)
            if diagram_f1_scores
            else 0.0
        )

        # =========================================================
        # 7. OVERALL EVALUATION SCORE
        # =========================================================

        overall_score = (
            structural_f1 * 0.60
            + requirement_result.get(
                "coverage_score",
                0.0
            ) * 0.30
            + syntax_score * 0.10
        )

        return {
            "syntax": {
                "class": syntax_results["class"],
                "sequence": syntax_results["sequence"],
                "er": syntax_results["er"],
                "overall_score": round(
                    syntax_score,
                    4
                ),
            },

            "class": class_result,

            "sequence": sequence_result,

            "er": er_result,

            "requirements": requirement_result,

            "summary": {
                "syntax_score": round(
                    syntax_score,
                    4
                ),

                "structural_f1": round(
                    structural_f1,
                    4
                ),

                "requirement_coverage": round(
                    requirement_result.get(
                        "coverage_score",
                        0.0
                    ),
                    4
                ),

                "overall_score": round(
                    overall_score,
                    4
                ),
            }
        }