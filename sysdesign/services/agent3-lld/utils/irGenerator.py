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

def generate_class_plantuml(class_diagram):

    plantuml = "@startuml\n\n"

    plantuml += "skinparam classAttributeIconSize 0\n"
    plantuml += "skinparam linetype ortho\n\n"

    # ====================================
    # CLASS DEFINITIONS
    # ====================================

    for cls in class_diagram.get("classes", []):

        class_name = _escape_name(cls.get("name"))

        if not class_name:
            continue

        plantuml += f"class {class_name} {{\n"

        # ----------------------------
        # ATTRIBUTES
        # ----------------------------

        for attr in cls.get("attributes", []):

            safe_attr = str(attr).replace('"', '\\"')
            plantuml += f"  +{safe_attr}\n"

        plantuml += "\n"

        # ----------------------------
        # METHODS
        # ----------------------------

        for method in cls.get("methods", []):

            safe_method = str(method).replace('"', '\\"')
            plantuml += f"  +{safe_method}\n"

        plantuml += "}\n\n"

    # ====================================
    # RELATIONSHIPS
    # ====================================

    for rel in class_diagram.get("relationships", []):

        source = _escape_name(rel.get("source"))
        target = _escape_name(rel.get("target"))

        if not source or not target:
            continue

        relationship_type = rel.get("type", "association")
        cardinality = rel.get("cardinality", "")

        # ----------------------------
        # RELATIONSHIP TYPES
        # ----------------------------

        if relationship_type == "inheritance":

            arrow = "<|--"

        elif relationship_type == "composition":

            arrow = "*--"

        elif relationship_type == "aggregation":

            arrow = "o--"

        elif relationship_type == "dependency":

            arrow = "..>"

        else:

            arrow = "--"

        if relationship_type == "dependency":
            plantuml += f"{source} {arrow} {target}\n"
            continue

        # ----------------------------
        # CARDINALITIES
        # ----------------------------

        left_cardinality = '"1"'
        right_cardinality = '"1"'

        if cardinality == "1..*":

            right_cardinality = '"*"'

        elif cardinality == "0..*":

            right_cardinality = '"0..*"'

        elif cardinality == "0..1":

            right_cardinality = '"0..1"'

        elif cardinality == "1":

            right_cardinality = '"1"'

        # ----------------------------
        # GENERATE RELATIONSHIP
        # ----------------------------

        plantuml += (
            f'{source} {left_cardinality} '
            f'{arrow} {right_cardinality} '
            f'{target}\n'
        )

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
    plantuml += "skinparam linetype ortho\n\n"
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

    def render_message(message, alias_lookup, indent=""):
        sender_name = str(message.get("from", "")).strip()
        receiver_name = str(message.get("to", "")).strip()
        sender = alias_lookup.get(sender_name, _escape_name(sender_name))
        receiver = alias_lookup.get(receiver_name, _escape_name(receiver_name))
        text = _message_text(message)

        if not sender or not receiver:
            return ""

        # Requirement 7: Return arrows must be determined by structured message type
        raw_type = str(message.get("type", "call")).strip().lower()
        arrow = "-->" if raw_type == "return" else "->"

        parts = [f"{indent}{sender} {arrow} {receiver}: {text}\n"]
        activates = bool(message.get("activate", message.get("activates_target", False)))
        deactivates = bool(message.get("deactivate", message.get("deactivates_target", False)))

        if activates and not deactivates:
            parts.append(f"{indent}activate {receiver}\n")
        elif deactivates and not activates:
            parts.append(f"{indent}deactivate {receiver}\n")
        elif activates and deactivates:
            parts.append(f"{indent}activate {receiver}\n")
            parts.append(f"{indent}deactivate {receiver}\n")

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
            header = f"{indent}else {condition}".rstrip()
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

        if block_type in {"alt", "loop", "opt"} and not any(str(item.get("block_type", item.get("type", ""))).strip().lower() == "else" for item in nested_blocks if isinstance(item, dict)):
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

    entities = er_diagram.get("entities", [])
    entity_aliases = set()

    for entity in entities:

        raw_name = entity.get("name", "")

        entity_name = _escape_name(raw_name)

        if not entity_name:
            continue

        alias = (
            raw_name.upper()
            .replace(" ", "_")
            .replace("-", "_")
        )

        entity_aliases.add(alias)

        plantuml += (
            f'entity "{raw_name}" '
            f'as {alias} {{\n'
        )

        # ----------------------------
        # PRIMARY KEY
        # ----------------------------

        primary_key = entity.get("primary_key")

        if primary_key:

            safe_pk = (
                str(primary_key)
                .replace('"', '\\"')
            )

            plantuml += (
                f'    {safe_pk} <<key>>\n'
            )

        # ----------------------------
        # ATTRIBUTES
        # ----------------------------

        for attr in entity.get("attributes", []):

            if attr == primary_key:
                continue

            safe_attr = (
                str(attr)
                .replace('"', '\\"')
            )

            plantuml += f"    {safe_attr}\n"

        plantuml += "}\n\n"

    # ====================================
    # RELATIONSHIPS
    # ====================================

    relationships = er_diagram.get(
        "relationships",
        []
    )

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
        # CARDINALITIES
        # ----------------------------

        source_multiplicity = str(rel.get("source_multiplicity", "")).strip()
        target_multiplicity = str(rel.get("target_multiplicity", "")).strip()

        if source_multiplicity or target_multiplicity:
            left = _to_chen_cardinality(source_multiplicity or "1")
            right = _to_chen_cardinality(target_multiplicity or "1")
        elif rel_type == "one-to-one":

            left = "1"
            right = "1"

        elif rel_type == "one-to-many":

            left = "1"
            right = "N"

        elif rel_type == "many-to-one":

            left = "N"
            right = "1"

        elif rel_type == "many-to-many":

            left = "N"
            right = "N"

        else:

            left = "1"
            right = "N"

        # ----------------------------
        # CONNECT RELATIONSHIP
        # ----------------------------

        plantuml += (
            f"{relationship_name}"
            f"-{left}- "
            f"{source}\n"
        )

        plantuml += (
            f"{relationship_name}"
            f"-{right}- "
            f"{target}\n\n"
        )

    plantuml += "@endchen"

    return plantuml
