import re


# ====================================
# SAFE NAME ESCAPING
# ====================================

def _escape_name(name):

    if name is None:
        return ""

    name = str(name).strip()

    if not name:
        return ""

    # Escape quotes
    escaped = name.replace('"', '\\"')

    # Wrap if contains special chars/spaces
    if any(ch in escaped for ch in [" ", "-", ".", "/", ":", "(", ")"]):
        return f'"{escaped}"'

    return escaped


def _to_chen_cardinality(value):
    cardinality = str(value).strip()
    mapping = {
        "1": "1",
        "0..1": "(0,1)",
        "0..*": "(0,N)",
        "1..*": "(1,N)",
        "N": "N",
    }

    if cardinality in mapping:
        return mapping[cardinality]

    raise ValueError(
        f"Unsupported ER multiplicity for Chen PlantUML rendering: {value!r}"
    )


# ====================================
# CLASS DIAGRAM GENERATOR
# ====================================

def _format_class_method(method):
    if not method:
        return ""
    if hasattr(method, "name"):
        name = getattr(method, "name", "")
        params = []
        for p in getattr(method, "parameters", []) or []:
            p_name = getattr(p, "name", str(p))
            p_type = getattr(p, "data_type", "")
            if p_type:
                params.append(f"{p_name}: {p_type}")
            else:
                params.append(p_name)
        params_str = ", ".join(params)
        ret_type = getattr(method, "return_type", "void") or "void"
        vis_val = getattr(method, "visibility", "+")
        if hasattr(vis_val, "value"):
            vis_val = vis_val.value
        vis_map = {"public": "+", "private": "-", "protected": "#", "package": "~", "+": "+", "-": "-", "#": "#", "~": "~"}
        vis = vis_map.get(str(vis_val).lower(), "+")
        return f"{vis}{name}({params_str}): {ret_type}"
    elif isinstance(method, dict):
        name = str(method.get("name", "")).strip()
        params = []
        for p in method.get("parameters", method.get("params", [])) or []:
            if isinstance(p, dict):
                p_name = str(p.get("name", "")).strip()
                p_type = str(p.get("data_type", p.get("type", ""))).strip()
                if p_type:
                    params.append(f"{p_name}: {p_type}")
                elif p_name:
                    params.append(p_name)
            else:
                params.append(str(p).strip())
        params_str = ", ".join(params)
        ret_type = str(method.get("return_type", method.get("returns", "void"))).strip() or "void"
        vis_val = str(method.get("visibility", "+")).strip().lower()
        vis_map = {"public": "+", "private": "-", "protected": "#", "package": "~", "+": "+", "-": "-", "#": "#", "~": "~"}
        vis = vis_map.get(vis_val, "+")
        return f"{vis}{name}({params_str}): {ret_type}"
    else:
        s = str(method).strip()
        if not s:
            return ""
        if s[0] in ("+", "-", "#", "~"):
            return s
        return f"+{s}"


# ====================================
# CLASS DIAGRAM GENERATOR
# ====================================

