import logging
import re
from schemas.ir_schema import (
    IntermediateRepresentation,
    ClassIR,
    ClassRelationship,
    Method,
    MethodParameter,
    Visibility,
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

logger = logging.getLogger(__name__)

METHOD_PATTERN = re.compile(
    r"^\s*(?:([+\-#~])\s*)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)(?:\s*:\s*([a-zA-Z0-9_<>,\s\[\]*&?]+))?\s*$"
)


def _split_parameters(args_block: str) -> list[str]:
    params = []
    current = []
    depth = 0
    for ch in args_block:
        if ch in ('<', '[', '('):
            depth += 1
            current.append(ch)
        elif ch in ('>', ']', ')'):
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            params.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        p = "".join(current).strip()
        if p:
            params.append(p)
    return params


def _parse_param(param_str: str) -> tuple[str, str]:
    p = param_str.strip()
    if not p:
        return "", ""
    if ":" in p:
        parts = p.split(":", 1)
        return parts[0].strip(), parts[1].strip()
    parts = p.split()
    if len(parts) == 2:
        return parts[1].strip(), parts[0].strip()
    return p, ""


def _map_visibility(prefix: str | None) -> Visibility:
    if not prefix:
        return Visibility.PUBLIC
    prefix_clean = prefix.strip().lower()
    if prefix_clean in ("-", "private"):
        return Visibility.PRIVATE
    if prefix_clean in ("#", "protected"):
        return Visibility.PROTECTED
    if prefix_clean in ("~", "package"):
        return Visibility.PACKAGE
    return Visibility.PUBLIC


def _parse_method_object(raw_method: object) -> Method:
    if isinstance(raw_method, dict):
        name = str(raw_method.get("name", "")).strip()
        return_type = str(raw_method.get("return_type", raw_method.get("returns", raw_method.get("type", "void")))).strip() or "void"
        visibility = _map_visibility(str(raw_method.get("visibility", "public")))
        params_raw = raw_method.get("parameters", raw_method.get("params", [])) or []
        parameters: list[MethodParameter] = []
        for p in params_raw:
            if isinstance(p, dict):
                p_name = str(p.get("name", "")).strip()
                p_type = str(p.get("data_type", p.get("type", ""))).strip()
                if p_name:
                    parameters.append(MethodParameter(name=p_name, data_type=p_type))
            elif isinstance(p, str):
                p_name, p_type = _parse_param(p)
                if p_name:
                    parameters.append(MethodParameter(name=p_name, data_type=p_type))
        return Method(
            name=name,
            parameters=parameters,
            visibility=visibility,
            return_type=return_type,
        )

    text = str(raw_method or "").strip()
    if not text:
        return Method(name="")

    match = METHOD_PATTERN.match(text)
    if match:
        vis_char, name, args_raw, ret_type = match.groups()
        visibility = _map_visibility(vis_char)
        param_strings = _split_parameters(args_raw or "")
        parameters = []
        for ps in param_strings:
            p_name, p_type = _parse_param(ps)
            if p_name:
                parameters.append(MethodParameter(name=p_name, data_type=p_type))
        return Method(
            name=name,
            parameters=parameters,
            visibility=visibility,
            return_type=ret_type.strip() if ret_type else "void",
        )

    # Fallback for plain method text without parentheses
    clean_text = text
    visibility = Visibility.PUBLIC
    if clean_text and clean_text[0] in ("+", "-", "#", "~"):
        visibility = _map_visibility(clean_text[0])
        clean_text = clean_text[1:].strip()
    return Method(
        name=clean_text or text,
        parameters=[],
        visibility=visibility,
        return_type="void",
    )


def _parse_method_signature(text: str) -> tuple[str, list[str]]:
    method = _parse_method_object(text)
    return method.name, [p.name for p in method.parameters]


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
            method_obj = _parse_method_object(raw_method)
            if method_obj and method_obj.name:
                methods.append(method_obj)

        cls = ClassIR(
            name=name,
            attributes=attributes,
            methods=methods,
            requirement_ids=[str(rid) for rid in raw_cls.get("requirement_ids", []) or []],
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
        source_mult = str(rel.get("source_multiplicity", ""))
        target_mult = str(rel.get("target_multiplicity", ""))

        if source not in class_index:
            logger.warning("UNDEFINED_RELATIONSHIP_SOURCE: Relationship source '%s' is not defined in classes.", source)
            continue

        if target not in class_index:
            logger.warning("UNDEFINED_RELATIONSHIP_TARGET: Relationship target '%s' is not defined in classes.", target)
            continue

        cls = class_index[source]
        cls.relationships.append(ClassRelationship(
            target=target,
            source=source,
            rel_type=rel_type,
            cardinality=cardinality or target_mult,
            source_multiplicity=source_mult,
            target_multiplicity=target_mult or cardinality,
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
            requirement_ids=[str(rid) for rid in raw_seq.get("requirement_ids", []) or []],
        ))

    # ------------------------------------
    # Entities
    # ------------------------------------
    er_diagram = parsed_json.get("er_diagram", {}) or {}
    raw_entities = er_diagram.get("entities", []) or []

    entities: list[EntityIR] = []
    entity_index: dict[str, EntityIR] = {}

    raw_entity_relationships = er_diagram.get("relationships", []) or []
    entity_rel_targets: dict[str, set[str]] = {}
    for rel in raw_entity_relationships:
        s = str(rel.get("source", "")).strip()
        t = str(rel.get("target", "")).strip()
        if s and t:
            entity_rel_targets.setdefault(s, set()).add(t)
            entity_rel_targets.setdefault(t, set()).add(s)

    for raw_entity in raw_entities:
        name = str(raw_entity.get("name", "")).strip()
        if not name:
            continue

        primary_key = str(raw_entity.get("primary_key", "")).strip()
        raw_attrs = raw_entity.get("attributes", []) or []
        related_targets = entity_rel_targets.get(name, set())

        attributes: list[EntityAttribute] = []
        for attr in raw_attrs:
            attr_name = str(attr).strip()
            if not attr_name:
                continue

            # Skip redundant attributes that duplicate explicit relationships
            attr_norm = attr_name.lower().replace("_", "")
            is_redundant = False
            for target in related_targets:
                target_norm = target.lower().replace("_", "")
                if attr_norm in (target_norm, target_norm + "s", target_norm + "es", target_norm + "list", "list" + target_norm):
                    is_redundant = True
                    break
            if is_redundant and attr_name != primary_key:
                logger.info("FILTERED_REDUNDANT_ER_ATTRIBUTE: Filtered attribute '%s' from entity '%s'.", attr_name, name)
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
            requirement_ids=[str(rid) for rid in raw_entity.get("requirement_ids", []) or []],
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
        rel_name = str(rel.get("name", "")).strip()
        source_mult = str(rel.get("source_multiplicity", "")).strip()
        target_mult = str(rel.get("target_multiplicity", "")).strip()

        if source not in entity_index:
            logger.warning("UNDEFINED_ENTITY_REFERENCE: Source entity '%s' is not defined in ER diagram.", source)
            continue

        if target not in entity_index:
            logger.warning("UNDEFINED_ENTITY_REFERENCE: Target entity '%s' is not defined in ER diagram.", target)
            continue

        entity = entity_index[source]
        entity.relationships.append(EntityRelationship(
            target=target,
            name=rel_name,
            source=source,
            rel_type=rel_type,
            source_multiplicity=source_mult,
            target_multiplicity=target_mult,
        ))

    return IntermediateRepresentation(
        classes=classes,
        sequences=sequences,
        entities=entities,
    )
