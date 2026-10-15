import logging
import re
from schemas.ir_schema import IntermediateRepresentation, MessageType, ParticipantType
from schemas.api_models import ValidationError, Severity, ValidationReport
from validators.stage_validators import _types_are_compatible, _is_lifecycle_container

logger = logging.getLogger(__name__)


def _collect_all_ir_messages(seq) -> list:
    """Recursively collect all messages from sequence items, logic blocks, and messages."""
    messages = []
    seen = set()

    def _walk(item):
        if item is None:
            return
        if hasattr(item, "items") or hasattr(item, "logic_blocks"):
            for child in getattr(item, "items", []) or []:
                _walk(child)
            for child_msg in getattr(item, "messages", []) or []:
                _walk(child_msg)
            for child_block in getattr(item, "logic_blocks", []) or []:
                _walk(child_block)
        elif hasattr(item, "to_participant") or hasattr(item, "method"):
            item_id = id(item)
            if item_id not in seen:
                seen.add(item_id)
                messages.append(item)

    if getattr(seq, "items", None):
        for item in seq.items:
            _walk(item)
    else:
        for msg in getattr(seq, "messages", []) or []:
            _walk(msg)
        for blk in getattr(seq, "logic_blocks", []) or []:
            _walk(blk)

    for msg in getattr(seq, "messages", []) or []:
        item_id = id(msg)
        if item_id not in seen:
            seen.add(item_id)
            messages.append(msg)

    return messages


def _is_return_message(msg) -> bool:
    """Check if message is a return/reply message and should not be validated as a method call."""
    msg_type = getattr(msg, "type", None)
    if hasattr(msg_type, "value"):
        msg_type = msg_type.value
    msg_type_str = str(msg_type or "").strip().lower()
    if msg_type_str in ("return", "reply", "response"):
        return True
    if getattr(msg, "arrow", "") == "-->":
        return True
    method_str = str(getattr(msg, "method", "")).strip().lower()
    if method_str.startswith("return") or method_str.startswith("response"):
        return True
    if method_str in ("result", "response", "ack", "token", "ok", "error", "data"):
        return True
    return bool(re.search(r"\b(result|response|acknowledgement|ack)\b", method_str))


