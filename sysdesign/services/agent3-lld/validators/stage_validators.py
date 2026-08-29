from __future__ import annotations

import re

EXTERNAL_PARTICIPANT_TYPES = {
    "actor",
    "boundary",
    "database",
    "external",
}


CLASS_RELATIONSHIP_TYPES = {
    "association",
    "aggregation",
    "composition",
    "inheritance",
    "dependency",
}

CLASS_CARDINALITY_VALUES = {
    "1",
    "0..1",
    "1..*",
    "0..*",
}

ER_RELATIONSHIP_TYPES = {
    "one-to-one",
    "one-to-many",
    "many-to-one",
    "many-to-many",
}

ER_MULTIPLICITY_VALUES = {
    "1",
    "0..1",
    "0..*",
    "1..*",
}

ER_CARDINALITY_LABELS = {
    "one-to-one",
    "one-to-many",
    "many-to-one",
    "many-to-many",
    "1:1",
    "1:n",
    "n:1",
    "n:m",
    "many",
}

ITERATION_CONDITION_RE = re.compile(
    r"\b(for each|for every|each item|every item|repeat|iterate|iteration|per item)\b",
    re.IGNORECASE,
)

SUCCESS_MESSAGE_RE = re.compile(
    r"\b(success|successresponse|response|confirmation|confirmed)\b",
    re.IGNORECASE,
)


def _result(
    errors: list[dict],
    warnings: list[dict],
    total_checks: int,
    stage: str,
) -> dict:
    passed = len(errors) == 0
    return {
        "passed": passed,
        "valid": passed,
        "stage": stage,
        "errors": errors,
        "warnings": warnings,
        "total_checks": total_checks,
        "passed_checks": max(total_checks - len(errors), 0),
    }


def _error(
    rule_id: str,
    message: str,
    severity: str = "high",
    *,
    code: str | None = None,
    path: str = "",
    details: dict | None = None,
) -> dict:
    return {
        "rule_id": rule_id,
        "code": code or rule_id,
        "severity": severity,
        "path": path,
        "message": message,
        "details": details or {},
    }


def _warning(
    rule_id: str,
    message: str,
    *,
    code: str | None = None,
    path: str = "",
    details: dict | None = None,
) -> dict:
    return {
        "rule_id": rule_id,
        "code": code or rule_id,
        "severity": "warning",
        "path": path,
        "message": message,
        "details": details or {},
    }


def _parse_method_name(message: str) -> str:
    text = str(message or "").strip()
    match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", text)
    if match:
        return match.group(1)
    return text.split()[0] if text else ""


