from __future__ import annotations

import re


CLASS_RELATIONSHIP_TYPES = {
    "association",
    "aggregation",
    "composition",
    "inheritance",
    "dependency",
}

ER_RELATIONSHIP_TYPES = {
    "one-to-one",
    "one-to-many",
    "many-to-one",
    "many-to-many",
}


def _result(errors: list[dict], warnings: list[dict], total_checks: int) -> dict:
    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "total_checks": total_checks,
        "passed_checks": max(total_checks - len(errors), 0),
    }


def _error(rule_id: str, message: str, severity: str = "high") -> dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
    }


def _warning(rule_id: str, message: str) -> dict:
    return {
        "rule_id": rule_id,
        "severity": "warning",
        "message": message,
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
        errors.append(_error("CLASS-STRUCTURE", "class_diagram.classes must be a list.", "critical"))
        return _result(errors, warnings, 1)

    class_names = set()
    for index, cls in enumerate(classes):
        total_checks += 1
        if not isinstance(cls, dict):
            errors.append(_error("CLASS-STRUCTURE", f"Class at index {index} must be an object."))
            continue

        name = str(cls.get("name", "")).strip()
        if not name:
            errors.append(_error("CLASS-NAME", f"Class at index {index} has no name."))
            continue

        class_names.add(name)
        attributes = cls.get("attributes", []) or []
        methods = cls.get("methods", []) or []
        if not attributes and not methods:
            errors.append(_error("CLASS-EMPTY", f"Class '{name}' has no attributes or methods."))

    connected = set()
    for index, rel in enumerate(relationships):
        total_checks += 1
        if not isinstance(rel, dict):
            errors.append(_error("CLASS-RELATIONSHIP", f"Relationship at index {index} must be an object."))
            continue

        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        rel_type = str(rel.get("type", "association")).strip()
        if source not in class_names:
            errors.append(_error("CLASS-REL-SOURCE", f"Relationship source '{source}' is not a defined class."))
        if target not in class_names:
            errors.append(_error("CLASS-REL-TARGET", f"Relationship target '{target}' is not a defined class."))
        if rel_type not in CLASS_RELATIONSHIP_TYPES:
            errors.append(_error("CLASS-REL-TYPE", f"Relationship type '{rel_type}' is not supported."))
        if source in class_names:
            connected.add(source)
        if target in class_names:
            connected.add(target)

    if len(class_names) > 1:
        for name in sorted(class_names - connected):
            warnings.append(_warning("CLASS-ISOLATED", f"Class '{name}' is isolated."))

    return _result(errors, warnings, total_checks)


def validate_er_diagram(er_diagram: dict | None, class_diagram: dict | None) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    diagram = er_diagram or {}
    entities = diagram.get("entities", []) or []
    relationships = diagram.get("relationships", []) or []

    if not isinstance(entities, list):
        errors.append(_error("ER-STRUCTURE", "er_diagram.entities must be a list.", "critical"))
        return _result(errors, warnings, 1)

    entity_names = set()
    for index, entity in enumerate(entities):
        total_checks += 1
        if not isinstance(entity, dict):
            errors.append(_error("ER-ENTITY", f"Entity at index {index} must be an object."))
            continue

        name = str(entity.get("name", "")).strip()
        if not name:
            errors.append(_error("ER-ENTITY-NAME", f"Entity at index {index} has no name."))
            continue

        entity_names.add(name)
        attributes = entity.get("attributes", []) or []
        primary_key = str(entity.get("primary_key", "")).strip()
        if not primary_key:
            errors.append(_error("ER-PRIMARY-KEY", f"Entity '{name}' has no primary key.", "critical"))
        if not attributes:
            errors.append(_error("ER-ATTRIBUTES", f"Entity '{name}' has no attributes."))

    for index, rel in enumerate(relationships):
        total_checks += 1
        if not isinstance(rel, dict):
            errors.append(_error("ER-RELATIONSHIP", f"ER relationship at index {index} must be an object."))
            continue

        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        rel_type = str(rel.get("type", "one-to-many")).strip()
        if source not in entity_names:
            errors.append(_error("ER-REL-SOURCE", f"ER relationship source '{source}' is not a defined entity."))
        if target not in entity_names:
            errors.append(_error("ER-REL-TARGET", f"ER relationship target '{target}' is not a defined entity."))
        if rel_type not in ER_RELATIONSHIP_TYPES:
            errors.append(_error("ER-REL-TYPE", f"ER relationship type '{rel_type}' is not supported."))

    class_names = {
        str(cls.get("name", "")).strip().lower().replace("_", "")
        for cls in (class_diagram or {}).get("classes", []) or []
        if isinstance(cls, dict) and cls.get("attributes")
    }
    entity_names_normalized = {name.lower().replace("_", "") for name in entity_names}
    for class_name in sorted(class_names):
        if class_name and class_name not in entity_names_normalized and class_name + "s" not in entity_names_normalized:
            warnings.append(_warning("ER-CLASS-MAPPING", f"Persistent class concept '{class_name}' has no obvious ER entity."))

    return _result(errors, warnings, total_checks)


def validate_sequence_diagrams(sequence_diagrams: list | None, class_diagram: dict | None) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    sequences = sequence_diagrams or []
    if not isinstance(sequences, list):
        errors.append(_error("SEQ-STRUCTURE", "sequence_diagrams must be a list.", "critical"))
        return _result(errors, warnings, 1)

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
            errors.append(_error("SEQ-DIAGRAM", f"Sequence at index {seq_index} must be an object."))
            continue

        name = str(sequence.get("name", f"Sequence {seq_index + 1}"))
        participants = [str(p).strip() for p in sequence.get("participants", []) or [] if str(p).strip()]
        participant_set = set(participants)
        if not participants:
            errors.append(_error("SEQ-PARTICIPANTS", f"Sequence '{name}' has no participants."))

        for participant in participants:
            if participant not in class_names:
                warnings.append(_warning("SEQ-EXTERNAL-PARTICIPANT", f"Participant '{participant}' is not a defined class."))

        for msg_index, message in enumerate(sequence.get("messages", []) or []):
            total_checks += 1
            if not isinstance(message, dict):
                errors.append(_error("SEQ-MESSAGE", f"Message {msg_index} in sequence '{name}' must be an object."))
                continue

            sender = str(message.get("from", "")).strip()
            receiver = str(message.get("to", "")).strip()
            method = _parse_method_name(str(message.get("message", "")).strip())
            if sender not in participant_set:
                errors.append(_error("SEQ-SENDER", f"Message sender '{sender}' is not declared in sequence '{name}'."))
            if receiver not in participant_set:
                errors.append(_error("SEQ-RECEIVER", f"Message receiver '{receiver}' is not declared in sequence '{name}'."))
            if receiver in class_methods and method and method not in class_methods[receiver]:
                errors.append(_error("SEQ-METHOD", f"Method '{method}' is not defined on receiving class '{receiver}'."))

    return _result(errors, warnings, total_checks)
