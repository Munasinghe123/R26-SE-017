from __future__ import annotations

import json
from typing import Any


def build_overview_prompt(project_name: str, requirements: dict[str, Any]) -> str:
    fr_summary = [
        f"- [{fr.get('id', 'FR')}]: {fr.get('title', '')} - {fr.get('description', '')}"
        for fr in requirements.get("functional_requirements", [])
    ]
    nfr_summary = [
        f"- [{nfr.get('id', 'NFR')}] ({nfr.get('iso_characteristic', 'quality')}): {nfr.get('description', '')}"
        for nfr in requirements.get("non_functional_requirements", [])
    ]

    return f"""
You are an expert Systems Architect creating Section 1 & 2 of an ISO/IEC/IEEE 29148:2018 Software Requirements Specification (SRS).

PROJECT NAME:
{project_name}

RAW FUNCTIONAL REQUIREMENTS:
{chr(10).join(fr_summary) if fr_summary else "None specified"}

RAW NON-FUNCTIONAL REQUIREMENTS:
{chr(10).join(nfr_summary) if nfr_summary else "None specified"}

EXISTING CONSTRAINTS / ASSUMPTIONS:
- Design Constraints: {requirements.get('design_constraints', [])}
- External Interfaces: {requirements.get('external_interfaces', [])}
- Assumptions: {requirements.get('assumptions_and_dependencies', [])}

TASK:
Generate the System Overview artifact in strict JSON format.

EXTERNAL INTERFACES (IEEE 29148 §9.6.4.4 & §9.6.4.9):
- Analyze the provided Functional and Non-Functional Requirements for any required third-party services, APIs, payment gateways, messaging services, external data registries, or authentication providers.
- Extract concrete external interfaces that the software must communicate with to fulfill these requirements.
- If no external interfaces are mentioned or implied, return an empty array [].

ACRONYMS & DOMAIN GLOSSARY (IEEE 29148 §9.6.20 / §5.2):
- Scan the project name, FRs, and NFRs for industry acronyms, technical terms, or domain abbreviations (e.g. RBAC, EHR, SLA, HIPAA, REST, JWT, TLS, FHIR, etc.).
- Provide concise, formal definitions for each term relevant to the system context.
- Include at least 3-6 key terms to establish domain understanding.

STANDARDS COMPLIANCE & REGULATORY GOVERNANCE (IEEE 29148 §9.6.17):
- Identify formal external standards, regulations, or compliance frameworks applicable to this system based on the NFRs (security, privacy, accessibility) and constraints:
  * Baseline Engineering: ISO/IEC/IEEE 29148:2018 (Requirements Engineering) and ISO/IEC 25010:2011 (Product Quality).
  * Domain & Data Privacy: e.g. HIPAA (health data), GDPR (user privacy), PCI-DSS (payments), or ISO 27001 (information security) if applicable.
  * Accessibility: e.g. WCAG 2.1 Level AA (if web/user interfaces are present).

OUTPUT SCHEMA:
{{
  "overview_section": {{
    "purpose": "A formal paragraph (>20 characters) explaining why this software exists and what this SRS defines.",
    "scope": "Clear description of product boundaries, primary objectives, and business value.",
    "product_perspective": "Context of how this system fits into existing platforms, client devices, and external systems.",
    "acronyms_and_glossary": [
      {{
        "term": "e.g. RBAC",
        "definition": "Role-Based Access Control - Access policy restricting actions based on assigned user roles."
      }}
    ],
    "standards_compliance": [
      {{
        "standard": "e.g. ISO/IEC/IEEE 29148:2018",
        "category": "Software Engineering Standard | Regulatory Privacy | Accessibility | Information Security",
        "scope_and_applicability": "Governs formal specification structure and requirement normative language."
      }}
    ],
    "user_characteristics": [
      {{
        "role": "e.g. End User / Administrator",
        "description": "User background, technical competence, and expectations."
      }}
    ],
    "external_interfaces": [
      {{
        "name": "e.g. Payment Gateway API",
        "category": "Third-Party SaaS API | Software Interface | Communication Protocol",
        "purpose": "Why this external interface is required to fulfill the requirements",
        "protocol": "e.g. HTTPS / REST JSON / Webhooks / OAuth2"
      }}
    ],
    "assumptions_and_dependencies": [
      "Key technical or operational assumptions"
    ],
    "design_constraints": [
      "Hardware, regulatory, or architectural constraints"
    ]
  }}
}}

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON.
- Do NOT wrap in markdown explanation.
- Do NOT output preamble or postamble.
""".strip()


