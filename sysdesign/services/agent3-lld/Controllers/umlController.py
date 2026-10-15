from __future__ import annotations

import os
from Services.umlService import UMLService
from schemas.umlSchema import GenerateRequest


def _print_upstream_inputs(request: GenerateRequest) -> None:
    print(f"\n{'='*60}")
    print("[LLD-Agent] INPUTS RECEIVED FROM UPSTREAM AGENTS")
    print(f"{'='*60}")

    # Agent 1 (Requirements Agent)
    print("[AGENT 1: Requirements Agent Input]")
    print(f"  Project Name        : {request.project_name or 'N/A'}")
    if request.project_description:
        print(f"  Project Description : {request.project_description}")
    reqs = request.functional_requirements or []
    print(f"  Functional Requirements ({len(reqs)} items received):")
    if reqs:
        for r in reqs:
            title_part = f" - {r.title}" if r.title else ""
            desc_part = f": {r.description}" if r.description else ""
            print(f"    - [{r.id}]{title_part}{desc_part}")
    else:
        print("    - (None provided)")

    # Agent 2 (High-Level Design / HLD Agent)
    arch = request.high_level_architecture
    print(f"\n[AGENT 2: High-Level Design (HLD) Agent Input]")
    print(f"  Architecture Pattern: {arch.pattern or 'N/A'}")
    if arch.layers:
        print(f"  Architectural Layers / Boundaries ({len(arch.layers)} layers):")
        for layer in arch.layers:
            comps = f" (Components: {', '.join(layer.components)})" if layer.components else ""
            desc = f" - {layer.description}" if layer.description else ""
            print(f"    - {layer.name}{desc}{comps}")
    else:
        print("  Architectural Layers: None specified")
    if arch.architectural_constraints:
        print(f"  Architectural Constraints ({len(arch.architectural_constraints)} constraints):")
        for c in arch.architectural_constraints:
            print(f"    - {c}")
    else:
        print("  Architectural Constraints: None specified")
    print(f"{'='*60}\n")


def _build_requirements_text(request: GenerateRequest) -> tuple[str, list[str]]:
    lines: list[str] = []
    requirement_ids: list[str] = []

    project_name = request.project_name.strip() or "Untitled Project"
    lines.append(f"Project Name: {project_name}")

    if request.project_description.strip():
        lines.append(f"Project Description: {request.project_description.strip()}")

    architecture = request.high_level_architecture
    arch_pattern = architecture.pattern.strip()
    is_failed_hld = arch_pattern.lower() in ("failed", "none", "none specified", "error", "n/a", "invalid")

    if arch_pattern and not is_failed_hld:
        lines.append(f"Architecture Pattern: {arch_pattern}")
    elif is_failed_hld:
        lines.append("Architecture Pattern: Provisional (HLD unavailable or failed; do not invent speculative layers)")

    if architecture.layers:
        valid_layers = [
            l for l in architecture.layers
            if l.name.strip() and l.name.strip().lower() not in ("none specified", "none", "failed", "n/a")
        ]
        if valid_layers:
            lines.append("Architecture Layers:")
            for layer in valid_layers:
                name = layer.name.strip() or "Layer"
                lines.append(f"- {name}")
                if layer.description.strip():
                    lines.append(f"  Description: {layer.description.strip()}")
                if layer.components:
                    components = ", ".join([c.strip() for c in layer.components if c.strip()])
                    if components:
                        lines.append(f"  Components: {components}")

    if architecture.architectural_constraints:
        valid_constraints = [
            c.strip() for c in architecture.architectural_constraints
            if c.strip() and c.strip().lower() not in ("none specified", "none", "failed", "n/a")
        ]
        if valid_constraints:
            constraints = ", ".join(valid_constraints)
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
            "png": class_png or "",
            "cloudinary_url": class_png or "",
            "svg_content": "",
        })

    seq_plantuml = plantuml.get("sequence", []) or []
    seq_pngs = pngs.get("sequence", []) or []
    for index, seq in enumerate(seq_plantuml):
        seq_png = ""
        if index < len(seq_pngs):
            if isinstance(seq_pngs[index], dict):
                seq_png = seq_pngs[index].get("png") or seq_pngs[index].get("cloudinary_url") or ""
            elif isinstance(seq_pngs[index], str):
                seq_png = seq_pngs[index]
        diagrams.append({
            "diagram_type": "Sequence",
            "plantuml_syntax": seq.get("plantuml", "") if isinstance(seq, dict) else str(seq),
            "mermaid_syntax": "",
            "name": seq.get("name", f"Sequence {index + 1}") if isinstance(seq, dict) else f"Sequence {index + 1}",
            "png_base64": seq_png or "",
            "png": seq_png or "",
            "cloudinary_url": seq_png or "",
            "svg_content": "",
        })

    er_plantuml = plantuml.get("er", "")
    er_png = pngs.get("er", "")
    if isinstance(er_png, list):
        er_png = er_png[0] if er_png else ""
    if er_plantuml or er_png:
        diagrams.append({
            "diagram_type": "ER",
            "plantuml_syntax": er_plantuml if isinstance(er_plantuml, str) else (er_plantuml[0] if er_plantuml else ""),
            "mermaid_syntax": "",
            "name": "ER Diagram",
            "png_base64": er_png or "",
            "png": er_png or "",
            "cloudinary_url": er_png or "",
            "svg_content": "",
        })

    return diagrams


class UMLController:

    @staticmethod
    def generate(request: GenerateRequest):
        _print_upstream_inputs(request)
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
            "pngs": result.get("pngs") or {},
            "cloudinary_urls": result.get("cloudinary_urls") or {},
            "files": result.get("files") or {},
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
            "plantuml": result.get("plantuml") or {},
            "pngs": result.get("pngs") or {},
            "cloudinary_urls": result.get("cloudinary_urls") or {},
            "files": result.get("files") or {},
            "validation_report": validation_report,
            "educational_summary": "",
            "iterations_used": result.get("iterations_used", 1),
            "exported_files": _flatten_exported_files(result.get("files") or {}),
        }