def validate_class_diagram(class_diagram: dict | None) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    diagram = class_diagram or {}
    classes = diagram.get("classes", []) or []
    relationships = diagram.get("relationships", []) or []

    if not isinstance(classes, list):
        errors.append(_error(
            "CLASS-STRUCTURE",
            "class_diagram.classes must be a list.",
            "critical",
            code="INVALID_CLASS_COLLECTION",
            path="classes",
        ))
        return _result(errors, warnings, 1, "class")

    class_names = set()
    for index, cls in enumerate(classes):
        total_checks += 1
        if not isinstance(cls, dict):
            errors.append(_error(
                "CLASS-STRUCTURE",
                f"Class at index {index} must be an object.",
                code="INVALID_CLASS_OBJECT",
                path=f"classes[{index}]",
            ))
            continue

        name = str(cls.get("name", "")).strip()
        if not name:
            errors.append(_error(
                "CLASS-NAME",
                f"Class at index {index} has no name.",
                code="MISSING_CLASS_NAME",
                path=f"classes[{index}].name",
            ))
            continue

        class_names.add(name)
        attributes = cls.get("attributes", []) or []
        methods = cls.get("methods", []) or []
        if not attributes and not methods:
            errors.append(_error(
                "CLASS-EMPTY",
                f"Class '{name}' has no attributes or methods.",
                code="EMPTY_CLASS",
                path=f"classes[{index}]",
                details={"class": name},
            ))

    connected = set()
    for index, rel in enumerate(relationships):
        total_checks += 1
        if not isinstance(rel, dict):
            errors.append(_error(
                "CLASS-RELATIONSHIP",
                f"Relationship at index {index} must be an object.",
                code="INVALID_CLASS_RELATIONSHIP_OBJECT",
                path=f"relationships[{index}]",
            ))
            continue

        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        rel_type = str(rel.get("type", "association")).strip()
        cardinality = str(rel.get("cardinality", "")).strip()
        if source not in class_names:
            errors.append(_error(
                "CLASS-REL-SOURCE",
                f"Relationship source '{source}' is not a defined class.",
                code="UNKNOWN_CLASS_RELATIONSHIP_SOURCE",
                path=f"relationships[{index}].source",
                details={"source": source},
            ))
        if target not in class_names:
            errors.append(_error(
                "CLASS-REL-TARGET",
                f"Relationship target '{target}' is not a defined class.",
                code="UNKNOWN_CLASS_RELATIONSHIP_TARGET",
                path=f"relationships[{index}].target",
                details={"target": target},
            ))
        if rel_type not in CLASS_RELATIONSHIP_TYPES:
            errors.append(_error(
                "CLASS-REL-TYPE",
                f"Relationship type '{rel_type}' is not supported.",
                code="UNSUPPORTED_CLASS_RELATIONSHIP_TYPE",
                path=f"relationships[{index}].type",
                details={"type": rel_type},
            ))
        if cardinality and cardinality not in CLASS_CARDINALITY_VALUES:
            errors.append(_error(
                "CLASS-REL-CARDINALITY",
                f"Relationship cardinality '{cardinality}' is not supported.",
                code="UNSUPPORTED_CLASS_CARDINALITY",
                path=f"relationships[{index}].cardinality",
                details={"cardinality": cardinality},
            ))
        if rel_type == "dependency" and cardinality:
            errors.append(_error(
                "CLASS-DEPENDENCY-CARDINALITY",
                "Dependency relationships must not define structural cardinality.",
                code="DEPENDENCY_CARDINALITY_NOT_ALLOWED",
                path=f"relationships[{index}].cardinality",
                details={"source": source, "target": target, "cardinality": cardinality},
            ))
        if rel_type == "inheritance" and cardinality:
            errors.append(_error(
                "CLASS-INHERITANCE-CARDINALITY",
                "Inheritance relationships must not define structural cardinality.",
                code="INHERITANCE_CARDINALITY_NOT_ALLOWED",
                path=f"relationships[{index}].cardinality",
                details={"source": source, "target": target, "cardinality": cardinality},
            ))
        if source in class_names:
            connected.add(source)
        if target in class_names:
            connected.add(target)

    if len(class_names) > 1:
        for name in sorted(class_names - connected):
            warnings.append(_warning(
                "CLASS-ISOLATED",
                f"Class '{name}' is isolated.",
                code="ISOLATED_CLASS",
                details={"class": name},
            ))

    return _result(errors, warnings, total_checks, "class")


