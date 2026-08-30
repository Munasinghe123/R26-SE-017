def generate_plantuml(data):

    

    plantuml = "@startuml\n\n"

    # ====================================
    # CLASS DEFINITIONS
    # ====================================

    for cls in data["classes"]:

        class_name = cls["name"]

        plantuml += f"class {class_name} {{\n"

        # ----------------------------
        # ATTRIBUTES
        # ----------------------------

        for attr in cls.get("attributes", []):

            plantuml += f"  +{attr}\n"

        plantuml += "\n"

        # ----------------------------
        # METHODS
        # ----------------------------

        for method in cls.get("methods", []):

            plantuml += f"  +{method}\n"

        plantuml += "}\n\n"

    # ====================================
    # RELATIONSHIPS
    # ====================================

    for rel in data["relationships"]:

        source = rel["source"]
        target = rel["target"]

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
        # CARDINALITY HANDLING
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

    # ====================================
    # END UML
    # ====================================

    plantuml += "\n@enduml"

    return plantuml