from __future__ import annotations

import re
from schemas.ir_schema import (
    IntermediateRepresentation,
    ClassIR,
    ClassRelationship,
    Method,
    MethodParameter,
    SequenceIR,
    SequenceMessage,
    MessageType,
    EntityIR,
    EntityAttribute,
    EntityRelationship,
)


def _parse_method_signature(text: str) -> tuple[str, list[str]]:
    if not text:
        return "", []

    match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*$", text)
    if not match:
        return text.strip(), []

    name = match.group(1).strip()
    args_block = match.group(2).strip()
    if not args_block:
        return name, []

    args = [arg.strip() for arg in args_block.split(",") if arg.strip()]
    return name, args


def _ensure_class(class_index: dict[str, ClassIR], name: str) -> ClassIR:
    if name in class_index:
        return class_index[name]

    cls = ClassIR(name=name)
    class_index[name] = cls
    return cls


def _ensure_entity(entity_index: dict[str, EntityIR], name: str) -> EntityIR:
    if name in entity_index:
        return entity_index[name]

    entity = EntityIR(name=name)
    entity_index[name] = entity
    return entity


def convert_to_ir(parsed_json: dict) -> IntermediateRepresentation:
    parsed_json = parsed_json or {}

    # ------------------------------------
    # Classes
    # ------------------------------------
    class_diagram = parsed_json.get("class_diagram", {}) or {}
    raw_classes = class_diagram.get("classes", []) or []

    classes: list[ClassIR] = []
    class_index: dict[str, ClassIR] = {}

    for raw_cls in raw_classes:
        name = str(raw_cls.get("name", "")).strip()
        if not name:
            continue

        attributes = [str(a) for a in raw_cls.get("attributes", []) or []]
        raw_methods = raw_cls.get("methods", []) or []
        methods: list[Method] = []
        for raw_method in raw_methods:
            method_text = str(raw_method).strip()
            if not method_text:
                continue

            method_name, args = _parse_method_signature(method_text)
            parameters = [MethodParameter(name=arg) for arg in args]
            methods.append(Method(
                name=method_name or method_text,
                parameters=parameters,
            ))

        cls = ClassIR(
            name=name,
            attributes=attributes,
            methods=methods,
        )
        classes.append(cls)
        class_index[name] = cls

    raw_relationships = class_diagram.get("relationships", []) or []
    for rel in raw_relationships:
        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        if not source or not target:
            continue

        rel_type = str(rel.get("type", "association"))
        cardinality = str(rel.get("cardinality", ""))
        cls = _ensure_class(class_index, source)
        if cls not in classes:
            classes.append(cls)

        cls.relationships.append(ClassRelationship(
            target=target,
            rel_type=rel_type,
            cardinality=cardinality,
        ))

    # ------------------------------------
    # Sequences
    # ------------------------------------
    sequences: list[SequenceIR] = []
    raw_sequences = parsed_json.get("sequence_diagrams", []) or []

    for raw_seq in raw_sequences:
        name = str(raw_seq.get("name", "Sequence"))
        description = str(raw_seq.get("description", ""))
        participants = [str(p) for p in raw_seq.get("participants", []) or []]

        messages: list[SequenceMessage] = []
        for raw_msg in raw_seq.get("messages", []) or []:
            sender = str(raw_msg.get("from", "")).strip()
            receiver = str(raw_msg.get("to", "")).strip()
            message_text = str(raw_msg.get("message", "")).strip()

            method_name, args = _parse_method_signature(message_text)
            msg_type = MessageType.CALL
            if message_text.lower().startswith("return"):
                msg_type = MessageType.RETURN

            messages.append(SequenceMessage(
                from_participant=sender,
                to_participant=receiver,
                method=method_name or message_text,
                arguments=args,
                type=msg_type,
            ))

        sequences.append(SequenceIR(
            name=name,
            description=description,
            participants=participants,
            messages=messages,
        ))

    # ------------------------------------
    # Entities
    # ------------------------------------
    er_diagram = parsed_json.get("er_diagram", {}) or {}
    raw_entities = er_diagram.get("entities", []) or []

    entities: list[EntityIR] = []
    entity_index: dict[str, EntityIR] = {}

    for raw_entity in raw_entities:
        name = str(raw_entity.get("name", "")).strip()
        if not name:
            continue

        primary_key = str(raw_entity.get("primary_key", "")).strip()
        raw_attrs = raw_entity.get("attributes", []) or []

        attributes: list[EntityAttribute] = []
        for attr in raw_attrs:
            attr_name = str(attr).strip()
            if not attr_name:
                continue

            constraint = ""
            if primary_key and attr_name == primary_key:
                constraint = "PK"
            attributes.append(EntityAttribute(
                name=attr_name,
                constraint=constraint,
            ))

        if primary_key and all(a.name != primary_key for a in attributes):
            attributes.insert(0, EntityAttribute(
                name=primary_key,
                constraint="PK",
            ))

        entity = EntityIR(
            name=name,
            attributes=attributes,
        )
        entities.append(entity)
        entity_index[name] = entity

    raw_entity_relationships = er_diagram.get("relationships", []) or []
    for rel in raw_entity_relationships:
        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        if not source or not target:
            continue

        rel_type = str(rel.get("type", "one-to-many"))
        entity = _ensure_entity(entity_index, source)
        if entity not in entities:
            entities.append(entity)

        entity.relationships.append(EntityRelationship(
            target=target,
            rel_type=rel_type,
        ))

    return IntermediateRepresentation(
        classes=classes,
        sequences=sequences,
        entities=entities,
    )
