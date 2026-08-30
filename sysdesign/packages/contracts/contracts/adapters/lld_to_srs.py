from contracts.v1.lld import LLDPackage
from contracts.v1.srs_annex import SRSDesignAnnex

def adapt(lld: LLDPackage) -> SRSDesignAnnex:
    """
    Adapt LLDPackage to SRSDesignAnnex so the SRS assembler can ingest it.
    """
    matrix = []
    for cls in lld.classes:
        matrix.append({
            "component": cls.name,
            "layer": "database_entity" if cls.stereotype == "entity" else cls.package,
            "responsibilities": f"Handles data attributes: {', '.join(a.name for a in cls.attributes)}"
        })

    return SRSDesignAnnex(
        schema_version="1.0",
        job_id=lld.job_id,
        agent="lld",
        component_responsibility_matrix=matrix,
        external_interfaces=[],
        nfr_allocation=[],
        design_constraints=[],
        quality_evidence={"consistency": lld.consistency_report.model_dump()},
        artifact_uris=lld.artifact_uris
    )
