import logging
from schemas.ir_schema import IntermediateRepresentation
from schemas.api_models import (
    TraceabilityEntry,
    OverDesignFlag,
)

logger = logging.getLogger(__name__)


class OverDesignDetector:
    """
    Module 4: Over-Design Detector.
    Checks bidirectional traceability:
    - Forward: Every requirement has at least one Class/Entity/Sequence
    - Backward: Every Class/Entity/Sequence maps to at least one requirement
    """

    def detect(
        self,
        ir: IntermediateRepresentation,
        requirement_ids: list[str],
    ) -> tuple[list[TraceabilityEntry], list[OverDesignFlag]]:
        """
        Run traceability analysis.
        Returns the traceability matrix and a list of over-design flags.
        """
        traceability_matrix: list[TraceabilityEntry] = []
        overdesign_flags: list[OverDesignFlag] = []

        # ------------------------------------------
        # 1. Build forward traceability matrix
        #    (Requirement → which artifacts cover it)
        # ------------------------------------------
        for req_id in requirement_ids:
            entry = TraceabilityEntry(
                requirement_id=req_id,
                mapped_classes=[
                    cls.name for cls in ir.classes
                    if req_id in cls.requirement_ids
                ],
                mapped_sequences=[
                    seq.name for seq in ir.sequences
                    if req_id in seq.requirement_ids
                ],
                mapped_entities=[
                    entity.name for entity in ir.entities
                    if req_id in entity.requirement_ids
                ],
            )

            # Check if requirement is covered
            entry.is_covered = bool(
                entry.mapped_classes
                or entry.mapped_sequences
                or entry.mapped_entities
            )

            if not entry.is_covered:
                overdesign_flags.append(OverDesignFlag(
                    element_type="requirement",
                    element_name=req_id,
                    reason=(
                        f"Requirement '{req_id}' is NOT covered by any Class, "
                        f"Sequence, or Entity in the design."
                    ),
                    educational_feedback=(
                        f"🎓 Every functional requirement should be traceable to "
                        f"at least one design artifact. If '{req_id}' has no "
                        f"corresponding class, sequence flow, or database table, "
                        f"it means this requirement will NOT be implemented. "
                        f"Either add the missing design elements or re-evaluate "
                        f"whether this requirement is still needed."
                    ),
                ))

            traceability_matrix.append(entry)

        # ------------------------------------------
        # 2. Backward traceability: Classes
        #    (Flag classes with no requirement mapping)
        # ------------------------------------------
        for cls in ir.classes:
            if not cls.requirement_ids:
                overdesign_flags.append(OverDesignFlag(
                    element_type="class",
                    element_name=cls.name,
                    reason=(
                        f"Class '{cls.name}' has NO requirement_ids — it cannot "
                        f"be traced back to any original requirement."
                    ),
                    educational_feedback=(
                        f"🎓 This is called 'feature creep' or 'over-engineering'. "
                        f"Every class in your design should exist because a specific "
                        f"requirement demands it. Class '{cls.name}' appears to be "
                        f"an LLM hallucination or an unnecessary addition. Remove it, "
                        f"or map it to a valid requirement."
                    ),
                ))

        # ------------------------------------------
        # 3. Backward traceability: Entities
        #    (Flag DB tables with no requirement mapping)
        # ------------------------------------------
        for entity in ir.entities:
            if not entity.requirement_ids:
                overdesign_flags.append(OverDesignFlag(
                    element_type="entity",
                    element_name=entity.name,
                    reason=(
                        f"Entity '{entity.name}' has NO requirement_ids — "
                        f"this database table cannot be traced to any requirement."
                    ),
                    educational_feedback=(
                        f"🎓 Every database table should store data that a specific "
                        f"requirement needs. Table '{entity.name}' appears to be "
                        f"unrequested. In enterprise projects, unnecessary tables "
                        f"add complexity, maintenance costs, and security surface area."
                    ),
                ))

        # ------------------------------------------
        # 4. Backward traceability: Sequences
        #    (Flag flows with no requirement mapping)
        # ------------------------------------------
        for seq in ir.sequences:
            if not seq.requirement_ids:
                overdesign_flags.append(OverDesignFlag(
                    element_type="sequence",
                    element_name=seq.name,
                    reason=(
                        f"Sequence '{seq.name}' has NO requirement_ids — "
                        f"this interaction flow has no business justification."
                    ),
                    educational_feedback=(
                        f"🎓 Every sequence flow represents a use case or user "
                        f"interaction. If '{seq.name}' doesn't map to any requirement, "
                        f"it means the system is designed to do something nobody asked "
                        f"for. This wastes development time and adds unnecessary complexity."
                    ),
                ))

        # ------------------------------------------
        # 5. Check for unused methods (methods not called in any sequence)
        # ------------------------------------------
        all_called_methods = set()
        for seq in ir.sequences:
            for msg in seq.messages:
                all_called_methods.add((msg.to_participant, msg.method))

        for cls in ir.classes:
            for method in cls.methods:
                if (cls.name, method.name) not in all_called_methods:
                    # Only flag if it's a public method (private methods might be internal)
                    if method.visibility.value == "public":
                        overdesign_flags.append(OverDesignFlag(
                            element_type="method",
                            element_name=f"{cls.name}.{method.name}()",
                            reason=(
                                f"Public method '{method.name}()' in class '{cls.name}' "
                                f"is never called in any Sequence Diagram."
                            ),
                            educational_feedback=(
                                f"🎓 A public method that is never called in any "
                                f"sequence flow might be over-engineered. Either add "
                                f"a sequence that uses this method, or consider if "
                                f"it's truly needed. Unused public methods increase "
                                f"your API surface area unnecessarily."
                            ),
                        ))

        logger.info(
            f"Over-design detection complete: "
            f"{len(traceability_matrix)} requirements traced, "
            f"{len(overdesign_flags)} flags raised"
        )

        return traceability_matrix, overdesign_flags