def validate_er_diagram(er_diagram: dict | None, class_diagram: dict | None) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    diagram = er_diagram or {}
    entities = diagram.get("entities", []) or []
    relationships = diagram.get("relationships", []) or []

    if not isinstance(entities, list):
        errors.append(_error(
            "ER-STRUCTURE",
            "er_diagram.entities must be a list.",
            "critical",
            code="INVALID_ENTITY_COLLECTION",
            path="entities",
        ))
        return _result(errors, warnings, 1, "er")

    entity_names = set()
    for index, entity in enumerate(entities):
        total_checks += 1
        if not isinstance(entity, dict):
            errors.append(_error(
                "ER-ENTITY",
                f"Entity at index {index} must be an object.",
                code="INVALID_ENTITY_OBJECT",
                path=f"entities[{index}]",
            ))
            continue

        name = str(entity.get("name", "")).strip()
        if not name:
            errors.append(_error(
                "ER-ENTITY-NAME",
                f"Entity at index {index} has no name.",
                code="MISSING_ENTITY_NAME",
                path=f"entities[{index}].name",
            ))
            continue

        entity_names.add(name)
        attributes = entity.get("attributes", []) or []
        primary_key = str(entity.get("primary_key", "")).strip()
        if not primary_key:
            errors.append(_error(
                "ER-PRIMARY-KEY",
                f"Entity '{name}' has no primary key.",
                "critical",
                code="MISSING_PRIMARY_KEY",
                path=f"entities[{index}].primary_key",
                details={"entity": name},
            ))
        if not attributes:
            errors.append(_error(
                "ER-ATTRIBUTES",
                f"Entity '{name}' has no attributes.",
                code="MISSING_ENTITY_ATTRIBUTES",
                path=f"entities[{index}].attributes",
                details={"entity": name},
            ))
        elif primary_key and primary_key not in [str(attr).strip() for attr in attributes]:
            errors.append(_error(
                "ER-PRIMARY-KEY-ATTRIBUTE",
                f"Entity '{name}' primary key '{primary_key}' is not present in attributes.",
                "critical",
                code="PRIMARY_KEY_ATTRIBUTE_MISSING",
                path=f"entities[{index}].primary_key",
                details={"entity": name, "primary_key": primary_key, "attributes": attributes},
            ))

    for index, rel in enumerate(relationships):
        total_checks += 1
        if not isinstance(rel, dict):
            errors.append(_error(
                "ER-RELATIONSHIP",
                f"ER relationship at index {index} must be an object.",
                code="INVALID_ER_RELATIONSHIP_OBJECT",
                path=f"relationships[{index}]",
            ))
            continue

        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        rel_name = str(rel.get("name", "")).strip()
        rel_type = str(rel.get("type", "one-to-many")).strip()
        source_multiplicity = str(rel.get("source_multiplicity", "")).strip()
        target_multiplicity = str(rel.get("target_multiplicity", "")).strip()
        evidence = str(rel.get("evidence", "")).strip().lower()
        if source not in entity_names:
            errors.append(_error(
                "ER-REL-SOURCE",
                f"ER relationship source '{source}' is not a defined entity.",
                code="UNKNOWN_ER_RELATIONSHIP_SOURCE",
                path=f"relationships[{index}].source",
                details={"source": source},
            ))
        if target not in entity_names:
            errors.append(_error(
                "ER-REL-TARGET",
                f"ER relationship target '{target}' is not a defined entity.",
                code="UNKNOWN_ER_RELATIONSHIP_TARGET",
                path=f"relationships[{index}].target",
                details={"target": target},
            ))
        if rel_type not in ER_RELATIONSHIP_TYPES:
            errors.append(_error(
                "ER-REL-TYPE",
                f"ER relationship type '{rel_type}' is not supported.",
                code="UNSUPPORTED_ER_RELATIONSHIP_TYPE",
                path=f"relationships[{index}].type",
                details={"type": rel_type},
            ))
        normalized_name = rel_name.lower().replace(" ", "-")
        if not rel_name:
            errors.append(_error(
                "ER-REL-NAME",
                f"ER relationship from '{source}' to '{target}' must define a semantic name.",
                code="MISSING_ER_RELATIONSHIP_NAME",
                path=f"relationships[{index}].name",
                details={"source": source, "target": target},
            ))
        elif normalized_name in ER_CARDINALITY_LABELS or rel_name.lower() == rel_type.lower():
            errors.append(_error(
                "ER-REL-NAME",
                f"ER relationship name '{rel_name}' is a cardinality label, not semantic domain meaning.",
                code="CARDINALITY_LABEL_USED_AS_RELATIONSHIP_NAME",
                path=f"relationships[{index}].name",
                details={"name": rel_name, "type": rel_type},
            ))
        for field_name, multiplicity in [
            ("source_multiplicity", source_multiplicity),
            ("target_multiplicity", target_multiplicity),
        ]:
            if not multiplicity:
                errors.append(_error(
                    "ER-REL-MULTIPLICITY",
                    f"ER relationship {field_name} is required.",
                    code="MISSING_ER_MULTIPLICITY",
                    path=f"relationships[{index}].{field_name}",
                    details={"source": source, "target": target},
                ))
            elif multiplicity not in ER_MULTIPLICITY_VALUES:
                errors.append(_error(
                    "ER-REL-MULTIPLICITY",
                    f"ER relationship {field_name} '{multiplicity}' is not supported.",
                    code="UNSUPPORTED_ER_MULTIPLICITY",
                    path=f"relationships[{index}].{field_name}",
                    details={"multiplicity": multiplicity},
                ))
        if any(token in evidence for token in ["one or more", "at least one"]) and target_multiplicity == "0..*":
            errors.append(_error(
                "ER-REL-MULTIPLICITY",
                "Explicit one-or-more relationship evidence must not be modeled with a zero lower bound.",
                code="ONE_OR_MORE_MODELED_AS_ZERO_OR_MORE",
                path=f"relationships[{index}].target_multiplicity",
                details={"source": source, "target": target, "evidence": rel.get("evidence", "")},
            ))

    class_names = {
        str(cls.get("name", "")).strip().lower().replace("_", "")
        for cls in (class_diagram or {}).get("classes", []) or []
        if isinstance(cls, dict) and cls.get("attributes")
    }
    entity_names_normalized = {name.lower().replace("_", "") for name in entity_names}
    for class_name in sorted(class_names):
        if class_name and class_name not in entity_names_normalized and class_name + "s" not in entity_names_normalized:
            warnings.append(_warning(
                "ER-CLASS-MAPPING",
                f"Persistent class concept '{class_name}' has no obvious ER entity.",
                code="PERSISTENT_CLASS_WITHOUT_ENTITY",
                details={"class": class_name},
            ))

    return _result(errors, warnings, total_checks, "er")