def generate_class_plantuml(class_diagram):

    plantuml = "@startuml\n\n"

    plantuml += "skinparam classAttributeIconSize 0\n"
    plantuml += "skinparam linetype ortho\n\n"

    # ====================================
    # CLASS DEFINITIONS
    # ====================================

    classes = class_diagram.get("classes", []) if isinstance(class_diagram, dict) else getattr(class_diagram, "classes", [])

    for cls in classes:

        class_name = _escape_name(cls.get("name") if isinstance(cls, dict) else getattr(cls, "name", ""))

        if not class_name:
            continue

        plantuml += f"class {class_name} {{\n"

        # ----------------------------
        # ATTRIBUTES
        # ----------------------------

        attributes = cls.get("attributes", []) if isinstance(cls, dict) else getattr(cls, "attributes", [])
        for attr in attributes:

            safe_attr = str(attr).replace('"', '\\"')
            plantuml += f"  +{safe_attr}\n"

        plantuml += "\n"

        # ----------------------------
        # METHODS
        # ----------------------------

        methods = cls.get("methods", []) if isinstance(cls, dict) else getattr(cls, "methods", [])
        for method in methods:

            formatted = _format_class_method(method)
            if formatted:
                safe_method = formatted.replace('"', '\\"')
                plantuml += f"  {safe_method}\n"

        plantuml += "}\n\n"

    # ====================================
    # RELATIONSHIPS
    # ====================================

    relationships = class_diagram.get("relationships", []) if isinstance(class_diagram, dict) else getattr(class_diagram, "relationships", [])

    for rel in relationships:

        source = _escape_name(rel.get("source") if isinstance(rel, dict) else getattr(rel, "source", getattr(rel, "source_class", "")))
        target = _escape_name(rel.get("target") if isinstance(rel, dict) else getattr(rel, "target", getattr(rel, "target_class", "")))

        if not source or not target:
            continue

        raw_rel_type = rel.get("type", rel.get("rel_type", "association")) if isinstance(rel, dict) else getattr(rel, "rel_type", getattr(rel, "type", "association"))
        if hasattr(raw_rel_type, "value"):
            raw_rel_type = raw_rel_type.value
        relationship_type = str(raw_rel_type).lower().strip()

        source_mult = str(rel.get("source_multiplicity", "") if isinstance(rel, dict) else getattr(rel, "source_multiplicity", "")).strip()
        target_mult = str((rel.get("target_multiplicity", "") or rel.get("cardinality", "")) if isinstance(rel, dict) else (getattr(rel, "target_multiplicity", "") or getattr(rel, "cardinality", ""))).strip()

        # ----------------------------
        # RELATIONSHIP TYPES & SEMANTICS
        # ----------------------------

        ownership = str(rel.get("ownership", "") if isinstance(rel, dict) else getattr(rel, "ownership", "")).strip().lower()
        owner = str(rel.get("owner", rel.get("whole", "")) if isinstance(rel, dict) else getattr(rel, "owner", getattr(rel, "whole", ""))).strip()
        is_target_owner = ownership == "target" or owner == target

        if relationship_type == "inheritance":

            parent = str(rel.get("parent", rel.get("superclass", "")) if isinstance(rel, dict) else getattr(rel, "parent", getattr(rel, "superclass", ""))).strip()
            direction = str(rel.get("direction", "") if isinstance(rel, dict) else getattr(rel, "direction", "")).strip().lower()
            if parent == target or direction in ("child_to_parent", "source_to_target"):
                arrow = "--|>"
            elif parent == source or direction in ("parent_to_child", "target_to_source"):
                arrow = "<|--"
            else:
                arrow = "--|>"

            plantuml += f"{source} {arrow} {target}\n"
            continue

        elif relationship_type == "composition":

            arrow = "--*" if is_target_owner else "*--"

        elif relationship_type == "aggregation":

            arrow = "--o" if is_target_owner else "o--"

        elif relationship_type == "dependency":

            arrow = "..>"
            plantuml += f"{source} {arrow} {target}\n"
            continue

        else:

            arrow = "--"

        # ----------------------------
        # CARDINALITIES (Preserve 1..*, do not invent '1' if omitted)
        # ----------------------------

        left_cardinality = f'"{source_mult}" ' if source_mult else ""
        right_cardinality = f' "{target_mult}"' if target_mult else ""

        # ----------------------------
        # GENERATE RELATIONSHIP
        # ----------------------------

        plantuml += f"{source} {left_cardinality}{arrow}{right_cardinality} {target}\n"

    plantuml += "\n@enduml"

    return plantuml


# ====================================
# SEQUENCE DIAGRAM GENERATOR
# ====================================

