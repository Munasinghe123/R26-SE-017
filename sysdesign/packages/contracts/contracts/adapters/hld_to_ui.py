from typing import List
from contracts.v1.architecture import ArchitecturePackage, Boundary
from contracts.v1.requirements import RequirementsPackage
from contracts.v1.ui import UIRequest, UIComponent


def adapt(arch: ArchitecturePackage, reqs: RequirementsPackage) -> UIRequest:
    """
    Adapt ArchitecturePackage + RequirementsPackage into UIRequest for Agent 4.
    Filters components to presentation boundary components only.
    """
    presentation_comps = [
        c for c in arch.components
        if c.boundary == Boundary.PRESENTATION or c.boundary == "presentation"
    ]

    # If no presentation component explicitly specified, fallback to all service/client components
    if not presentation_comps:
        presentation_comps = arch.components

    ui_components: List[UIComponent] = [
        UIComponent(
            name=comp.name,
            responsibilities=comp.responsibilities,
            covers_frs=comp.requirement_ids
        )
        for comp in presentation_comps
    ]

    return UIRequest(
        schema_version="1.0",
        job_id=arch.job_id,
        project_name=arch.project_name,
        domain=reqs.scope or arch.project_name,
        functional_requirements=reqs.functional_requirements,
        non_functional_requirements=reqs.non_functional_requirements,
        ui_components=ui_components,
        architecture_pattern=arch.architecture_style
    )
