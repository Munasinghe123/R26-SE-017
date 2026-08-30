from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

app = FastAPI(title="SRS Assembler Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "service": "srs-assembler", "schema": "1.0"}


@app.post("/run")
def run(payload: Dict[str, Any]):
    """
    Assembles complete IEEE 29148 Software Requirements Specification (SRS)
    from requirements package + 3 design annexes (HLD, LLD, UI).
    """
    try:
        reqs = payload.get("requirements", {})
        hld_annex = payload.get("hld_annex", {})
        lld_annex = payload.get("lld_annex", {})
        ui_annex = payload.get("ui_annex", {})

        project_name = reqs.get("project_name", "Software System")
        job_id = reqs.get("job_id", "job-dev")

        md_lines = []
        md_lines.append(f"# System Requirements Specification (IEEE 29148 Standard)")
        md_lines.append(f"## Project: {project_name}")
        md_lines.append(f"**Job ID:** `{job_id}`\n")

        md_lines.append("### 1. Functional Requirements")
        for fr in reqs.get("functional_requirements", []):
            md_lines.append(f"- **[{fr.get('id')}] {fr.get('title')}**: {fr.get('description')}")

        md_lines.append("\n### 2. Non-Functional Requirements (ISO/IEC 25010)")
        for nfr in reqs.get("non_functional_requirements", []):
            md_lines.append(f"- **[{nfr.get('id')}] ({nfr.get('iso_characteristic')})**: {nfr.get('description')}")

        md_lines.append("\n### 3. High-Level Architecture (Agent 2 - Quality Gate)")
        hld_matrix = hld_annex.get("component_responsibility_matrix", [])
        if hld_matrix:
            md_lines.append("| Component | Boundary | Responsibility |")
            md_lines.append("|---|---|---|")
            for row in hld_matrix:
                md_lines.append(f"| {row.get('component')} | {row.get('layer')} | {row.get('responsibilities')} |")

        scores = hld_annex.get("quality_evidence", {})
        if scores:
            md_lines.append(f"\n**Composite Architecture Score (CAS):** `{scores.get('CAS', 'N/A')}`")
            md_lines.append(f"- RTS (Requirement Traceability): `{scores.get('RTS', 'N/A')}`")
            md_lines.append(f"- QAC (Quality Attribute Coverage): `{scores.get('QAC', 'N/A')}`")
            md_lines.append(f"- CI (Coupling Index): `{scores.get('CI', 'N/A')}`")
            md_lines.append(f"- CoS (Cohesion Score): `{scores.get('CoS', 'N/A')}`")

        md_lines.append("\n### 4. Low-Level Design Annex (Agent 3)")
        lld_matrix = lld_annex.get("component_responsibility_matrix", [])
        if lld_matrix:
            md_lines.append(f"Generated `{len(lld_matrix)}` detailed design components.")
        for k, uri in lld_annex.get("artifact_uris", {}).items():
            md_lines.append(f"- Diagram `{k}`: {uri}")

        md_lines.append("\n### 5. User Interface & Usability Annex (Agent 4)")
        ui_matrix = ui_annex.get("component_responsibility_matrix", [])
        if ui_matrix:
            md_lines.append(f"Planned `{len(ui_matrix)}` UI screen components.")
        for k, uri in ui_annex.get("artifact_uris", {}).items():
            md_lines.append(f"- Screen `{k}`: {uri}")

        document_content = "\n".join(md_lines)

        return {
            "status": "success",
            "job_id": job_id,
            "project_name": project_name,
            "srs_markdown": document_content,
            "summary": f"IEEE 29148 SRS assembled with {len(reqs.get('functional_requirements', []))} FRs and 3 design annexes."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SRS Assembly failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=False)