def generate_sequence_plantuml(sequence_diagram):
    from utils.sequence_normalizer import normalize_sequence_diagram, ROLE_TO_PLANTUML

    # 1. Normalize sequence data first
    sequence_diagram = normalize_sequence_diagram(sequence_diagram)

    diagram_name = sequence_diagram.get(
        "name",
        "Sequence Diagram"
    )

    plantuml = "@startuml\n\n"
    plantuml += "hide footbox\n\n"
    plantuml += f"title {diagram_name}\n\n"

    def _participant_type_name(value):
        if hasattr(value, "value"):
            value = value.value
        normalized = str(value).strip().lower()
        return ROLE_TO_PLANTUML.get(normalized, "participant")

    def _sequence_participant_alias(participant_name, used_aliases):
        alias = re.sub(r"[^A-Za-z0-9_]+", "", str(participant_name))
        if not alias:
            alias = "Participant"
        if alias[0].isdigit():
            alias = f"P{alias}"
        base_alias = alias
        suffix = 2
        while alias in used_aliases:
            alias = f"{base_alias}{suffix}"
            suffix += 1
        used_aliases.add(alias)
        return alias

    def _message_text(message):
        return str(message.get("message", "")).replace('"', '\\"')

    # Track active participant lifelines to avoid unmatched/inappropriate deactivations
    active_counts = {}

    def render_message(message, alias_lookup, indent=""):
        sender_name = str(message.get("from", "")).strip()
        receiver_name = str(message.get("to", "")).strip()
        sender = alias_lookup.get(sender_name, _escape_name(sender_name))
        receiver = alias_lookup.get(receiver_name, _escape_name(receiver_name))
        text = _message_text(message)

        if not sender or not receiver:
            return ""

        raw_type = message.get("type", "call")
        if hasattr(raw_type, "value"):
            raw_type = raw_type.value
        raw_type = str(raw_type).strip().lower()
        arrow = "-->" if raw_type == "return" else "->"

        parts = [f"{indent}{sender} {arrow} {receiver}: {text}\n"]
        activates = bool(message.get("activate", message.get("activates_target", False)))
        deactivates = bool(message.get("deactivate", message.get("deactivates_target", False)))

        # Lifecycle management:
        # Calls activate the receiver (target)
        # Returns deactivate the sender (the participant whose execution is completing)
        if raw_type == "call":
            if activates and not deactivates:
                parts.append(f"{indent}activate {receiver}\n")
                active_counts[receiver] = active_counts.get(receiver, 0) + 1
            elif activates and deactivates:
                # Immediate self-call or transient activation
                parts.append(f"{indent}activate {receiver}\n")
                parts.append(f"{indent}deactivate {receiver}\n")
            elif deactivates and not activates:
                # Target deactivation on call only if active
                if active_counts.get(receiver, 0) > 0:
                    parts.append(f"{indent}deactivate {receiver}\n")
                    active_counts[receiver] -= 1
        elif raw_type == "return":
            # On return message, sender execution is ending. Never deactivate response receiver!
            # Never deactivate a lifeline that was not activated!
            if active_counts.get(sender, 0) > 0:
                parts.append(f"{indent}deactivate {sender}\n")
                active_counts[sender] -= 1

        return "".join(parts)

    def render_logic_block(block, alias_lookup, indent=""):
        block_type_value = block.get("block_type", block.get("type", "alt"))
        if hasattr(block_type_value, "value"):
            block_type_value = block_type_value.value
        block_type = str(block_type_value).strip().lower()
        condition = str(block.get("condition", "")).strip()
        messages = block.get("messages", []) or []
        nested_blocks = block.get("logic_blocks", []) or []

        if block_type == "else":
            header = f"{indent}else [{condition}]".rstrip() if condition else f"{indent}else"
        elif block_type == "end":
            header = f"{indent}end"
        elif block_type == "loop":
            header = f"{indent}loop [{condition}]".rstrip() if condition else f"{indent}loop"
        elif block_type == "opt":
            header = f"{indent}opt [{condition}]".rstrip() if condition else f"{indent}opt"
        else:
            header = f"{indent}alt [{condition}]".rstrip() if condition else f"{indent}alt"

        rendered = [f"{header}\n"]

        # Render items inside block in exact order
        block_items = block.get("items", []) or []
        if block_items:
            for item in block_items:
                if isinstance(item, dict):
                    if "block_type" in item or ("type" in item and str(item.get("type")).lower() in {"loop", "alt", "opt", "else"}):
                        rendered.append(render_logic_block(item, alias_lookup, indent=indent + "  "))
                    else:
                        rendered.append(render_message(item, alias_lookup, indent=indent + "  "))
        else:
            for message in messages:
                if isinstance(message, dict):
                    rendered.append(render_message(message, alias_lookup, indent=indent + "  "))

            for nested_block in nested_blocks:
                if isinstance(nested_block, dict):
                    rendered.append(render_logic_block(nested_block, alias_lookup, indent=indent + "  "))

        # Every alt, loop, or opt block MUST be closed with end
        if block_type in {"alt", "loop", "opt"}:
            rendered.append(f"{indent}end\n")

        return "".join(rendered)

    # ====================================
    # PARTICIPANTS
    # ====================================

    participants = sequence_diagram.get(
        "participants",
        []
    )
    participant_types = sequence_diagram.get("participant_types", {}) or {}
    used_aliases = set()
    alias_lookup = {}

    for participant in participants:
        safe_participant = _escape_name(participant)
        participant_type = _participant_type_name(participant_types.get(participant, "participant"))
        alias = _sequence_participant_alias(participant, used_aliases)
        alias_lookup[str(participant)] = alias

        if safe_participant:
            if participant_type == "participant":
                plantuml += f"participant \"{participant}\" as {alias}\n"
            else:
                plantuml += f"{participant_type} \"{participant}\" as {alias}\n"

    plantuml += "\n"

    # ====================================
    # MESSAGES & LOGIC BLOCKS (CAUSAL ORDER)
    # ====================================

    raw_items = sequence_diagram.get("items", sequence_diagram.get("interactions", [])) or []

    if raw_items:
        for item in raw_items:
            if isinstance(item, dict):
                if "block_type" in item or ("type" in item and str(item.get("type")).lower() in {"loop", "alt", "opt", "else"}):
                    plantuml += render_logic_block(item, alias_lookup)
                else:
                    plantuml += render_message(item, alias_lookup)
    else:
        # Fallback: render top-level messages first, then logic blocks
        messages = sequence_diagram.get("messages", []) or []
        for message in messages:
            if isinstance(message, dict):
                plantuml += render_message(message, alias_lookup)

        logic_blocks = sequence_diagram.get("logic_blocks", []) or []
        for block in logic_blocks:
            if isinstance(block, dict):
                plantuml += render_logic_block(block, alias_lookup)

    # Close any unclosed activations to ensure balanced PlantUML rendering
    for participant_alias, count in list(active_counts.items()):
        while count > 0:
            plantuml += f"deactivate {participant_alias}\n"
            count -= 1

    plantuml += "\n@enduml"

    return plantuml


