import logging
from schemas.ir_schema import IntermediateRepresentation
from schemas.api_models import ValidationError, Severity, ValidationReport

logger = logging.getLogger(__name__)


class ConsistencyEngine:

    def validate(self, ir: IntermediateRepresentation) -> ValidationReport:
        """Run all consistency validation rules and return a report."""
        errors: list[ValidationError] = []
        total_checks = 0
        passed_checks = 0

        # Build lookup indexes for fast access
        class_index = {c.name: c for c in ir.classes}
        class_methods_index = {}
        for c in ir.classes:
            class_methods_index[c.name] = {m.name: m for m in c.methods}

        entity_index = {e.name: e for e in ir.entities}

        # ----------------------------------------------------------
        # CV-001: Every method called in Sequence messages exists
        #         in the corresponding Class definition
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for msg in seq.messages:
                if msg.type.value == "return":
                    continue  # Return messages don't need method validation

                target = msg.to_participant
                if target in class_index:
                    total_checks += 1
                    cls = class_index[target]
                    method_names = [m.name for m in cls.methods]
                    if msg.method not in method_names:
                        errors.append(ValidationError(
                            rule_id="CV-001",
                            severity=Severity.CRITICAL,
                            message=(
                                f"Sequence '{seq.name}' calls method '{msg.method}()' "
                                f"on class '{target}', but this method does NOT exist "
                                f"in the Class definition."
                            ),
                            suggestion=(
                                f"Add method '{msg.method}()' to class '{target}', OR "
                                f"fix the Sequence diagram to use an existing method: "
                                f"{method_names}"
                            ),
                            educational_feedback=(
                                f"🎓 When a Sequence Diagram shows object A calling "
                                f"method X on object B, that method MUST be declared in "
                                f"B's Class Diagram. This is called 'behavioral-structural "
                                f"consistency' — the behavior shown in Sequences must be "
                                f"supported by the structure in Classes."
                            )
                        ))
                    else:
                        passed_checks += 1

        # ----------------------------------------------------------
        # CV-002: Every participant in Sequence diagrams has a
        #         matching Class definition
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for participant in seq.participants:
                total_checks += 1
                if participant not in class_index:
                    errors.append(ValidationError(
                        rule_id="CV-002",
                        severity=Severity.CRITICAL,
                        message=(
                            f"Sequence '{seq.name}' uses participant '{participant}', "
                            f"but no Class with this name is defined."
                        ),
                        suggestion=(
                            f"Create a Class definition for '{participant}', OR "
                            f"fix the participant name to match an existing class."
                        ),
                        educational_feedback=(
                            f"🎓 Every object (participant) that appears in a Sequence "
                            f"Diagram must have a corresponding Class in the Class Diagram. "
                            f"Without it, the system doesn't know what '{participant}' is "
                            f"or what methods it can handle."
                        )
                    ))
                else:
                    passed_checks += 1

        # ----------------------------------------------------------
        # CV-003: Every Class with data attributes has a
        #         corresponding ER entity (for data-holding classes)
        # ----------------------------------------------------------
        entity_names_lower = {e.name.lower().replace("_", "") for e in ir.entities}
        for cls in ir.classes:
            if cls.stereotype in ("entity", "") and cls.attributes:
                total_checks += 1
                cls_name_lower = cls.name.lower().replace("_", "")
                # Check both exact and pluralized matches
                has_entity = (
                    cls_name_lower in entity_names_lower
                    or cls_name_lower + "s" in entity_names_lower
                    or cls_name_lower.rstrip("s") in entity_names_lower
                )
                if not has_entity:
                    errors.append(ValidationError(
                        rule_id="CV-003",
                        severity=Severity.HIGH,
                        message=(
                            f"Class '{cls.name}' has data attributes but no "
                            f"corresponding ER entity/table exists."
                        ),
                        suggestion=(
                            f"Create an ER entity (database table) that maps "
                            f"to class '{cls.name}' with appropriate columns "
                            f"for its attributes."
                        ),
                        educational_feedback=(
                            f"🎓 If a class holds persistent data (attributes that "
                            f"need to be stored), it typically needs a corresponding "
                            f"database table in the ER Diagram. This ensures your "
                            f"application data has a storage location."
                        )
                    ))
                else:
                    passed_checks += 1

        # ----------------------------------------------------------
        # CV-004: FK relationships in ER match associations in Class
        # ----------------------------------------------------------
        for entity in ir.entities:
            for attr in entity.attributes:
                if attr.constraint.startswith("FK"):
                    total_checks += 1
                    # Extract referenced table from "FK -> table.column"
                    try:
                        ref_table = attr.constraint.split("->")[1].strip().split(".")[0]
                        if ref_table not in entity_index:
                            errors.append(ValidationError(
                                rule_id="CV-004",
                                severity=Severity.HIGH,
                                message=(
                                    f"Entity '{entity.name}' has FK referencing "
                                    f"'{ref_table}', but no entity with this name exists."
                                ),
                                suggestion=(
                                    f"Create entity '{ref_table}', OR fix the FK "
                                    f"reference in '{entity.name}.{attr.name}'."
                                ),
                                educational_feedback=(
                                    f"🎓 A Foreign Key (FK) creates a relationship between "
                                    f"two tables. The referenced table MUST exist in the "
                                    f"ER diagram. If '{ref_table}' doesn't exist, the "
                                    f"database cannot enforce referential integrity."
                                )
                            ))
                        else:
                            passed_checks += 1
                    except (IndexError, ValueError):
                        pass

        # ----------------------------------------------------------
        # CV-005: Method parameters in Sequence match method
        #         signatures in Class
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for msg in seq.messages:
                if msg.type.value == "return":
                    continue
                target = msg.to_participant
                if target in class_methods_index and msg.method in class_methods_index[target]:
                    total_checks += 1
                    cls_method = class_methods_index[target][msg.method]
                    cls_param_count = len(cls_method.parameters)
                    seq_arg_count = len(msg.arguments)
                    if seq_arg_count > 0 and cls_param_count > 0 and seq_arg_count != cls_param_count:
                        errors.append(ValidationError(
                            rule_id="CV-005",
                            severity=Severity.MEDIUM,
                            message=(
                                f"Sequence '{seq.name}': method '{msg.method}()' on "
                                f"'{target}' is called with {seq_arg_count} arguments, "
                                f"but the Class defines {cls_param_count} parameters."
                            ),
                            suggestion=(
                                f"Align the parameter count. Class '{target}.{msg.method}' "
                                f"expects: {[p.name for p in cls_method.parameters]}"
                            ),
                            educational_feedback=(
                                f"🎓 When a Sequence Diagram shows a method call with "
                                f"specific arguments, those arguments should match the "
                                f"method's parameter list in the Class Diagram. Mismatched "
                                f"parameters mean the method call would fail at runtime."
                            )
                        ))
                    else:
                        passed_checks += 1

        # ----------------------------------------------------------
        # CV-006: ER entities referenced in sequence exist
        # ----------------------------------------------------------
        repository_classes = [c for c in ir.classes if c.stereotype == "repository"]
        for repo in repository_classes:
            total_checks += 1
            # Repository name pattern: XxxRepository -> entity should be xxx or xxxs
            base_name = repo.name.replace("Repository", "").lower()
            has_entity = any(
                e.name.lower() in (base_name, base_name + "s", base_name + "es")
                for e in ir.entities
            )
            if not has_entity:
                errors.append(ValidationError(
                    rule_id="CV-006",
                    severity=Severity.HIGH,
                    message=(
                        f"Repository class '{repo.name}' exists but no corresponding "
                        f"database entity/table was found."
                    ),
                    suggestion=(
                        f"Create an ER entity for '{base_name}s' (pluralized snake_case) "
                        f"that '{repo.name}' manages."
                    ),
                    educational_feedback=(
                        f"🎓 Repository classes are the data access layer — they read "
                        f"and write to database tables. Every Repository MUST have a "
                        f"corresponding table in the ER diagram. Without it, the "
                        f"Repository has no data source to operate on."
                    )
                ))
            else:
                passed_checks += 1

        # ----------------------------------------------------------
        # CV-007: Every ER entity has a Primary Key
        # ----------------------------------------------------------
        for entity in ir.entities:
            total_checks += 1
            has_pk = any(attr.constraint == "PK" for attr in entity.attributes)
            if not has_pk:
                errors.append(ValidationError(
                    rule_id="CV-007",
                    severity=Severity.CRITICAL,
                    message=(
                        f"Entity '{entity.name}' has NO Primary Key defined."
                    ),
                    suggestion=(
                        f"Add a Primary Key column (e.g., '{entity.name.rstrip('s')}_id') "
                        f"with constraint 'PK' to entity '{entity.name}'."
                    ),
                    educational_feedback=(
                        f"🎓 Every database table MUST have a Primary Key (PK). "
                        f"The PK uniquely identifies each record in the table. "
                        f"Without it, you cannot reliably reference or update "
                        f"specific rows."
                    )
                ))
            else:
                passed_checks += 1

        # ----------------------------------------------------------
        # CV-008: Actors in Sequences are not defined as Classes
        #         (actors are external — they shouldn't be classes)
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for actor in seq.actors:
                total_checks += 1
                if actor in class_index:
                    errors.append(ValidationError(
                        rule_id="CV-008",
                        severity=Severity.LOW,
                        message=(
                            f"'{actor}' is defined as both an Actor in Sequence "
                            f"'{seq.name}' and as a Class. Actors are external "
                            f"entities and should not be system classes."
                        ),
                        suggestion=(
                            f"Remove the Class definition for '{actor}' if it's "
                            f"external, OR remove it from the actors list if it's "
                            f"an internal system component."
                        ),
                        educational_feedback=(
                            f"🎓 In UML, an Actor represents an external entity "
                            f"(user, external system) that interacts with your system. "
                            f"Actors should NOT have Class definitions because they "
                            f"are outside the system boundary."
                        )
                    ))
                else:
                    passed_checks += 1

        # ----------------------------------------------------------
        # Calculate consistency score
        # ----------------------------------------------------------
        consistency_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        critical_errors = [e for e in errors if e.severity == Severity.CRITICAL]

        report = ValidationReport(
            passed=len(critical_errors) == 0,
            consistency_score=round(consistency_score, 2),
            total_checks=total_checks,
            passed_checks=passed_checks,
            errors=errors,
        )

        logger.info(
            f"Consistency validation: {passed_checks}/{total_checks} checks passed "
            f"({consistency_score:.1f}%), {len(errors)} errors found"
        )

        return report
