from __future__ import annotations

import re

EXTERNAL_PARTICIPANT_TYPES = {
    "actor",
    "boundary",
    "database",
    "external",
    "external_system",
    "system",
    "client",
    "user",
    "participant",
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


def is_architectural_component(name: str) -> bool:
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


def _split_call_args(args_str: str) -> list[str]:
    params = []
    current = []
    depth = 0
    for ch in args_str:
        if ch in ('<', '[', '('):
            depth += 1
            current.append(ch)
        elif ch in ('>', ']', ')'):
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            p = "".join(current).strip()
            if p:
                params.append(p)
            current = []
        else:
            current.append(ch)
    if current:
        p = "".join(current).strip()
        if p:
            params.append(p)
    return params


def _parse_method_call_args(text: str) -> list[str]:
    match = re.search(r"\((.*?)\)", str(text or ""))
    if not match:
        return []
    return _split_call_args(match.group(1).strip())


def _parse_arg_name_and_type(arg: object) -> tuple[str, str]:
    if isinstance(arg, dict):
        return str(arg.get("name", "")).strip(), str(arg.get("data_type", arg.get("type", ""))).strip()
    s = str(arg or "").strip()
    if not s:
        return "", ""
    if ":" in s:
        parts = s.split(":", 1)
        return parts[0].strip(), parts[1].strip()
    parts = s.split()
    if len(parts) == 2:
        if parts[0][0].isupper() and not parts[1][0].isupper():
            return parts[1].strip(), parts[0].strip()
        return parts[0].strip(), parts[1].strip()
    return s, ""


def _types_are_compatible(expected_type: str, actual_type: str) -> bool:
    if not expected_type or not actual_type:
        return True
    exp = expected_type.strip().lower()
    act = actual_type.strip().lower()
    if exp == act:
        return True
    synonyms = {
        "str": "string",
        "int": "integer",
        "bool": "boolean",
        "void": "void",
    }
    exp = synonyms.get(exp, exp)
    act = synonyms.get(act, act)
    if exp == act:
        return True
    if exp.startswith("list<") and act.startswith("list<") and exp.endswith(">") and act.endswith(">"):
        return _types_are_compatible(exp[5:-1], act[5:-1])
    return False


LIFECYCLE_CONTAINER_KEYWORDS = {
    "session", "meeting", "meetinginformation", "process", "workflow",
    "batch", "job", "request", "ticket", "draft", "document", "cart"
}

LIFECYCLE_ATTRIBUTES = {
    "status", "state", "phase", "stage", "createdat", "created_at",
    "uploadedfiles", "transcript", "rawdata"
}


def _is_lifecycle_container(name: str, entity_or_class: dict | None = None) -> bool:
    name_clean = str(name).strip().lower().replace("_", "")
    if any(kw in name_clean for kw in LIFECYCLE_CONTAINER_KEYWORDS):
        return True
    if entity_or_class and isinstance(entity_or_class, dict):
        attrs = entity_or_class.get("attributes", []) or []
        attr_names = {
            str(a.get("name") if isinstance(a, dict) else a).strip().lower().replace("_", "")
            for a in attrs
        }
        if any(la in attr_names for la in LIFECYCLE_ATTRIBUTES):
            return True
        methods = entity_or_class.get("methods", []) or []
        for m in methods:
            m_name = str(m.get("name") if isinstance(m, dict) else m).lower()
            if any(prefix in m_name for prefix in ("add", "append", "attach", "setstatus", "updatestatus")):
                return True
    return False


def _extract_method_detail(method: object) -> dict:
    if isinstance(method, dict):
        m_name = str(method.get("name", "")).strip()
        params = method.get("parameters", method.get("params", [])) or []
        required = []
        structured_params = []
        for p in params:
            if isinstance(p, dict):
                p_name = str(p.get("name", "")).strip()
                p_type = str(p.get("data_type", p.get("type", ""))).strip()
                is_req = p.get("required") is not False and "default" not in p and "default_value" not in p
                if is_req:
                    required.append(p_name)
                structured_params.append({"name": p_name, "type": p_type, "required": is_req})
            elif isinstance(p, str):
                p_clean = p.strip()
                p_name, p_type = _parse_arg_name_and_type(p_clean)
                is_req = ("=" not in p_clean and bool(p_name))
                if is_req:
                    required.append(p_name)
                structured_params.append({"name": p_name, "type": p_type, "required": is_req})
        ret_type = str(method.get("return_type", method.get("returns", ""))).strip()
        return {
            "name": m_name,
            "required_params": required,
            "parameters": structured_params,
            "return_type": ret_type,
        }
    elif isinstance(method, str):
        text = method.strip()
        if text and text[0] in ("+", "-", "#", "~"):
            text = text[1:].strip()
        m_name = _parse_method_name(text)
        ret_type = ""
        if ":" in text:
            ret_type = text.split(":")[-1].strip()
        raw_args = _parse_method_call_args(text)
        required = []
        structured_params = []
        for a in raw_args:
            p_name, p_type = _parse_arg_name_and_type(a)
            is_req = ("=" not in a and bool(p_name))
            if is_req:
                required.append(p_name)
            structured_params.append({"name": p_name, "type": p_type, "required": is_req})
        return {
            "name": m_name,
            "required_params": required,
            "parameters": structured_params,
            "return_type": ret_type,
        }
    elif hasattr(method, "name"):
        m_name = getattr(method, "name", "")
        params = getattr(method, "parameters", []) or []
        required = []
        structured_params = []
        for p in params:
            p_name = getattr(p, "name", str(p))
            p_type = getattr(p, "data_type", "")
            required.append(p_name)
            structured_params.append({"name": p_name, "type": p_type, "required": True})
        ret_type = getattr(method, "return_type", "")
        return {
            "name": m_name,
            "required_params": required,
            "parameters": structured_params,
            "return_type": ret_type,
        }
    return {}


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
        source_mult = str(rel.get("source_multiplicity", "")).strip()
        target_mult = str(rel.get("target_multiplicity", "")).strip()

        if cardinality and cardinality not in CLASS_CARDINALITY_VALUES:
            errors.append(_error(
                "CLASS-REL-CARDINALITY",
                f"Relationship cardinality '{cardinality}' is not supported.",
                code="UNSUPPORTED_CLASS_CARDINALITY",
                path=f"relationships[{index}].cardinality",
                details={"cardinality": cardinality},
            ))
        if source_mult and source_mult not in CLASS_CARDINALITY_VALUES:
            errors.append(_error(
                "CLASS-REL-SOURCE-MULTIPLICITY",
                f"Relationship source multiplicity '{source_mult}' is not supported.",
                code="UNSUPPORTED_CLASS_MULTIPLICITY",
                path=f"relationships[{index}].source_multiplicity",
                details={"source_multiplicity": source_mult},
            ))
        if target_mult and target_mult not in CLASS_CARDINALITY_VALUES:
            errors.append(_error(
                "CLASS-REL-TARGET-MULTIPLICITY",
                f"Relationship target multiplicity '{target_mult}' is not supported.",
                code="UNSUPPORTED_CLASS_MULTIPLICITY",
                path=f"relationships[{index}].target_multiplicity",
                details={"target_multiplicity": target_mult},
            ))
        effective_target_mult = target_mult or cardinality
        if effective_target_mult in ("1..*", "1"):
            source_class_obj = next((c for c in classes if isinstance(c, dict) and c.get("name") == source), None)
            if _is_lifecycle_container(source, source_class_obj):
                errors.append(_error(
                    "CLASS-LIFECYCLE-MULTIPLICITY",
                    f"Relationship from lifecycle entity '{source}' to '{target}' has target multiplicity '{effective_target_mult}', "
                    f"but '{source}' may exist before '{target}' is identified/created. Expected lower bound 0 (e.g., '0..*').",
                    code="LIFECYCLE_MULTIPLICITY_MISMATCH",
                    path=f"relationships[{index}].target_multiplicity",
                    details={"source": source, "target": target, "target_multiplicity": effective_target_mult},
                ))
        if rel_type == "dependency" and (cardinality or source_mult or target_mult):
            errors.append(_error(
                "CLASS-DEPENDENCY-CARDINALITY",
                "Dependency relationships must not define structural cardinality.",
                code="DEPENDENCY_CARDINALITY_NOT_ALLOWED",
                path=f"relationships[{index}].cardinality",
                details={"source": source, "target": target, "cardinality": cardinality or target_mult},
            ))
        if rel_type == "inheritance" and (cardinality or source_mult or target_mult):
            errors.append(_error(
                "CLASS-INHERITANCE-CARDINALITY",
                "Inheritance relationships must not define structural cardinality.",
                code="INHERITANCE_CARDINALITY_NOT_ALLOWED",
                path=f"relationships[{index}].cardinality",
                details={"source": source, "target": target, "cardinality": cardinality or target_mult},
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

        if is_architectural_component(name):
            errors.append(_error(
                "ER-ARCHITECTURAL-ENTITY",
                f"Architectural component '{name}' must not be converted into an ER persistent entity.",
                "critical",
                code="ARCHITECTURAL_COMPONENT_AS_ENTITY",
                path=f"entities[{index}].name",
                details={"entity": name},
            ))
            continue

        entity_names.add(name)
        attributes = entity.get("attributes", []) or []
        primary_key = str(entity.get("primary_key", "")).strip()
        if not primary_key:
            for attr in attributes:
                if isinstance(attr, dict) and attr.get("constraint") == "PK":
                    primary_key = str(attr.get("name", "")).strip()
                    break

        if not primary_key:
            errors.append(_error(
                "ER-PRIMARY-KEY",
                f"Entity '{name}' has no primary key.",
                "critical",
                code="MISSING_PRIMARY_KEY",
                path=f"entities[{index}].primary_key",
                details={"entity": name},
            ))
        if not attributes and not primary_key:
            errors.append(_error(
                "ER-ATTRIBUTES",
                f"Entity '{name}' has no attributes.",
                code="MISSING_ENTITY_ATTRIBUTES",
                path=f"entities[{index}].attributes",
                details={"entity": name},
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
        if target_multiplicity in ("1..*", "1"):
            source_ent_obj = next((e for e in entities if isinstance(e, dict) and e.get("name") == source), None)
            if _is_lifecycle_container(source, source_ent_obj):
                errors.append(_error(
                    "ER-LIFECYCLE-MULTIPLICITY",
                    f"ER relationship from lifecycle entity '{source}' to '{target}' has target multiplicity '{target_multiplicity}', "
                    f"but '{source}' may exist before '{target}' is identified/created. Expected lower bound 0 (e.g., '0..*').",
                    code="LIFECYCLE_MULTIPLICITY_MISMATCH",
                    path=f"relationships[{index}].target_multiplicity",
                    details={"source": source, "target": target, "target_multiplicity": target_multiplicity},
                ))

    # Detect redundant ER attributes that duplicate relationships to separate entities
    entity_related_targets: dict[str, set[str]] = {}
    for rel in relationships:
        if isinstance(rel, dict):
            s = str(rel.get("source", "")).strip()
            t = str(rel.get("target", "")).strip()
            if s and t:
                entity_related_targets.setdefault(s, set()).add(t)
                entity_related_targets.setdefault(t, set()).add(s)

    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            continue
        ename = str(entity.get("name", "")).strip()
        related_targets = entity_related_targets.get(ename, set())
        attributes = entity.get("attributes", []) or []
        for attr_idx, attr in enumerate(attributes):
            attr_name = str(attr.get("name") if isinstance(attr, dict) else attr).strip()
            attr_norm = attr_name.lower().replace("_", "")
            for target in related_targets:
                target_norm = target.lower().replace("_", "")
                if attr_norm in (target_norm, target_norm + "s", target_norm + "es", target_norm + "list", "list" + target_norm):
                    errors.append(_error(
                        "ER-REDUNDANT-ATTRIBUTE",
                        f"Entity '{ename}' has attribute '{attr_name}' which redundantly duplicates ER relationship to entity '{target}'.",
                        code="REDUNDANT_RELATIONSHIP_ATTRIBUTE",
                        path=f"entities[{index}].attributes[{attr_idx}]",
                        details={"entity": ename, "attribute": attr_name, "related_entity": target},
                    ))
                    break

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


def _is_external_participant(participant: str, participant_types: dict, actors: list | None = None) -> bool:
    if actors and participant in actors:
        return True
    participant_type = participant_types.get(participant, "")
    if hasattr(participant_type, "value"):
        participant_type = participant_type.value
    pt = str(participant_type).strip().lower()
    if pt in EXTERNAL_PARTICIPANT_TYPES or pt in ("control", "controller", "service", "repository", "boundary", "gateway"):
        return True
    p_lower = participant.lower()
    if any(p_lower == s or p_lower.startswith(s) or p_lower.endswith(s) for s in ("actor", "user", "client", "external", "database", "db", "gateway", "system", "boundary")):
        return True
    return False


def _iter_sequence_messages(sequence: dict):
    seen = set()

    def _walk(item, path: str):
        if not isinstance(item, dict):
            return
        if "block_type" in item or str(item.get("type", "")).lower() in {"loop", "alt", "opt", "else"}:
            for idx, child in enumerate(item.get("items", []) or []):
                yield from _walk(child, f"{path}.items[{idx}]")
            for idx, msg in enumerate(item.get("messages", []) or []):
                yield from _walk(msg, f"{path}.messages[{idx}]")
            for idx, blk in enumerate(item.get("logic_blocks", []) or []):
                yield from _walk(blk, f"{path}.logic_blocks[{idx}]")
        else:
            item_id = id(item)
            if item_id not in seen:
                seen.add(item_id)
                yield path, item

    if sequence.get("items"):
        for idx, item in enumerate(sequence.get("items", []) or []):
            yield from _walk(item, f"items[{idx}]")
    if sequence.get("interactions"):
        for idx, item in enumerate(sequence.get("interactions", []) or []):
            yield from _walk(item, f"interactions[{idx}]")
    if sequence.get("messages"):
        for idx, msg in enumerate(sequence.get("messages", []) or []):
            yield from _walk(msg, f"messages[{idx}]")
    if sequence.get("logic_blocks"):
        for idx, blk in enumerate(sequence.get("logic_blocks", []) or []):
            yield from _walk(blk, f"logic_blocks[{idx}]")


def _iter_logic_blocks(sequence: dict):
    seen = set()

    def _walk(item, path: str):
        if not isinstance(item, dict):
            return
        if "block_type" in item or str(item.get("type", "")).lower() in {"loop", "alt", "opt", "else"}:
            item_id = id(item)
            if item_id not in seen:
                seen.add(item_id)
                yield path, item
            for idx, child in enumerate(item.get("items", []) or []):
                yield from _walk(child, f"{path}.items[{idx}]")
            for idx, blk in enumerate(item.get("logic_blocks", []) or []):
                yield from _walk(blk, f"{path}.logic_blocks[{idx}]")

    for idx, item in enumerate(sequence.get("items", sequence.get("interactions", [])) or []):
        yield from _walk(item, f"items[{idx}]")
    for idx, blk in enumerate(sequence.get("logic_blocks", []) or []):
        yield from _walk(blk, f"logic_blocks[{idx}]")


def _flatten_sequence_message_order(sequence: dict) -> list[tuple[str, dict]]:
    ordered = []
    seen = set()

    def _walk(item, path: str):
        if not isinstance(item, dict):
            return
        if "block_type" in item or str(item.get("type", "")).lower() in {"loop", "alt", "opt", "else"}:
            for idx, child in enumerate(item.get("items", []) or []):
                _walk(child, f"{path}.items[{idx}]")
            for idx, msg in enumerate(item.get("messages", []) or []):
                _walk(msg, f"{path}.messages[{idx}]")
            for idx, blk in enumerate(item.get("logic_blocks", []) or []):
                _walk(blk, f"{path}.logic_blocks[{idx}]")
        else:
            item_id = id(item)
            if item_id not in seen:
                seen.add(item_id)
                ordered.append((path, item))

    raw_items = sequence.get("items", sequence.get("interactions", [])) or []
    if raw_items:
        for idx, item in enumerate(raw_items):
            _walk(item, f"items[{idx}]")
    else:
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
            _walk(block, f"logic_blocks[{block_index}]")
        ordered.extend(delayed_success)

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
    class_method_details = {}
    for cls in (class_diagram or {}).get("classes", []) or []:
        if not isinstance(cls, dict):
            continue
        name = str(cls.get("name", "")).strip()
        methods = set()
        method_details = {}
        for method in cls.get("methods", []) or []:
            detail = _extract_method_detail(method)
            m_name = detail.get("name")
            if m_name:
                methods.add(m_name)
                method_details[m_name] = detail
        if name:
            class_methods[name] = methods
            class_method_details[name] = method_details

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
            p_lower = participant.lower()
            is_speculative = p_lower in ("controller", "service", "repository", "frontend", "ui") or any(
                p_lower.endswith(sfx) and len(p_lower) > len(sfx)
                for sfx in ("controller", "service", "repository", "frontend")
            )
            if is_speculative and participant not in class_names:
                warnings.append(_warning(
                    "SEQ-SPECULATIVE-ARCHITECTURE",
                    f"Participant '{participant}' is a speculative architectural component without verified HLD or Class Diagram backing.",
                    code="SPECULATIVE_ARCHITECTURE_PARTICIPANT",
                    path=f"sequence_diagrams[{seq_index}].participants[{participant_index}]",
                    details={"participant": participant, "sequence": name},
                ))
            if participant not in class_names:
                if _is_external_participant(participant, participant_types, sequence.get("actors", []) or []):
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

            # Issue 3: Do not validate return labels as receiving-class method calls
            raw_msg_type = str(message.get("type", "")).strip().lower()
            raw_arrow = str(message.get("arrow", "")).strip()
            msg_text = str(message.get("message", "")).strip().lower()
            is_return = (
                raw_msg_type in ("return", "reply", "response")
                or raw_arrow == "-->"
                or msg_text.startswith("return")
                or msg_text.startswith("response")
                or msg_text in ("result", "response", "ack", "token", "ok", "error", "data")
                or bool(re.search(r"\b(result|response|acknowledgement|ack)\b", msg_text))
            )

            if receiver in class_methods and method and not is_return:
                if method not in class_methods[receiver]:
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
                else:
                    # Issue 4: Check structured method required arguments and return contracts
                    m_detail = class_method_details.get(receiver, {}).get(method)
                    if m_detail:
                        req_params = m_detail.get("required_params", [])
                        call_args = message.get("arguments", []) or []
                        if not call_args:
                            parsed_args = _parse_method_call_args(str(message.get("message", "")))
                            if parsed_args:
                                call_args = parsed_args
                        if call_args and len(call_args) < len(req_params):
                            errors.append(_error(
                                "SEQ-METHOD-ARGS",
                                f"Method '{method}' on class '{receiver}' requires {len(req_params)} arguments, but {len(call_args)} were provided.",
                                code="MISSING_REQUIRED_METHOD_ARGUMENTS",
                                path=f"sequence_diagrams[{seq_index}].{message_path}.message",
                                details={
                                    "sequence": name,
                                    "receiver": receiver,
                                    "method": method,
                                    "required_parameters": req_params,
                                    "provided_arguments": call_args,
                                },
                            ))
                        params = m_detail.get("parameters", [])
                        if call_args and params and len(call_args) > len(params):
                            errors.append(_error(
                                "SEQ-METHOD-ARGS",
                                f"Method '{method}' on class '{receiver}' defines {len(params)} parameters, but {len(call_args)} arguments were provided.",
                                code="METHOD_ARGUMENT_COUNT_MISMATCH",
                                path=f"sequence_diagrams[{seq_index}].{message_path}.message",
                                details={
                                    "sequence": name,
                                    "receiver": receiver,
                                    "method": method,
                                    "defined_parameters": [p.get("name") for p in params],
                                    "provided_arguments": call_args,
                                },
                            ))
                        for arg_idx, arg_item in enumerate(call_args):
                            if arg_idx < len(params):
                                param_info = params[arg_idx]
                                param_name = param_info.get("name", "")
                                param_type = param_info.get("type", "")
                                arg_name, arg_type = _parse_arg_name_and_type(arg_item)
                                if arg_type and param_type and not _types_are_compatible(param_type, arg_type):
                                    errors.append(_error(
                                        "SEQ-METHOD-ARG-TYPE",
                                        f"Method '{method}' on class '{receiver}' expects parameter '{param_name}: {param_type}', "
                                        f"but argument was provided with incompatible type '{arg_type}'.",
                                        code="METHOD_ARGUMENT_TYPE_MISMATCH",
                                        path=f"sequence_diagrams[{seq_index}].{message_path}.arguments[{arg_idx}]",
                                        details={
                                            "sequence": name,
                                            "receiver": receiver,
                                            "method": method,
                                            "parameter": param_name,
                                            "expected_type": param_type,
                                            "actual_type": arg_type,
                                        },
                                    ))
                        expected_return = str(message.get("return_type", message.get("returns", ""))).strip()
                        defined_return = str(m_detail.get("return_type", "")).strip()
                        if expected_return and defined_return and defined_return.lower() not in ("void", "") and expected_return.lower() != defined_return.lower():
                            errors.append(_error(
                                "SEQ-METHOD-RETURN",
                                f"Method '{method}' returns '{defined_return}', but sequence expects '{expected_return}'.",
                                code="INCOMPATIBLE_RETURN_CONTRACT",
                                path=f"sequence_diagrams[{seq_index}].{message_path}.return_type",
                                details={
                                    "sequence": name,
                                    "receiver": receiver,
                                    "method": method,
                                    "expected_return": expected_return,
                                    "defined_return": defined_return,
                                },
                            ))

        ordered_messages = _flatten_sequence_message_order(sequence)

        # Lifeline activation balance tracking (including nested self-calls)
        activation_depth: dict[str, int] = {}
        for participant in participants:
            activation_depth[participant] = 0

        for message_path, message in ordered_messages:
            total_checks += 1
            sender = str(message.get("from", "")).strip()
            receiver = str(message.get("to", "")).strip()
            raw_msg_type = str(message.get("type", "call")).strip().lower()
            raw_arrow = str(message.get("arrow", "")).strip()
            msg_text = str(message.get("message", "")).strip().lower()
            is_return = (
                raw_msg_type in ("return", "reply", "response")
                or raw_arrow == "-->"
                or msg_text.startswith("return")
                or msg_text.startswith("response")
                or msg_text in ("result", "response", "ack", "token", "ok", "error", "data")
                or bool(re.search(r"\b(result|response|acknowledgement|ack)\b", msg_text))
            )
            activates = bool(message.get("activate", message.get("activates_target", False)))
            deactivates = bool(message.get("deactivate", message.get("deactivates_target", False)))

            if not is_return:
                if activates and not deactivates:
                    activation_depth[receiver] = activation_depth.get(receiver, 0) + 1
                elif activates and deactivates:
                    pass
                elif deactivates and not activates:
                    current_depth = activation_depth.get(receiver, 0)
                    if current_depth <= 0:
                        errors.append(_error(
                            "SEQ-ACTIVATION-BALANCE",
                            f"Participant '{receiver}' is deactivated while not active in sequence '{name}'.",
                            code="DEACTIVATING_UNACTIVATED_LIFELINE",
                            path=f"sequence_diagrams[{seq_index}].{message_path}",
                            details={"sequence": name, "participant": receiver},
                        ))
                    else:
                        activation_depth[receiver] = current_depth - 1
            else:
                current_depth = activation_depth.get(sender, 0)
                if current_depth > 0:
                    activation_depth[sender] = current_depth - 1
                elif deactivates:
                    errors.append(_error(
                        "SEQ-ACTIVATION-BALANCE",
                        f"Participant '{sender}' is deactivated on return while not active in sequence '{name}'.",
                        code="DEACTIVATING_UNACTIVATED_LIFELINE",
                        path=f"sequence_diagrams[{seq_index}].{message_path}",
                        details={"sequence": name, "participant": sender},
                    ))

        for p, depth in activation_depth.items():
            if depth > 0:
                errors.append(_error(
                    "SEQ-ACTIVATION-BALANCE",
                    f"Participant '{p}' has {depth} unbalanced activation(s) without matching completion in sequence '{name}'.",
                    code="UNBALANCED_LIFELINE_ACTIVATION",
                    path=f"sequence_diagrams[{seq_index}]",
                    details={"sequence": name, "participant": p, "unbalanced_depth": depth},
                ))

        # Check mandatory processing steps for the selected use case
        has_input = False
        has_processing = False
        has_response = False
        for _, msg in ordered_messages:
            m_text = str(msg.get("message", "")).lower()
            m_type = str(msg.get("type", "")).lower()
            if any(token in m_text for token in ("upload", "submit", "request", "create", "start", "init")):
                has_input = True
            if any(token in m_text for token in ("process", "convert", "extract", "identify", "calculate", "validate", "save", "persist", "add", "set")):
                has_processing = True
            if any(token in m_text for token in ("response", "result", "confirm", "ack", "token", "status", "complete")) or m_type == "return":
                has_response = True

        if len(ordered_messages) >= 2 and not (has_input and has_response):
            warnings.append(_warning(
                "SEQ-USE-CASE-STEPS",
                f"Sequence '{name}' should include all mandatory lifecycle steps (trigger/input, processing, and response) for its use case.",
                code="MISSING_MANDATORY_PROCESSING_STEP",
                details={"sequence": name, "has_input": has_input, "has_processing": has_processing, "has_response": has_response},
            ))

        # Check failure handling and progress behavior where applicable
        has_failure_handling = any(
            isinstance(b, dict) and str(b.get("block_type", b.get("type", ""))).lower() == "alt"
            for _, b in _iter_logic_blocks(sequence)
        ) or any(
            any(err_token in str(m.get("message", "")).lower() for err_token in ("error", "fail", "invalid", "reject"))
            for _, m in ordered_messages
        )
        is_heavy_processing = any(
            any(kw in str(m.get("message", "")).lower() for kw in ("upload", "convert", "extract", "transcribe", "speech", "audio", "video", "file", "document", "import"))
            for _, m in ordered_messages
        )
        if is_heavy_processing and not has_failure_handling:
            warnings.append(_warning(
                "SEQ-FAILURE-HANDLING",
                f"Sequence '{name}' performs file/multi-step processing but defines no alternative failure handling or error paths.",
                code="MISSING_FAILURE_BEHAVIOR",
                details={"sequence": name},
            ))

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