INVALID_RELATIONSHIP_NAMES = {
    "one-to-one", "one_to_one", "1:1",
    "one-to-many", "one_to_many", "1:n", "1:m", "1..*", "0..*",
    "many-to-one", "many_to_one", "n:1", "m:1",
    "many-to-many", "many_to_many", "n:m", "m:n",
    "has-many", "has_many", "has-one", "has_one",
    "1", "0..1", "n", "m", "many"
}


def is_invalid_relationship_name(name: str | None) -> bool:
    if not name:
        return True
    cleaned = str(name).strip().lower().replace(" ", "-")
    return cleaned in INVALID_RELATIONSHIP_NAMES or cleaned.replace("-", "_") in INVALID_RELATIONSHIP_NAMES


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


# ====================================
# ER DIAGRAM GENERATOR (CHEN STYLE)
# ====================================

def generate_er_plantuml(er_diagram):

    plantuml = "@startchen\n\n"

    # ====================================
    # STYLE
    # ====================================

    plantuml += "<style>\n"

    plantuml += "entity {\n"
    plantuml += "    BackgroundColor White\n"
    plantuml += "    BorderColor Black\n"
    plantuml += "}\n"

    plantuml += "relationship {\n"
    plantuml += "    BackgroundColor LightBlue\n"
    plantuml += "    BorderColor Black\n"
    plantuml += "}\n"

    plantuml += "</style>\n\n"

    # ====================================
    # ENTITIES
    # ====================================

    # Collect relationships upfront to identify redundant collection attributes
    if hasattr(er_diagram, "entities"):
        all_relationships = []
        for ent in getattr(er_diagram, "entities", []) or []:
            for rel in getattr(ent, "relationships", []) or []:
                all_relationships.append({
                    "source": getattr(rel, "source", ent.name),
                    "target": getattr(rel, "target", ""),
                })
    elif isinstance(er_diagram, dict):
        all_relationships = er_diagram.get("relationships", []) or []
    else:
        all_relationships = getattr(er_diagram, "relationships", []) or []

    entity_targets_map: dict[str, set[str]] = {}
    for r in all_relationships:
        if isinstance(r, dict):
            s = str(r.get("source", "")).strip()
            t = str(r.get("target", "")).strip()
            if s and t:
                entity_targets_map.setdefault(s, set()).add(t)
                entity_targets_map.setdefault(t, set()).add(s)

    if hasattr(er_diagram, "entities"):
        entities = getattr(er_diagram, "entities", []) or []
    elif isinstance(er_diagram, dict):
        entities = er_diagram.get("entities", []) or []
    else:
        entities = []
    entity_aliases = set()

    for entity in entities:

        raw_name = entity.get("name", "") if isinstance(entity, dict) else getattr(entity, "name", "")
        raw_name_clean = str(raw_name).strip()

        if not raw_name_clean:
            continue

        if is_architectural_component(raw_name_clean):
            continue

        entity_name = _escape_name(raw_name_clean)

        alias = (
            raw_name_clean.upper()
            .replace(" ", "_")
            .replace("-", "_")
        )

        entity_aliases.add(alias)

        plantuml += (
            f'entity "{raw_name_clean}" '
            f'as {alias} {{\n'
        )

        # ----------------------------
        # PRIMARY KEY
        # ----------------------------

        attributes = entity.get("attributes", []) if isinstance(entity, dict) else getattr(entity, "attributes", [])
        primary_key = str(entity.get("primary_key", "") if isinstance(entity, dict) else getattr(entity, "primary_key", "")).strip()

        if not primary_key:
            for attr in attributes:
                constraint = attr.get("constraint", "") if isinstance(attr, dict) else getattr(attr, "constraint", "")
                if constraint == "PK":
                    primary_key = attr.get("name", "") if isinstance(attr, dict) else getattr(attr, "name", str(attr))
                    break

        if primary_key:
            safe_pk = primary_key.replace('"', '\\"')
            plantuml += f'    {safe_pk} <<key>>\n'

        # ----------------------------
        # ATTRIBUTES
        # ----------------------------

        for attr in attributes:

            attr_name = str(getattr(attr, "name", attr.get("name", str(attr)) if isinstance(attr, dict) else str(attr))).strip()
            if not attr_name or attr_name == primary_key:
                continue

            # Skip redundant attributes that duplicate explicit relationships
            attr_norm = attr_name.lower().replace("_", "")
            is_redundant = False
            for target_name in entity_targets_map.get(raw_name_clean, set()):
                target_norm = target_name.lower().replace("_", "")
                if attr_norm in (target_norm, target_norm + "s", target_norm + "es", target_norm + "list", "list" + target_norm):
                    is_redundant = True
                    break
            if is_redundant:
                continue

            safe_attr = attr_name.replace('"', '\\"')
            plantuml += f"    {safe_attr}\n"

        plantuml += "}\n\n"

    # ====================================
    # RELATIONSHIPS
    # ====================================

    if hasattr(er_diagram, "entities"):
        relationships = []
        for ent in er_diagram.entities:
            for rel in getattr(ent, "relationships", []):
                relationships.append({
                    "source": getattr(rel, "source", ent.name),
                    "target": getattr(rel, "target", ""),
                    "name": getattr(rel, "name", ""),
                    "type": getattr(rel, "rel_type", "one-to-many"),
                    "source_multiplicity": getattr(rel, "source_multiplicity", ""),
                    "target_multiplicity": getattr(rel, "target_multiplicity", ""),
                })
    elif isinstance(er_diagram, dict):
        relationships = er_diagram.get("relationships", []) or []
    else:
        relationships = getattr(er_diagram, "relationships", []) or []

    for index, rel in enumerate(relationships):

        source_raw = rel.get("source", "")
        target_raw = rel.get("target", "")

        source = (
            source_raw.upper()
            .replace(" ", "_")
            .replace("-", "_")
        )

        target = (
            target_raw.upper()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if not source or not target:
            continue

        if source not in entity_aliases or target not in entity_aliases:
            continue

        rel_type = rel.get("type", "one-to-many")
        rel_name = str(rel.get("name", "")).strip()

        if not is_invalid_relationship_name(rel_name):
            semantic_name = rel_name
        else:
            semantic_name = "RELATIONSHIP"

        # ----------------------------
        # CREATE RELATIONSHIP ENTITY
        # ----------------------------

        relationship_name = (
            f"REL_{index}"
        )

        plantuml += (
            f'relationship "{semantic_name}" '
            f'as {relationship_name} {{\n'
            f'}}\n\n'
        )

        # ----------------------------
        # CARDINALITIES (Preserve 1..* as (1,N), do not invent missing multiplicities)
        # ----------------------------

        source_multiplicity = str(rel.get("source_multiplicity", "")).strip()
        target_multiplicity = str(rel.get("target_multiplicity", "")).strip()
        cardinality = str(rel.get("cardinality", "")).strip()
        if not target_multiplicity and cardinality:
            target_multiplicity = cardinality

        left = _to_chen_cardinality(source_multiplicity) if source_multiplicity else ""
        right = _to_chen_cardinality(target_multiplicity) if target_multiplicity else ""

        # ----------------------------
        # CONNECT RELATIONSHIP
        # ----------------------------

        if left:
            plantuml += (
                f"{relationship_name}"
                f"-{left}- "
                f"{source}\n"
            )
        else:
            plantuml += (
                f"{relationship_name}"
                f"-- "
                f"{source}\n"
            )

        if right:
            plantuml += (
                f"{relationship_name}"
                f"-{right}- "
                f"{target}\n\n"
            )
        else:
            plantuml += (
                f"{relationship_name}"
                f"-- "
                f"{target}\n\n"
            )

    plantuml += "@endchen"

    return plantuml
