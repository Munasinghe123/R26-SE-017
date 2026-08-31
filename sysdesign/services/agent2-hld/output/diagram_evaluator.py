"""Diagram Evaluator — Research-Grade Validation

Applies the same 6-metric evaluation framework (RTS, QAC, CI, CoS, SSM₁, SSM₂)
used for architecture validation to diagram artifacts.

This ensures diagrams are not just syntactically correct but also:
- Architecturally complete (RTS)
- Quality-attribute aligned (QAC)
- Structurally decoupled (CI)
- Semantically cohesive (CoS)
- Style-conformant (SSM₁, SSM₂)

Academic Positioning:
- Extends architecture evaluation to visual artifacts
- Provides auditable, deterministic scoring
- Supports research reproducibility
"""

from __future__ import annotations

import logging
from typing import Optional

from evaluation import evaluate_architecture

logger = logging.getLogger(__name__)


def _extract_architecture_from_diagram(diagram: str, kind: str, original_architecture: dict) -> dict:
    """Reverse-engineer architecture structure from diagram source.
    
    This allows us to validate if the diagram faithfully represents the architecture.
    """
    import re
    
    # Start with original architecture as baseline
    extracted = {
        "architecture_style": original_architecture.get("architecture_style", ""),
        "layers": original_architecture.get("layers", []),
        "components": [],
        "connectors": [],
    }
    
def _extract_architecture_from_diagram(diagram: str, kind: str, original_architecture: dict) -> dict:
    """Reverse-engineer architecture structure from diagram source.
    
    This allows us to validate if the diagram faithfully represents the architecture.
    """
    import re
    
    extracted = {
        "architecture_style": original_architecture.get("architecture_style", ""),
        "layers": original_architecture.get("layers", []),
        "components": [],
        "connectors": [],
    }
    
    orig_comps = original_architecture.get("components", [])

    if kind == "plantuml":
        # Match [ComponentName], component [ComponentName], database "Name", queue "Name", etc.
        comp_pattern = r'(?:\[([^\]\n]+)\]|(?:component|database|queue|storage|node|actor|cloud|rectangle|frame|package)\s+["\']?([^"\'\n\\[]+)["\']?)\s*(?:as\s+(\w+))?'
        
        seen_names = set()
        for match in re.finditer(comp_pattern, diagram, re.IGNORECASE):
            raw_name = (match.group(1) or match.group(2) or "").strip()
            alias = (match.group(3) or "").strip()
            if not raw_name or raw_name.startswith("@"):
                continue
            
            # Resolve to original component
            orig_comp = next((c for c in orig_comps if c.get("name", "").strip() in {raw_name, alias} or c.get("name", "").replace(" ", "_") in {raw_name, alias}), None)
            if not orig_comp and raw_name:
                orig_comp = next((c for c in orig_comps if raw_name.lower() in c.get("name", "").lower()), None)

            if orig_comp:
                c_name = orig_comp.get("name")
                if c_name not in seen_names:
                    seen_names.add(c_name)
                    extracted["components"].append(orig_comp)
        
        # Connectors: handles "A" -> "B", A --> B, A -[down]-> B, A ..> B, A ==> B with optional labels : label
        inter_pattern = r'["\']?([\w\s]+)["\']?\s*(?:-\[\w+\]->|-+>|\.\.>|==>|->)\s*["\']?([\w\s]+)["\']?(?:\s*:\s*([^\n]+))?'
        for match in re.finditer(inter_pattern, diagram):
            from_comp = match.group(1).strip()
            to_comp = match.group(2).strip()
            label = (match.group(3) or "").strip()
            
            if from_comp.startswith("@") or to_comp.startswith("@"):
                continue

            from_name = _resolve_component_name(from_comp, diagram, original_architecture)
            to_name = _resolve_component_name(to_comp, diagram, original_architecture)
            
            if from_name and to_name:
                extracted["connectors"].append({
                    "from_component": from_name,
                    "to_component": to_name,
                    "connector_type": label or "sync_call",
                    "protocol": "",
                })
    
    elif kind == "mermaid":
        # Matches Mermaid shapes: [...] [(...)] (...) {{...}} ([...])
        comp_pattern = r'(\w+)(?:\[|\[\(|\(|\{\{|\(\[)([^\]\)\}\n]+)(?:\]|\)\]|\)|\}\}|\]\))'
        seen_names = set()
        for match in re.finditer(comp_pattern, diagram):
            comp_id = match.group(1).strip()
            comp_label = match.group(2).strip().strip('"').strip("'")
            
            orig_comp = next((c for c in orig_comps if c.get("name", "") in {comp_label, comp_id} or c.get("name", "").replace(" ", "_") == comp_id), None)
            if orig_comp:
                c_name = orig_comp.get("name")
                if c_name not in seen_names:
                    seen_names.add(c_name)
                    extracted["components"].append(orig_comp)
        
        # Connectors: A -->|label| B or A --> B
        inter_pattern = r'(\w+)\s*--+>(?:\|"?([^"|]+)"?\|)?\s*(\w+)'
        for match in re.finditer(inter_pattern, diagram):
            from_id = match.group(1).strip()
            label = (match.group(2) or "").strip()
            to_id = match.group(3).strip()
            
            from_name = _resolve_component_name(from_id, diagram, original_architecture)
            to_name = _resolve_component_name(to_id, diagram, original_architecture)
            
            if from_name and to_name:
                extracted["connectors"].append({
                    "from_component": from_name,
                    "to_component": to_name,
                    "connector_type": label or "sync_call",
                    "protocol": "",
                })
    
    return extracted


