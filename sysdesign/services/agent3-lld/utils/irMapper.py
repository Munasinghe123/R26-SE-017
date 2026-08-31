from __future__ import annotations

import re
from schemas.ir_schema import (
    IntermediateRepresentation,
    ClassIR,
    ClassRelationship,
    Method,
    MethodParameter,
    LogicBlock,
    LogicBlockType,
    ParticipantType,
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


def _parse_participant_type(value: object) -> ParticipantType:
    normalized = str(value).strip().lower()
    for participant_type in ParticipantType:
        if participant_type.value == normalized:
            return participant_type
    return ParticipantType.PARTICIPANT


def _parse_logic_block_type(value: object) -> LogicBlockType:
    normalized = str(value).strip().lower()
    for logic_block_type in LogicBlockType:
        if logic_block_type.value == normalized:
            return logic_block_type
    return LogicBlockType.ALT


def _parse_sequence_message(raw_msg: dict) -> SequenceMessage:
    sender = str(raw_msg.get("from", "")).strip()
    receiver = str(raw_msg.get("to", "")).strip()
    message_text = str(raw_msg.get("message", "")).strip()

    method_name, args = _parse_method_signature(message_text)
    
    # Requirement 6: Check explicit type field first
    raw_type = str(raw_msg.get("type", "")).strip().lower()
    if raw_type == "return":
        msg_type = MessageType.RETURN
    elif raw_type == "call":
        msg_type = MessageType.CALL
    elif message_text.lower().startswith("return"):
        msg_type = MessageType.RETURN
    else:
        msg_type = MessageType.CALL

    return SequenceMessage(
        from_participant=sender,
        to_participant=receiver,
        method=method_name or message_text,
        arguments=args,
        activates_target=bool(raw_msg.get("activate", raw_msg.get("activates_target", False))),
        deactivates_target=bool(raw_msg.get("deactivate", raw_msg.get("deactivates_target", False))),
        type=msg_type,
    )


def _parse_logic_block(raw_block: dict) -> LogicBlock:
    logic_type = _parse_logic_block_type(raw_block.get("block_type", raw_block.get("type", "alt")))

    messages = []
    items: list[SequenceMessage | LogicBlock] = []
    
    raw_items = raw_block.get("items", raw_block.get("interactions", [])) or []
    if raw_items:
        for raw_item in raw_items:
            if isinstance(raw_item, dict):
                if "block_type" in raw_item or "type" in raw_item and str(raw_item.get("type")).lower() in {"loop", "alt", "opt", "else"}:
                    sub_block = _parse_logic_block(raw_item)
                    items.append(sub_block)
                else:
                    msg = _parse_sequence_message(raw_item)
                    messages.append(msg)
                    items.append(msg)
    else:
        for raw_msg in raw_block.get("messages", []) or []:
            if isinstance(raw_msg, dict):
                msg = _parse_sequence_message(raw_msg)
                messages.append(msg)
                items.append(msg)

    nested_blocks: list[LogicBlock] = []
    for raw_nested_block in raw_block.get("logic_blocks", []) or []:
        if isinstance(raw_nested_block, dict):
            sub_block = _parse_logic_block(raw_nested_block)
            nested_blocks.append(sub_block)
            if not raw_items:
                items.append(sub_block)

    return LogicBlock(
        block_type=logic_type,
        condition=str(raw_block.get("condition", "")).strip(),
        messages=messages,
        logic_blocks=nested_blocks,
        items=items,
    )


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
        participant_types_raw = raw_seq.get("participant_types", {}) or {}
        participant_types: dict[str, ParticipantType] = {}
        if isinstance(participant_types_raw, dict):
            for participant_name, participant_type in participant_types_raw.items():
                participant_name = str(participant_name).strip()
                if participant_name:
                    participant_types[participant_name] = _parse_participant_type(participant_type)

        logic_blocks: list[LogicBlock] = []
        messages: list[SequenceMessage] = []
        items: list[SequenceMessage | LogicBlock] = []
        raw_items = raw_seq.get("items", raw_seq.get("interactions", [])) or []

        if raw_items:
            for raw_item in raw_items:
                if isinstance(raw_item, dict):
                    if "block_type" in raw_item or ("type" in raw_item and str(raw_item.get("type")).lower() in {"loop", "alt", "opt", "else"}):
                        block = _parse_logic_block(raw_item)
                        logic_blocks.append(block)
                        items.append(block)
                    else:
                        msg = _parse_sequence_message(raw_item)
                        messages.append(msg)
                        items.append(msg)
        else:
            for raw_block in raw_seq.get("logic_blocks", []) or []:
                if isinstance(raw_block, dict):
                    logic_blocks.append(_parse_logic_block(raw_block))

            for raw_msg in raw_seq.get("messages", []) or []:
                if isinstance(raw_msg, dict):
                    msg = _parse_sequence_message(raw_msg)
                    messages.append(msg)
                    items.append(msg)

            for block in logic_blocks:
                items.append(block)

        sequences.append(SequenceIR(
            name=name,
            description=description,
            participants=participants,
            participant_types=participant_types,
            logic_blocks=logic_blocks,
            messages=messages,
            items=items,
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
