from typing import List, Dict
from contracts.v1.architecture import ArchitecturePackage, Boundary
from contracts.v1.requirements import RequirementsPackage
from contracts.v1.ui import UIRequest, UIComponent
from contracts.v1.lld import LLDPackage


def adapt(arch: ArchitecturePackage, reqs: RequirementsPackage, lld: LLDPackage) -> UIRequest:
    """
    Adapt ArchitecturePackage + RequirementsPackage + LLDPackage into UIRequest for Agent 4.
    Filters components to presentation boundary components only.
    Passes LLD structural information for UI data binding.
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

    # Build data dictionary from LLD entities and classes
    data_dictionary: List[dict] = []
    for ent in lld.entities:
        data_dictionary.append({
            "type": "database_entity",
            "name": ent.name,
            "fields": [{"name": c.name, "type": c.type} for c in ent.columns]
        })
    for cls in lld.classes:
        data_dictionary.append({
            "type": "domain_class",
            "name": cls.name,
            "fields": [{"name": a.name, "type": a.type} for a in cls.attributes]
        })

    # Build API contracts from LLD sequences
    api_contracts: List[dict] = []
    for seq in lld.sequences:
        api_contracts.append({
            "use_case": seq.use_case,
            "name": seq.name,
            "messages": [{"from": m.from_actor, "to": m.to_actor, "message": m.message} for m in seq.messages]
        })

    # Build design artifacts dictionary for UI generator
    design_artifacts = {
        "class_diagram": {
            "classes": [
                {
                    "name": cls.name,
                    "attributes": [a.name for a in cls.attributes],
                    "methods": [f"{m.name}({', '.join(m.params or [])})" for m in cls.methods]
                }
                for cls in lld.classes
            ]
        },
        "er_diagram": {
            "entities": [
                {
                    "name": ent.name,
                    "attributes": [
                        {
                            "name": c.name,
                            "type": c.type,
                            "key": "PK" if c.pk else ("FK" if c.fk else "")
                        }
                        for c in ent.columns
                    ]
                }
                for ent in lld.entities
            ]
        },
        "sequence_diagram": {
            "scenario": lld.sequences[0].use_case if lld.sequences else "Main Scenario",
            "actors": lld.sequences[0].participants if lld.sequences else [],
            "messages": [
                {
                    "from": m.from_actor,
                    "to": m.to_actor,
                    "action": m.message
                }
                for seq in lld.sequences for m in seq.messages
            ] if lld.sequences else []
        }
    }

    return UIRequest(
        schema_version="1.0",
        job_id=arch.job_id,
        project_name=arch.project_name,
        domain=reqs.scope or arch.project_name,
        functional_requirements=reqs.functional_requirements,
        non_functional_requirements=reqs.non_functional_requirements,
        ui_components=ui_components,
        architecture_pattern=arch.architecture_style,
        data_dictionary=data_dictionary,
        api_contracts=api_contracts,
        design_artifacts=design_artifacts,
    )

