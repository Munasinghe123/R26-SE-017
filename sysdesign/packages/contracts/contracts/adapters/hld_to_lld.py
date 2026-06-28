from typing import List, Dict
from contracts.v1.architecture import ArchitecturePackage, Boundary
from contracts.v1.requirements import RequirementsPackage
from contracts.v1.lld import LLDRequest, HighLevelArchitecture, ArchitecturalLayer


def _build_constraints(arch: ArchitecturePackage) -> List[str]:
    constraints: List[str] = []
    for comp in arch.components:
        if comp.provided_interfaces:
            constraints.append(f"{comp.name} exposes interfaces: {', '.join(comp.provided_interfaces)}")
        if comp.required_interfaces:
            constraints.append(f"{comp.name} requires interfaces: {', '.join(comp.required_interfaces)}")

    for conn in arch.connectors:
        protocol_info = f" via {conn.protocol}" if conn.protocol else ""
        constraints.append(f"{conn.from_component} communicates with {conn.to_component} ({conn.connector_type}{protocol_info})")

    for qp in arch.quality_provisions:
        constraints.append(f"Quality [{qp.nfr_id}] ({qp.iso_characteristic}) handled by {qp.responsible_component}: {qp.mechanism}")

    return constraints


def adapt(arch: ArchitecturePackage, reqs: RequirementsPackage) -> LLDRequest:
    """
    Adapt ArchitecturePackage + RequirementsPackage into LLDRequest for Agent 3.
    Groups components by boundary and injects interfaces/connectors as constraints.
    """
    boundary_map: Dict[str, List[str]] = {}
    for comp in arch.components:
        boundary_name = comp.boundary.value if isinstance(comp.boundary, Boundary) else str(comp.boundary)
        boundary_map.setdefault(boundary_name, []).append(comp.name)

    layers: List[ArchitecturalLayer] = [
        ArchitecturalLayer(
            name=b_name.replace("_", " ").title(),
            description=f"Components belonging to the {b_name} boundary.",
            components=comp_list
        )
        for b_name, comp_list in boundary_map.items()
    ]

    hla = HighLevelArchitecture(
        pattern=arch.architecture_style,
        layers=layers,
        architectural_constraints=_build_constraints(arch)
    )

    return LLDRequest(
        schema_version="1.0",
        job_id=arch.job_id,
        project_name=arch.project_name,
        project_description=reqs.purpose or f"Architecture for {arch.project_name}",
        high_level_architecture=hla,
        functional_requirements=reqs.functional_requirements,
        export_formats=["png", "puml"]
    )