def _is_external_participant(participant: str, participant_types: dict) -> bool:
    participant_type = participant_types.get(participant, "")
    if hasattr(participant_type, "value"):
        participant_type = participant_type.value
    return str(participant_type).strip().lower() in EXTERNAL_PARTICIPANT_TYPES


def _iter_sequence_messages(sequence: dict):
    for msg_index, message in enumerate(sequence.get("messages", []) or []):
        yield f"messages[{msg_index}]", message
    for block_index, block in enumerate(sequence.get("logic_blocks", []) or []):
        yield from _iter_logic_block_messages(block, f"logic_blocks[{block_index}]")


def _iter_logic_block_messages(block, path: str):
    if not isinstance(block, dict):
        return
    for msg_index, message in enumerate(block.get("messages", []) or []):
        yield f"{path}.messages[{msg_index}]", message
    for block_index, nested_block in enumerate(block.get("logic_blocks", []) or []):
        yield from _iter_logic_block_messages(nested_block, f"{path}.logic_blocks[{block_index}]")


def _iter_logic_blocks(sequence: dict):
    for block_index, block in enumerate(sequence.get("logic_blocks", []) or []):
        yield from _iter_logic_block_tree(block, f"logic_blocks[{block_index}]")


def _iter_logic_block_tree(block, path: str):
    if not isinstance(block, dict):
        return
    yield path, block
    for block_index, nested_block in enumerate(block.get("logic_blocks", []) or []):
        yield from _iter_logic_block_tree(nested_block, f"{path}.logic_blocks[{block_index}]")


def _flatten_sequence_message_order(sequence: dict) -> list[tuple[str, dict]]:
    ordered = []
    delayed_success = []
    has_logic_blocks = bool(sequence.get("logic_blocks", []) or [])
    for msg_index, message in enumerate(sequence.get("messages", []) or []):
        if isinstance(message, dict):
            item = (f"messages[{msg_index}]", message)
            if has_logic_blocks and _is_success_message(message):
                delayed_success.append(item)
            else:
                ordered.append(item)
    for block_index, block in enumerate(sequence.get("logic_blocks", []) or []):
        ordered.extend(_flatten_logic_block_message_order(block, f"logic_blocks[{block_index}]"))
    ordered.extend(delayed_success)
    return ordered


def _flatten_logic_block_message_order(block, path: str) -> list[tuple[str, dict]]:
    ordered = []
    if not isinstance(block, dict):
        return ordered
    for msg_index, message in enumerate(block.get("messages", []) or []):
        if isinstance(message, dict):
            ordered.append((f"{path}.messages[{msg_index}]", message))
    for block_index, nested_block in enumerate(block.get("logic_blocks", []) or []):
        ordered.extend(_flatten_logic_block_message_order(nested_block, f"{path}.logic_blocks[{block_index}]"))
    return ordered