def build_functional_prompt(requirements: dict[str, Any], overview_section: dict[str, Any]) -> str:
    fr_list = requirements.get("functional_requirements", [])
    fr_json = json.dumps(fr_list, indent=2, ensure_ascii=True)

    return f"""
You are an ISO/IEC/IEEE 29148 Requirements Engineer.
Formalize the raw functional requirements into strict IEEE 29148 normative specifications.

SYSTEM OVERVIEW CONTEXT:
Purpose: {overview_section.get('purpose', '')}
Scope: {overview_section.get('scope', '')}

RAW FUNCTIONAL REQUIREMENTS TO FORMALIZE:
{fr_json}

RULES:
1. You MUST preserve EVERY requirement ID (e.g. FR-1, FR-2). Do NOT drop or renumber any requirement.
2. Normative Phrasing: Every requirement statement MUST use standard normative wording like: "The system shall [action]...".
3. Provide at least one concrete, testable acceptance criterion per requirement (Given/When/Then or measurable verification check).
4. Assign an operational priority: "High", "Medium", or "Low".

OUTPUT SCHEMA:
{{
  "functional_requirements": [
    {{
      "id": "FR-1",
      "title": "Concise title",
      "statement": "The system shall...",
      "priority": "High | Medium | Low",
      "acceptance_criteria": [
        "Given valid user credentials, When user logs in, Then authentication succeeds within 200ms."
      ]
    }}
  ]
}}

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON.
- No markdown formatting outside the JSON, no commentary.
""".strip()


def build_non_functional_prompt(
    requirements: dict[str, Any],
    overview_section: dict[str, Any],
    functional_specs: list[dict[str, Any]],
) -> str:
    nfr_list = requirements.get("non_functional_requirements", [])
    nfr_json = json.dumps(nfr_list, indent=2, ensure_ascii=True)

    return f"""
You are a Quality Attribute and ISO/IEC 25010 Systems Engineer.
Formalize the raw non-functional requirements into measurable, verifiable software quality specifications.

SYSTEM CONTEXT:
System Scope: {overview_section.get('scope', '')}
Total Functional Specs: {len(functional_specs)}

RAW NON-FUNCTIONAL REQUIREMENTS:
{nfr_json}

VALID ISO/IEC 25010 CHARACTERISTICS:
- functional_suitability
- performance_efficiency
- compatibility
- usability
- reliability
- security
- maintainability
- portability

RULES:
1. Preserve EVERY input NFR ID (e.g. NFR-1, NFR-2). Do NOT drop or renumber.
2. Categorize each requirement into one of the valid ISO/IEC 25010 characteristics above.
3. Every requirement MUST have a measurable, quantifiable `target_metric` (e.g., latency < 300ms, 99.9% uptime, AES-256 encryption, WCAG 2.1 AA). Avoid purely vague adjectives like "fast" or "secure" without a metric.

OUTPUT SCHEMA:
{{
  "non_functional_requirements": [
    {{
      "id": "NFR-1",
      "iso_characteristic": "performance_efficiency",
      "description": "The system shall sustain high throughput during peak load.",
      "target_metric": "95th percentile response time < 300ms under 500 concurrent users."
    }}
  ]
}}

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON.
- No markdown wrapping, no prose explanations.
""".strip()


def build_traceability_prompt(
    functional_specs: list[dict[str, Any]],
    non_functional_specs: list[dict[str, Any]],
    annexes: dict[str, Any],
) -> str:
    fr_summary = [{"id": f.get("id"), "title": f.get("title")} for f in functional_specs]
    
    # Extract components from HLD annex if available
    hld_components = []
    hld_matrix = annexes.get("hld_annex", {}).get("component_responsibility_matrix", [])
    for row in hld_matrix:
        hld_components.append(row.get("component"))

    return f"""
You are a Lead Systems Engineer generating a Requirements Traceability Matrix (RTM) for an IEEE 29148 specification.

FUNCTIONAL REQUIREMENTS:
{json.dumps(fr_summary, ensure_ascii=True)}

AVAILABLE ARCHITECTURE COMPONENTS (from HLD Annex / System Model):
{json.dumps(hld_components if hld_components else ["Frontend Web Client", "API Gateway", "Core Business Service", "Persistence Store", "Auth Service"], ensure_ascii=True)}

RULES:
1. Every Functional Requirement MUST have exactly one entry in the traceability matrix.
2. Allocate each requirement to a logical subsystem or architectural component.
3. Assign a primary verification method: "Test", "Inspection", "Demonstration", or "Analysis".

OUTPUT SCHEMA:
{{
  "traceability_matrix": [
    {{
      "requirement_id": "FR-1",
      "allocated_component": "API Gateway / Auth Service",
      "verification_method": "Test"
    }}
  ]
}}

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON.
""".strip()
