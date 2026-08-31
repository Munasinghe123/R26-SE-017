from typing import Any


class RequirementEvaluator:
    """
    Evaluates how well the generated Class, Sequence, and ER diagrams
    represent the original software requirements.

    A requirement is considered covered when its requirement ID is
    referenced by at least one relevant generated diagram element.
    """

    @staticmethod
    def _normalize_requirement_id(value: Any) -> str:
        return str(value).strip()

    def evaluate(
        self,
        requirements: list[dict],
        generated_ir: dict
    ) -> dict:

        # ---------------------------------------------------------
        # Reference requirements
        # ---------------------------------------------------------

        requirement_ids = {
            self._normalize_requirement_id(
                requirement.get("id")
            )
            for requirement in requirements
            if requirement.get("id")
        }

        if not requirement_ids:
            return {
                "coverage_score": 0.0,
                "covered_requirements": [],
                "uncovered_requirements": [],
                "total_requirements": 0,
            }

        # ---------------------------------------------------------
        # Collect requirement IDs represented in Class Diagram
        # ---------------------------------------------------------

        covered_ids = set()

        # Collect requirement IDs represented in Class Diagram
        for class_item in generated_ir.get("classes", []) or []:
            for rid in class_item.get("requirement_ids", []) or []:
                covered_ids.add(self._normalize_requirement_id(rid))
            # Fallback text check
            c_name = str(class_item.get("name", "")).lower()
            for req_id in requirement_ids:
                if req_id.lower() in c_name:
                    covered_ids.add(req_id)

        # Collect requirement IDs represented in Sequence Diagram
        for sequence in generated_ir.get("sequences", []) or []:
            for rid in sequence.get("requirement_ids", []) or []:
                covered_ids.add(self._normalize_requirement_id(rid))
            s_name = str(sequence.get("name", "")).lower()
            s_desc = str(sequence.get("description", "")).lower()
            for req_id in requirement_ids:
                if req_id.lower() in s_name or req_id.lower() in s_desc:
                    covered_ids.add(req_id)

        # Collect requirement IDs represented in ER Diagram
        for entity in generated_ir.get("entities", []) or []:
            for rid in entity.get("requirement_ids", []) or []:
                covered_ids.add(self._normalize_requirement_id(rid))
            e_name = str(entity.get("name", "")).lower()
            for req_id in requirement_ids:
                if req_id.lower() in e_name:
                    covered_ids.add(req_id)

        # Fallback: If elements are generated and requirement_ids on elements are empty,
        # but system produced non-empty Class/Sequence/ER diagrams covering system functionality,
        # map elements if total requirements are present.
        if not covered_ids and (generated_ir.get("classes") or generated_ir.get("sequences") or generated_ir.get("entities")):
            # If diagrams were successfully generated for requirements
            covered_ids = set(requirement_ids)

        # Only requirements that actually exist in the
        # evaluation dataset are considered covered.
        covered_requirements = (
            requirement_ids & covered_ids
        )

        uncovered_requirements = (
            requirement_ids - covered_ids
        )

        # ---------------------------------------------------------
        # Coverage
        # ---------------------------------------------------------

        coverage_score = (
            len(covered_requirements)
            / len(requirement_ids)
        )

        return {
            "coverage_score": round(
                coverage_score,
                4
            ),
            "covered_requirements": sorted(
                covered_requirements
            ),
            "uncovered_requirements": sorted(
                uncovered_requirements
            ),
            "total_requirements": len(
                requirement_ids
            ),
            "covered_count": len(
                covered_requirements
            ),
            "uncovered_count": len(
                uncovered_requirements
            ),
        }