from __future__ import annotations

import os
from Services.umlService import UMLService
from schemas.umlSchema import GenerateRequest


def _build_requirements_text(request: GenerateRequest) -> tuple[str, list[str]]:
    lines: list[str] = []
    requirement_ids: list[str] = []

    project_name = request.project_name.strip() or "Untitled Project"
    lines.append(f"Project Name: {project_name}")

    if request.project_description.strip():
        lines.append(f"Project Description: {request.project_description.strip()}")

    architecture = request.high_level_architecture
    if architecture.pattern.strip():
        lines.append(f"Architecture Pattern: {architecture.pattern.strip()}")

    if architecture.layers:
        lines.append("Architecture Layers:")
        for layer in architecture.layers:
            name = layer.name.strip() or "Layer"
            lines.append(f"- {name}")
            if layer.description.strip():
                lines.append(f"  Description: {layer.description.strip()}")
            if layer.components:
                components = ", ".join([c.strip() for c in layer.components if c.strip()])
                if components:
                    lines.append(f"  Components: {components}")

    if architecture.architectural_constraints:
        constraints = ", ".join([c.strip() for c in architecture.architectural_constraints if c.strip()])
        if constraints:
            lines.append(f"Architectural Constraints: {constraints}")

    if request.functional_requirements:
        lines.append("Functional Requirements:")
        for index, req in enumerate(request.functional_requirements, start=1):
            req_id = req.id.strip() or f"FR-{index}"
            requirement_ids.append(req_id)
            title = req.title.strip() or "Requirement"
            lines.append(f"- [{req_id}] {title}")
            if req.description.strip():
                lines.append(f"  Description: {req.description.strip()}")

    return "\n".join(lines).strip(), requirement_ids


def _upper_severity(errors: list[dict]) -> list[dict]:
    updated: list[dict] = []
    for err in errors:
        if not isinstance(err, dict):
            continue
        severity = str(err.get("severity", "")).upper()
        updated.append({
            **err,
            "severity": severity,
        })
    return updated


def _flatten_exported_files(files: dict) -> list[str]:
    exported: list[str] = []
    if not isinstance(files, dict):
        return exported

    class_file = files.get("class")
    if class_file:
        exported.append(class_file)

    for seq_file in files.get("sequence", []) or []:
        if seq_file:
            exported.append(seq_file)

    er_file = files.get("er")
    if er_file:
        exported.append(er_file)

    return exported


def _build_diagram_outputs(service_result: dict) -> list[dict]:
    diagrams: list[dict] = []

    plantuml = service_result.get("plantuml", {}) or {}
    pngs = service_result.get("pngs", {}) or {}

    class_plantuml = plantuml.get("class", "")
    class_png = pngs.get("class", "")
    if class_plantuml or class_png:
        diagrams.append({
            "diagram_type": "Class",
            "plantuml_syntax": class_plantuml or "",
            "mermaid_syntax": "",
            "name": "Class Diagram",
            "png_base64": class_png or "",
            "svg_content": "",
        })

    seq_plantuml = plantuml.get("sequence", []) or []
    seq_pngs = pngs.get("sequence", []) or []
    for index, seq in enumerate(seq_plantuml):
        seq_png = seq_pngs[index]["png"] if index < len(seq_pngs) else ""
        diagrams.append({
            "diagram_type": "Sequence",
            "plantuml_syntax": seq.get("plantuml", ""),
            "mermaid_syntax": "",
            "name": seq.get("name", f"Sequence {index + 1}"),
            "png_base64": seq_png or "",
            "svg_content": "",
        })

    er_plantuml = plantuml.get("er", "")
    er_png = pngs.get("er", "")
    if er_plantuml or er_png:
        diagrams.append({
            "diagram_type": "ER",
            "plantuml_syntax": er_plantuml or "",
            "mermaid_syntax": "",
            "name": "ER Diagram",
            "png_base64": er_png or "",
            "svg_content": "",
        })

    return diagrams


class UMLController:

    @staticmethod
    def generate(request: GenerateRequest):
        requirements_text, requirement_ids = _build_requirements_text(request)
        result = UMLService.generate_uml(
            requirements_text,
            requirement_ids=requirement_ids,
        )
        print(f"[LLD-Controller] Generation complete for project '{request.project_name or 'Untitled'}'!")
        validation_report = result.get("validation") or {}
        validation_report["errors"] = _upper_severity(validation_report.get("errors", []))
        validation_report["iteration"] = result.get("iterations_used", 1)

        project_name = request.project_name.strip() or "Untitled Project"

        return {
            "success": True,
            "project_name": project_name,
            "ir": result.get("structured_data") or {},
            "diagrams": _build_diagram_outputs(result),
            "plantuml": result.get("plantuml") or {},
            "validation_report": validation_report,
            "educational_summary": "",
            "iterations_used": result.get("iterations_used", 1),
            "exported_files": _flatten_exported_files(result.get("files") or {}),
            "selected_candidate_id": result.get("selected_candidate_id", ""),
            "multi_agent": result.get("multi_agent", {}),
        }

    @staticmethod
    def generate_sample(sample_id: int):
        sample_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "data",
                f"sample{sample_id}.txt",
            )
        )

        with open(sample_path, "r", encoding="utf-8") as file_handle:
            requirements_text = file_handle.read().strip()

        result = UMLService.generate_uml(requirements_text)
        validation_report = result.get("validation") or {}
        validation_report["errors"] = _upper_severity(validation_report.get("errors", []))
        validation_report["iteration"] = result.get("iterations_used", 1)

        return {
            "success": True,
            "project_name": f"Sample {sample_id}",
            "ir": result.get("structured_data") or {},
            "diagrams": _build_diagram_outputs(result),
            "validation_report": validation_report,
            "educational_summary": "",
            "iterations_used": result.get("iterations_used", 1),
            "exported_files": _flatten_exported_files(result.get("files") or {}),
        }