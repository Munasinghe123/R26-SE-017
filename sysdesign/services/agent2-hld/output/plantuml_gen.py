"""
HLA Agent — PlantUML Diagram Generator
Generates .puml component diagrams from the winning architecture.
"""


def generate_plantuml(architecture: dict, title: str = "") -> str:
    """
    Generate PlantUML component diagram from architecture JSON.

    Args:
        architecture: Parsed architecture dict (winner)
        title: Optional diagram title

    Returns:
        PlantUML source string (.puml content)
    """
    style = architecture.get("architecture_style", "Architecture")
    layers = architecture.get("layers", [])
    components = architecture.get("components", [])
    connectors = architecture.get("connectors", []) or architecture.get("interactions", [])

    title = title or f"{style} Architecture"

    lines = []
    lines.append("@startuml")
    lines.append(f'title {title}')
    lines.append("")
    lines.append("skinparam componentStyle rectangle")
    lines.append("skinparam backgroundColor #FEFEFE")
    lines.append("skinparam package {")
    lines.append("  BackgroundColor #F0F4F8")
    lines.append("  BorderColor #2C3E50")
    lines.append("  FontColor #2C3E50")
    lines.append("  FontSize 14")
    lines.append("}")
    lines.append("skinparam component {")
    lines.append("  BackgroundColor #3498DB")
    lines.append("  FontColor #FFFFFF")
    lines.append("  BorderColor #2980B9")
    lines.append("}")
    lines.append("")

    # Group components by layer/boundary
    layer_components = {}
    for comp in components:
        layer = comp.get("layer", comp.get("boundary", "Default Layer"))
        if layer not in layer_components:
            layer_components[layer] = []
        layer_components[layer].append(comp)

    # Create packages for each layer
    for layer_name, comps in layer_components.items():
        alias = str(layer_name).replace(" ", "_").replace("-", "_")

        lines.append(f'package "{layer_name}" as {alias} {{')
        for comp in comps:
            comp_name = comp.get("name", "Unknown")
            comp_alias = comp_name.replace(" ", "_").replace("-", "_")
            resps = comp.get("responsibilities", [])
            resp_str = resps[0] if isinstance(resps, list) and resps else comp.get("responsibility", "")
            lines.append(f'  [{comp_name}] as {comp_alias}')
            if resp_str:
                lines.append(f'  note right of {comp_alias} : {resp_str[:60]}')
        lines.append("}")
        lines.append("")

    # Add connectors / interactions
    lines.append("' === Connectors ===")
    for conn in connectors:
        fc = (conn.get("from_component") or conn.get("from") or "").replace(" ", "_").replace("-", "_")
        tc = (conn.get("to_component") or conn.get("to") or "").replace(" ", "_").replace("-", "_")
        ctype = conn.get("connector_type") or conn.get("type") or ""
        if fc and tc:
            lines.append(f'{fc} --> {tc} : {ctype}')

    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)