def _is_architectural_component(name: str) -> bool:
    """Classify if an entity represents an application architectural component.
    Entities named 'Service' or 'Component' alone can be valid domain entities (e.g., service catalog, IT service).
    Compound names like 'OrderService', 'UserController', 'OrderRepository' are architectural components."""
    name_clean = str(name).strip()
    name_lower = name_clean.lower()
    if name_lower in ("service", "component"):
        return False
    arch_suffixes = ("controller", "service", "repository", "handler", "gateway", "interceptor", "adapter", "router", "frontend", "ui")
    for sfx in arch_suffixes:
        if name_lower.endswith(sfx) and len(name_lower) > len(sfx):
            return True
    return False


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
        entity_names_lower = {e.name.lower().replace("_", "") for e in ir.entities}

        # ----------------------------------------------------------
        # CV-001: Every method called in Sequence messages exists
        #         in the corresponding Class definition
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for msg in _collect_all_ir_messages(seq):
                if _is_return_message(msg):
                    continue  # Return messages don't need receiving-class method validation

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
        #         matching Class definition (external actors, boundaries,
        #         architectural participants & external systems excluded)
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for participant in seq.participants:
                total_checks += 1
                if participant not in class_index:
                    pt = seq.participant_types.get(participant, "")
                    if hasattr(pt, "value"):
                        pt = pt.value
                    pt_str = str(pt or "").strip().lower()

                    is_external_or_arch = (
                        participant in seq.actors
                        or pt_str in (
                            "actor", "boundary", "control", "controller", "service",
                            "repository", "database", "external_system", "system",
                            "client", "user", "external", "participant"
                        )
                        or any(
                            participant.lower().startswith(prefix) or participant.lower().endswith(suffix)
                            for prefix in ("actor", "user", "client", "external", "db", "ext_")
                            for suffix in ("actor", "user", "client", "external", "system", "db", "database", "gateway", "boundary", "controller", "service", "repository")
                        )
                    )
                    if is_external_or_arch:
                        passed_checks += 1
                        continue

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
        #         corresponding ER entity (for data-holding classes,
        #         avoiding false positives for value objects)
        # ----------------------------------------------------------
        value_object_stereotypes = {"value_object", "vo", "dto", "embeddable", "datatype", "enum", "utility", "viewmodel"}
        common_value_objects = {"address", "money", "coordinates", "location", "dimensions", "daterange", "timeslot", "email", "phone", "fullname", "price", "quantity"}

        for cls in ir.classes:
            cls_stereo = (cls.stereotype or "").strip().lower()
            if cls_stereo in value_object_stereotypes:
                continue

            cls_name_lower = cls.name.lower().replace("_", "")
            if cls_name_lower in common_value_objects or cls_name_lower.endswith("vo") or cls_name_lower.endswith("dto") or cls_name_lower.endswith("value"):
                continue

            has_id_attr = any(
                a.lower() in ("id", "uuid", "code") or a.lower().endswith("_id") or a.lower().endswith("id")
                for a in cls.attributes
            )
            # If not stereotyped as an entity and has no identity attribute, treat as value object
            if cls_stereo != "entity" and not has_id_attr:
                continue

            if cls.stereotype in ("entity", "") and cls.attributes:
                total_checks += 1
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
        #         signatures in Class (avoiding false positives for missing args)
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for msg in _collect_all_ir_messages(seq):
                if _is_return_message(msg):
                    continue
                target = msg.to_participant
                if target in class_methods_index and msg.method in class_methods_index[target]:
                    total_checks += 1
                    cls_method = class_methods_index[target][msg.method]
                    cls_param_count = len(cls_method.parameters)
                    seq_arg_count = len(msg.arguments)
                    # Only flag if arguments exceed parameters or argument mismatch when calling 0-arg method
                    if seq_arg_count > 0 and cls_param_count == 0:
                        errors.append(ValidationError(
                            rule_id="CV-005",
                            severity=Severity.MEDIUM,
                            message=(
                                f"Sequence '{seq.name}': method '{msg.method}()' on "
                                f"'{target}' is called with {seq_arg_count} arguments, "
                                f"but the Class defines 0 parameters."
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
                    elif seq_arg_count > 0 and cls_param_count > 0 and seq_arg_count > cls_param_count:
                        errors.append(ValidationError(
                            rule_id="CV-005",
                            severity=Severity.MEDIUM,
                            message=(
                                f"Sequence '{seq.name}': method '{msg.method}()' on "
                                f"'{target}' is called with {seq_arg_count} arguments, "
                                f"exceeding the {cls_param_count} parameters defined by the Class."
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
                        type_mismatch_found = False
                        for arg_idx, arg_item in enumerate(msg.arguments):
                            if arg_idx < cls_param_count:
                                param = cls_method.parameters[arg_idx]
                                param_type = param.data_type
                                arg_str = str(arg_item).strip()
                                arg_type = ""
                                if ":" in arg_str:
                                    arg_type = arg_str.split(":", 1)[1].strip()
                                elif hasattr(arg_item, "data_type"):
                                    arg_type = getattr(arg_item, "data_type", "")
                                if arg_type and param_type and not _types_are_compatible(param_type, arg_type):
                                    type_mismatch_found = True
                                    errors.append(ValidationError(
                                        rule_id="CV-005",
                                        severity=Severity.HIGH,
                                        message=(
                                            f"Sequence '{seq.name}': method '{msg.method}()' on '{target}' "
                                            f"called with argument of type '{arg_type}', but parameter '{param.name}' expects '{param_type}'."
                                        ),
                                        suggestion=(
                                            f"Pass an argument matching type '{param_type}' or update '{target}.{msg.method}' parameter type."
                                        ),
                                        educational_feedback=(
                                            f"🎓 When a Sequence Diagram shows a method call, the data types of arguments must match "
                                            f"the parameter types in the Class Diagram. Incompatible types cause runtime failures."
                                        )
                                    ))
                        if not type_mismatch_found:
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
        #         (actors are external, but allow valid domain representations)
        # ----------------------------------------------------------
        for seq in ir.sequences:
            for actor in seq.actors:
                total_checks += 1
                if actor in class_index:
                    cls = class_index[actor]
                    actor_name_lower = actor.lower().replace("_", "")
                    has_domain_entity = (
                        bool(cls.attributes)
                        or cls.stereotype in ("entity", "domain", "")
                        or actor_name_lower in entity_names_lower
                        or actor_name_lower + "s" in entity_names_lower
                        or actor_name_lower.rstrip("s") in entity_names_lower
                    )
                    if has_domain_entity:
                        # Valid domain entity representation for the actor
                        passed_checks += 1
                        continue

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
        # CV-009: Architectural components not converted to ER entities
        # ----------------------------------------------------------
        for entity in ir.entities:
            total_checks += 1
            if _is_architectural_component(entity.name):
                errors.append(ValidationError(
                    rule_id="CV-009",
                    severity=Severity.HIGH,
                    message=(
                        f"Architectural component '{entity.name}' must not be "
                        f"converted into an ER persistent entity."
                    ),
                    suggestion=(
                        f"Remove '{entity.name}' from the ER diagram as it represents "
                        f"application architecture, not persistent domain data."
                    ),
                    educational_feedback=(
                        f"🎓 ER diagrams model database tables and persistent state. "
                        f"Architectural components like controllers, services, and "
                        f"repositories belong in Class or Sequence diagrams, not as tables."
                    )
                ))
            else:
                passed_checks += 1

        # ----------------------------------------------------------
        # CV-010: Lifeline activation balance in Sequence diagrams
        # ----------------------------------------------------------
        for seq in ir.sequences:
            activation_depth = {p: 0 for p in seq.participants}
            ordered_msgs = _collect_all_ir_messages(seq)
            for msg in ordered_msgs:
                sender = getattr(msg, "from_participant", "")
                target = getattr(msg, "to_participant", "")
                activates = getattr(msg, "activates_target", False)
                deactivates = getattr(msg, "deactivates_target", False)
                is_return = _is_return_message(msg)

                if not is_return:
                    if activates and not deactivates:
                        activation_depth[target] = activation_depth.get(target, 0) + 1
                    elif deactivates and not activates:
                        cur_depth = activation_depth.get(target, 0)
                        if cur_depth <= 0:
                            total_checks += 1
                            errors.append(ValidationError(
                                rule_id="CV-010",
                                severity=Severity.HIGH,
                                message=(
                                    f"Sequence '{seq.name}': Participant '{target}' is deactivated "
                                    f"while not active."
                                ),
                                suggestion=f"Ensure '{target}' is activated before deactivating it.",
                                educational_feedback=(
                                    f"🎓 In UML Sequence Diagrams, a lifeline execution bar can only be "
                                    f"deactivated if it was previously activated."
                                )
                            ))
                        else:
                            activation_depth[target] = cur_depth - 1
                else:
                    cur_depth = activation_depth.get(sender, 0)
                    if cur_depth > 0:
                        activation_depth[sender] = cur_depth - 1
                    elif deactivates:
                        total_checks += 1
                        errors.append(ValidationError(
                            rule_id="CV-010",
                            severity=Severity.HIGH,
                            message=(
                                f"Sequence '{seq.name}': Participant '{sender}' is deactivated on return "
                                f"while not active."
                            ),
                            suggestion=f"Ensure '{sender}' is active before deactivating on return.",
                            educational_feedback=(
                                f"🎓 Deactivation on return requires the participant to have an active lifeline."
                            )
                        ))

            for p, d in activation_depth.items():
                total_checks += 1
                if d > 0:
                    errors.append(ValidationError(
                        rule_id="CV-010",
                        severity=Severity.HIGH,
                        message=(
                            f"Sequence '{seq.name}': Participant '{p}' has {d} unbalanced activation(s) "
                            f"without matching completion/deactivation."
                        ),
                        suggestion=f"Add matching deactivation(s) or return messages for participant '{p}'.",
                        educational_feedback=(
                            f"🎓 Every activation bar in a Sequence Diagram must be closed with a corresponding "
                            f"deactivation or return message. Leaving lifelines active represents unfinished execution."
                        )
                    ))
                else:
                    passed_checks += 1

        # ----------------------------------------------------------
        # CV-011: Redundant ER attributes duplicating relationships
        # ----------------------------------------------------------
        entity_rel_targets = {}
        for entity in ir.entities:
            for rel in getattr(entity, "relationships", []):
                t = getattr(rel, "target", "")
                if t:
                    entity_rel_targets.setdefault(entity.name, set()).add(t)
                    entity_rel_targets.setdefault(t, set()).add(entity.name)

        for entity in ir.entities:
            targets = entity_rel_targets.get(entity.name, set())
            for attr in entity.attributes:
                total_checks += 1
                attr_norm = attr.name.lower().replace("_", "")
                is_redundant = False
                matched_target = ""
                for t in targets:
                    t_norm = t.lower().replace("_", "")
                    if attr_norm in (t_norm, t_norm + "s", t_norm + "es", t_norm + "list", "list" + t_norm):
                        is_redundant = True
                        matched_target = t
                        break
                if is_redundant:
                    errors.append(ValidationError(
                        rule_id="CV-011",
                        severity=Severity.HIGH,
                        message=(
                            f"Entity '{entity.name}' has redundant attribute '{attr.name}' "
                            f"which duplicates an ER relationship to entity '{matched_target}'."
                        ),
                        suggestion=(
                            f"Remove attribute '{attr.name}' from entity '{entity.name}' "
                            f"since the relationship to '{matched_target}' is already modeled."
                        ),
                        educational_feedback=(
                            f"🎓 In relational database modeling, relationships between tables "
                            f"are represented through foreign keys or junction tables. Embedding "
                            f"collection attributes (e.g., 'speakers', 'requirements') in an entity "
                            f"when an explicit relationship already exists creates redundant and invalid ER models."
                        )
                    ))
                else:
                    passed_checks += 1

        # ----------------------------------------------------------
        # CV-012: Lifecycle multiplicity consistency
        # ----------------------------------------------------------
        for cls in ir.classes:
            cls_dict = {"attributes": cls.attributes, "methods": [m.name for m in cls.methods]}
            if _is_lifecycle_container(cls.name, cls_dict):
                for rel in getattr(cls, "relationships", []):
                    target_mult = getattr(rel, "target_multiplicity", getattr(rel, "cardinality", ""))
                    if target_mult in ("1..*", "1"):
                        total_checks += 1
                        errors.append(ValidationError(
                            rule_id="CV-012",
                            severity=Severity.MEDIUM,
                            message=(
                                f"Relationship from lifecycle class '{cls.name}' to '{rel.target}' "
                                f"specifies target multiplicity '{target_mult}', but '{cls.name}' "
                                f"may exist before '{rel.target}' is identified/created."
                            ),
                            suggestion=(
                                f"Change target multiplicity to '0..*' to allow the lifecycle container "
                                f"to exist before child items are populated."
                            ),
                            educational_feedback=(
                                f"🎓 In system lifecycles, session or workflow entities are created first "
                                f"before extracted items or speakers are identified. Mandatory '1..*' "
                                f"multiplicities violate this lifecycle constraint."
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
