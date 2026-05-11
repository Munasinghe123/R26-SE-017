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

            arrow = "<.."

        else:

            arrow = "--"

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

    diagram_name = sequence_diagram.get(
        "name",
        "Sequence Diagram"
    )

    plantuml = "@startuml\n\n"

    plantuml += "skinparam linetype ortho\n\n"

    plantuml += f"title {diagram_name}\n\n"

    # ====================================
    # PARTICIPANTS
    # ====================================

    participants = sequence_diagram.get(
        "participants",
        []
    )

    for participant in participants:

        safe_participant = _escape_name(participant)

        if safe_participant:
            plantuml += f"participant {safe_participant}\n"

    plantuml += "\n"

    # ====================================
    # MESSAGES
    # ====================================

    messages = sequence_diagram.get(
        "messages",
        []
    )

    for message in messages:

        sender = _escape_name(
            message.get("from", "")
        )

        receiver = _escape_name(
            message.get("to", "")
        )

        text = str(
            message.get("message", "")
        ).replace('"', '\\"')

        if sender and receiver:

            plantuml += (
                f"{sender} -> {receiver}: {text}\n"
            )

    plantuml += "\n@enduml"

    return plantuml


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

        rel_type = rel.get(
            "type",
            "one-to-many"
        )

        # ----------------------------
        # CREATE RELATIONSHIP ENTITY
        # ----------------------------

        relationship_name = (
            f"REL_{index}"
        )

        plantuml += (
            f'relationship "{rel_type}" '
            f'as {relationship_name} {{\n'
            f'}}\n\n'
        )

        # ----------------------------
        # CARDINALITIES
        # ----------------------------

        if rel_type == "one-to-one":

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