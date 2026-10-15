def _format_method(method):
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


def generate_plantuml(data):

    plantuml = "@startuml\n\n"

    # ====================================
    # CLASS DEFINITIONS
    # ====================================

    for cls in data.get("classes", []):

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

            formatted = _format_method(method)
            if formatted:
                plantuml += f"  {formatted}\n"

        plantuml += "}\n\n"

    # ====================================
    # RELATIONSHIPS
    # ====================================

    for rel in data.get("relationships", []):

        source = rel["source"]
        target = rel["target"]

        relationship_type = str(rel.get("type", "association")).lower().strip()

        source_mult = str(rel.get("source_multiplicity", "")).strip()
        target_mult = str(rel.get("target_multiplicity", "") or rel.get("cardinality", "")).strip()

        ownership = str(rel.get("ownership", "")).strip().lower()
        owner = str(rel.get("owner", rel.get("whole", ""))).strip()
        is_target_owner = ownership == "target" or owner == target

        # ----------------------------
        # RELATIONSHIP TYPES
        # ----------------------------

        if relationship_type == "inheritance":

            parent = str(rel.get("parent", rel.get("superclass", ""))).strip()
            direction = str(rel.get("direction", "")).strip().lower()
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
        # CARDINALITY HANDLING
        # ----------------------------

        left_cardinality = f'"{source_mult}" ' if source_mult else ""
        right_cardinality = f' "{target_mult}"' if target_mult else ""

        # ----------------------------
        # GENERATE RELATIONSHIP
        # ----------------------------

        plantuml += f"{source} {left_cardinality}{arrow}{right_cardinality} {target}\n"

    # ====================================
    # END UML
    # ====================================

    plantuml += "\n@enduml"

    return plantuml