def _resolve_component_name(identifier: str, diagram: str, architecture: dict) -> Optional[str]:
    """Resolve component identifier/alias to actual component name."""
    clean_id = identifier.strip().strip('"').strip("'")
    
    # Direct match
    for comp in architecture.get("components", []):
        name = comp.get("name", "").strip()
        if name in {identifier, clean_id} or name.replace(" ", "_") in {identifier, clean_id}:
            return name
    
    # Fuzzy match on diagram declarations (both PlantUML & Mermaid)
    import re
    if "plantuml" in diagram.lower() or "@startuml" in diagram.lower():
        pattern = rf'(?:\[([^\]]+)\]|(?:component|database|queue|storage|node|actor|cloud|rectangle)\s+["\']?([^"\'\n\\[]+)["\']?)\s+as\s+{re.escape(clean_id)}\b'
        match = re.search(pattern, diagram, re.IGNORECASE)
        if match:
            found = (match.group(1) or match.group(2) or "").strip()
            for comp in architecture.get("components", []):
                if comp.get("name", "").strip() == found or found.lower() in comp.get("name", "").lower():
                    return comp.get("name")
            return found
            
    return clean_id


def evaluate_diagram_with_metrics(
    *,
    diagram: str,
    kind: str,
    architecture: dict,
    requirements: dict,
) -> dict:
    """Evaluate diagram using full 6-metric research-grade framework.
    
    Args:
        diagram: Diagram source code (PlantUML or Mermaid)
        kind: "plantuml" or "mermaid"
        architecture: Original architecture JSON
        requirements: Requirements JSON with FRs and NFRs
    
    Returns:
        {
            "diagram_cas": float,
            "metrics": {
                "rts": {...}, "qac": {...}, "ci": {...},
                "cos": {...}, "ssm": {...}
            },
            "scores": {
                "RTS": float, "QAC": float, "CI": float,
                "CoS": float, "SSM1": float, "SSM2": float, "CAS": float
            },
            "verdict": str,
            "detected_style": str,
            "issues": [str],
            "extracted_architecture": dict
        }
    """
    logger.info(f"Evaluating {kind} diagram with 6-metric framework")
    
    # Extract architecture from diagram
    extracted_arch = _extract_architecture_from_diagram(diagram, kind, architecture)
    
    # Apply full 6-metric evaluation
    eval_result = evaluate_architecture(extracted_arch, requirements)
    
    # Extract scores dict
    scores = {
        "RTS": eval_result["RTS"],
        "QAC": eval_result["QAC"],
        "CI": eval_result["CI"],
        "CoS": eval_result["CoS"],
        "SSM1": eval_result["SSM1"],
        "SSM2": eval_result["SSM2"],
        "CAS": eval_result["CAS"],
    }
    
    # Generate issues from metric results
    issues = []
    details = eval_result.get("details", {})
    
    rts_detail = details.get("rts", {})
    if rts_detail.get("untraced"):
        issues.append(f"RTS: {len(rts_detail['untraced'])} untraced requirements: {', '.join(rts_detail['untraced'][:5])}")
    
    qac_detail = details.get("qac", {})
    if qac_detail.get("uncovered"):
        issues.append(f"QAC: {len(qac_detail['uncovered'])} uncovered NFRs: {', '.join(qac_detail['uncovered'][:5])}")
    
    ci_detail = details.get("ci", {})
    if ci_detail.get("graph_density", 0) > 0.5:
        issues.append(f"CI: High graph density ({ci_detail['graph_density']:.2f}) indicates tight coupling")
    
    cos_detail = details.get("cos", {})
    low_cohesion = [
        c["name"] for c in cos_detail.get("component_cohesion", [])
        if c.get("cohesion", 1.0) < 0.5 and c.get("num_responsibilities", 0) >= 2
    ]
    if low_cohesion:
        issues.append(f"CoS: {len(low_cohesion)} components with low cohesion: {', '.join(low_cohesion[:5])}")
    
    logger.info(f"Diagram CAS: {scores['CAS']:.4f} | Verdict: {eval_result['verdict']}")
    
    return {
        "diagram_cas": scores["CAS"],
        "metrics": details,
        "scores": scores,
        "verdict": eval_result["verdict"],
        "detected_style": eval_result.get("detected_style", ""),
        "issues": issues,
        "extracted_architecture": extracted_arch,
        "weighted_breakdown": details.get("cas", {}).get("weighted_breakdown", {}),
    }
