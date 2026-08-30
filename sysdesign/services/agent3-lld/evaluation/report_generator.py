from typing import Any


class EvaluationReportGenerator:
    """
    Converts evaluation results into:
        1. A compact summary for the admin/panel view
        2. A detailed report for research analysis
    """

    @staticmethod
    def _percentage(value: Any) -> float:
        try:
            return round(float(value) * 100, 2)
        except (TypeError, ValueError):
            return 0.0

    def generate(self, evaluation_result: dict) -> dict:

        summary = evaluation_result.get(
            "summary",
            {}
        )

        class_result = evaluation_result.get(
            "class",
            {}
        )

        sequence_result = evaluation_result.get(
            "sequence",
            {}
        )

        er_result = evaluation_result.get(
            "er",
            {}
        )

        requirements = evaluation_result.get(
            "requirements",
            {}
        )

        syntax = evaluation_result.get(
            "syntax",
            {}
        )

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        summary_report = {
            "overall_score": self._percentage(
                summary.get("overall_score", 0.0)
            ),

            "syntax_score": self._percentage(
                summary.get("syntax_score", 0.0)
            ),

            "structural_f1": self._percentage(
                summary.get("structural_f1", 0.0)
            ),

            "requirement_coverage": self._percentage(
                summary.get("requirement_coverage", 0.0)
            ),

            "diagrams": {
                "class": self._percentage(
                    class_result.get("overall_f1", 0.0)
                ),

                "sequence": self._percentage(
                    sequence_result.get("overall_f1", 0.0)
                ),

                "er": self._percentage(
                    er_result.get("overall_f1", 0.0)
                ),
            }
        }

        # ---------------------------------------------------------
        # Detailed report
        # ---------------------------------------------------------

        detailed_report = {
            "syntax": syntax,

            "class": class_result,

            "sequence": sequence_result,

            "er": er_result,

            "requirements": requirements,
        }

        return {
            "summary": summary_report,
            "details": detailed_report,
        }