def _message_method(message: dict) -> str:
    return _parse_method_name(str(message.get("message", "")).strip()).lower()


def _is_success_message(message: dict) -> bool:
    text = str(message.get("message", "")).replace("_", "").lower()
    return bool(SUCCESS_MESSAGE_RE.search(text))


def _operation_category(method: str) -> int | None:
    normalized = method.lower()
    if "submit" in normalized or "checkout" in normalized:
        return 10
    if "validate" in normalized:
        return 20
    if "calculate" in normalized or "total" in normalized:
        return 30
    if ("create" in normalized or "save" in normalized or "persist" in normalized or "insert" in normalized) and "order" in normalized:
        return 40
    if ("create" in normalized or "save" in normalized or "persist" in normalized or "insert" in normalized) and any(token in normalized for token in ["item", "line", "detail"]):
        return 50
    return None


def _is_mandatory_write_after_success(method: str) -> bool:
    normalized = method.lower()
    if _operation_category(normalized) == 50:
        return True
    return any(token in normalized for token in ["create", "save", "persist", "insert", "update"]) and not _is_success_method(normalized)


def _is_success_method(method: str) -> bool:
    return bool(SUCCESS_MESSAGE_RE.search(method.replace("_", "")))


def validate_sequence_diagrams(sequence_diagrams: list | None, class_diagram: dict | None) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    sequences = sequence_diagrams or []
    if not isinstance(sequences, list):
        errors.append(_error(
            "SEQ-STRUCTURE",
            "sequence_diagrams must be a list.",
            "critical",
            code="INVALID_SEQUENCE_COLLECTION",
        ))
        return _result(errors, warnings, 1, "sequence")

    class_methods = {}
    for cls in (class_diagram or {}).get("classes", []) or []:
        if not isinstance(cls, dict):
            continue
        name = str(cls.get("name", "")).strip()
        methods = {
            _parse_method_name(method)
            for method in cls.get("methods", []) or []
            if _parse_method_name(method)
        }
        if name:
            class_methods[name] = methods

    class_names = set(class_methods.keys())

    for seq_index, sequence in enumerate(sequences):
        total_checks += 1
        if not isinstance(sequence, dict):
            errors.append(_error(
                "SEQ-DIAGRAM",
                f"Sequence at index {seq_index} must be an object.",
                code="INVALID_SEQUENCE_OBJECT",
                path=f"sequence_diagrams[{seq_index}]",
            ))
            continue

        name = str(sequence.get("name", f"Sequence {seq_index + 1}"))
        participants = [str(p).strip() for p in sequence.get("participants", []) or [] if str(p).strip()]
        participant_types = sequence.get("participant_types", {}) or {}
        participant_set = set(participants)
        if not participants:
            errors.append(_error(
                "SEQ-PARTICIPANTS",
                f"Sequence '{name}' has no participants.",
                code="MISSING_SEQUENCE_PARTICIPANTS",
                path=f"sequence_diagrams[{seq_index}].participants",
                details={"sequence": name},
            ))

        for participant_index, participant in enumerate(participants):
            if participant not in class_names:
                if _is_external_participant(participant, participant_types):
                    warnings.append(_warning(
                        "SEQ-EXTERNAL-PARTICIPANT",
                        f"Participant '{participant}' is external and not a defined class.",
                        code="DECLARED_EXTERNAL_PARTICIPANT",
                        path=f"sequence_diagrams[{seq_index}].participants[{participant_index}]",
                        details={"participant": participant},
                    ))
                else:
                    errors.append(_error(
                        "SEQ-INTERNAL-PARTICIPANT",
                        f"Internal participant '{participant}' is not a defined class.",
                        code="UNKNOWN_INTERNAL_PARTICIPANT",
                        path=f"sequence_diagrams[{seq_index}].participants[{participant_index}]",
                        details={"participant": participant},
                    ))

        for block_path, block in _iter_logic_blocks(sequence):
            total_checks += 1
            block_type = str(block.get("block_type", block.get("type", "alt"))).strip().lower()
            condition = str(block.get("condition", "")).strip()
            if block_type == "alt" and ITERATION_CONDITION_RE.search(condition):
                errors.append(_error(
                    "SEQ-LOGIC-BLOCK",
                    f"Iteration condition '{condition}' in sequence '{name}' must use a loop fragment, not alt.",
                    code="ITERATION_MUST_USE_LOOP",
                    path=f"sequence_diagrams[{seq_index}].{block_path}.block_type",
                    details={"sequence": name, "condition": condition, "block_type": block_type},
                ))
            if block_type == "loop" and not condition:
                warnings.append(_warning(
                    "SEQ-LOOP-CONDITION",
                    f"Loop fragment in sequence '{name}' should describe the iteration condition.",
                    code="LOOP_CONDITION_MISSING",
                    path=f"sequence_diagrams[{seq_index}].{block_path}.condition",
                    details={"sequence": name},
                ))

        for message_path, message in _iter_sequence_messages(sequence):
            total_checks += 1
            if not isinstance(message, dict):
                errors.append(_error(
                    "SEQ-MESSAGE",
                    f"Message at {message_path} in sequence '{name}' must be an object.",
                    code="INVALID_SEQUENCE_MESSAGE_OBJECT",
                    path=f"sequence_diagrams[{seq_index}].{message_path}",
                    details={"sequence": name},
                ))
                continue

            sender = str(message.get("from", "")).strip()
            receiver = str(message.get("to", "")).strip()
            method = _parse_method_name(str(message.get("message", "")).strip())
            if sender not in participant_set:
                errors.append(_error(
                    "SEQ-SENDER",
                    f"Message sender '{sender}' is not declared in sequence '{name}'.",
                    code="UNDECLARED_MESSAGE_SENDER",
                    path=f"sequence_diagrams[{seq_index}].{message_path}.from",
                    details={"sequence": name, "sender": sender},
                ))
            if receiver not in participant_set:
                errors.append(_error(
                    "SEQ-RECEIVER",
                    f"Message receiver '{receiver}' is not declared in sequence '{name}'.",
                    code="UNDECLARED_MESSAGE_RECEIVER",
                    path=f"sequence_diagrams[{seq_index}].{message_path}.to",
                    details={"sequence": name, "receiver": receiver},
                ))
            if receiver in class_methods and method and method not in class_methods[receiver]:
                errors.append(_error(
                    "SEQ-METHOD",
                    f"Method '{method}' is not defined on receiving class '{receiver}'.",
                    code="UNKNOWN_RECEIVER_METHOD",
                    path=f"sequence_diagrams[{seq_index}].{message_path}.message",
                    details={
                        "sequence": name,
                        "receiver": receiver,
                        "method": method,
                        "available_methods": sorted(class_methods[receiver]),
                    },
                ))

        ordered_messages = _flatten_sequence_message_order(sequence)
        max_seen_category = 0
        for message_path, message in ordered_messages:
            total_checks += 1
            method = _message_method(message)
            category = _operation_category(method)
            if category is not None:
                if category < max_seen_category:
                    errors.append(_error(
                        "SEQ-MESSAGE-ORDER",
                        f"Message '{message.get('message', '')}' appears out of main-flow order in sequence '{name}'.",
                        code="MAIN_FLOW_MESSAGE_ORDER_VIOLATION",
                        path=f"sequence_diagrams[{seq_index}].{message_path}.message",
                        details={"sequence": name, "method": method},
                    ))
                max_seen_category = max(max_seen_category, category)

        for index, (message_path, message) in enumerate(ordered_messages):
            if not _is_success_message(message):
                continue
            later_writes = [
                later_message.get("message", "")
                for _, later_message in ordered_messages[index + 1:]
                if _is_mandatory_write_after_success(_message_method(later_message))
            ]
            if later_writes:
                errors.append(_error(
                    "SEQ-SUCCESS-ORDER",
                    f"Success/response message '{message.get('message', '')}' occurs before mandatory operations complete in sequence '{name}'.",
                    code="SUCCESS_BEFORE_MANDATORY_OPERATION",
                    path=f"sequence_diagrams[{seq_index}].{message_path}.message",
                    details={"sequence": name, "later_mandatory_operations": later_writes},
                ))

    return _result(errors, warnings, total_checks, "sequence")
