"""
HLA Agent — Prompt Builder
Constructs the 5-layer structured prompt that forces LLMs
to produce valid, parseable architecture JSON output.

Layers:
  1. Role Assignment & Optimization Lens
  2. Context Injection (FRs & NFRs)
  3. Output Schema Enforcement (JSON structure)
  4. Architectural Constraints (Canonical Styles & Topology)
  5. Quality Guardrails (Coverage & Provisions)
"""

import json
from typing import Optional


def build_architecture_prompt(requirements: dict, feedback: Optional[str] = None, candidate_num: int = 1) -> str:
    """
    Builds a robust 5-layer structured prompt enforcing valid, 
    parseable high-level architecture JSON outputs without markdown wrapping.
    """
    project_name = requirements.get("project", "Unknown System")
    frs = requirements.get("functional_requirements", [])
    nfrs = requirements.get("non_functional_requirements", [])
    feedback_text = f"\n\nREGENERATION FEEDBACK TO ADDRESS:\n{feedback}" if feedback else ""

    # ── Layer 1: Role Assignment & Objective Candidate Lens ────────
    if candidate_num == 1:
        priority_lens = (
            "PRIMARY BEST-FIT ARCHITECTURE: Objectively analyze all functional and non-functional requirements "
            "to select the single most optimal, natural architecture style that best matches the workload."
        )
    else:
        priority_lens = (
            "ALTERNATIVE TRADEOFF ARCHITECTURE: Explore a secondary, viable architectural style that provides "
            "a different structural perspective or tradeoff for these requirements (e.g., if Candidate 1 used "
            "Microservices Architecture, consider Event-Driven Architecture or Modular Monolith)."
        )

    role_layer = (
        "# LAYER 1: ROLE ASSIGNMENT & OPTIMIZATION LENS\n"
        "You are a senior software architect with deep expertise across ALL architectural styles. "
        "You evaluate each project's requirements objectively without architectural bias.\n"
        f"For this specific candidate generation: **{priority_lens}**\n\n"
        "STRICT OUTPUT RULE: Do NOT output markdown commentary, markdown code fences (like ```json), or preambles. "
        "Output ONLY the raw, valid JSON object adhering strictly to the required schema."
    )

    # ── Layer 2: Context Injection ────────────────────────
    fr_text = "\n".join(f"  - [{fr['id']}] {fr['description']}" for fr in frs)
    nfr_text = "\n".join(f"  - [{nfr['id']}] ({nfr['type']}) {nfr['target']}" for nfr in nfrs)

    context_layer = (
        f"# LAYER 2: SYSTEM REQUIREMENTS CONTEXT\n"
        f"Project Name: **{project_name}**{feedback_text}\n\n"
        f"FUNCTIONAL REQUIREMENTS:\n{fr_text}\n\n"
        f"NON-FUNCTIONAL REQUIREMENTS:\n{nfr_text}"
    )

    # ── Layer 3: Output Schema Enforcement ────────────────
    schema_layer = """# LAYER 3: OUTPUT SCHEMA ENFORCEMENT
OUTPUT FORMAT: You MUST respond with ONLY a valid, raw JSON object without markdown fences.
The JSON structure MUST match this exact specification:

{
  "architecture_style": "<one of: Layered Architecture, Event-Driven Architecture, Microservices Architecture, Modular Monolith, Pipe-and-Filter Architecture>",
  "pros_and_cons": "<2-3 sentence expert explanation of why this style fits this scenario, detailing ATAM quality tradeoffs>",
  "layers": [
    {
      "name": "<layer name, e.g., Presentation, Business Logic, Data Access, Infrastructure>",
      "order": <integer, 1 = topmost layer>
    }
  ],
  "components": [
    {
      "name": "<PascalCase name ending with a role suffix like Service, Controller, Repository, Gateway, Handler, Manager, Engine>",
      "layer": "<MUST exactly match one of the string names defined in the layers array above>",
      "boundary": "<one of: presentation, business_logic, data_access, infrastructure, cross_cutting>",
      "element_type": "<one of: service, module, handler, gateway, repository, broker, controller, client>",
      "responsibilities": ["<responsibility 1: clear explanatory sentence of at least 8 words>", "<responsibility 2>"],
      "provided_interfaces": ["<e.g., POST /orders, GET /orders/{id}>"],
      "required_interfaces": ["<e.g., OrderRepository, PaymentGateway>"],
      "requirement_ids": ["<FR-1>", "<FR-2>"]
    }
  ],
  "connectors": [
    {
      "from_component": "<component name matching an item from the components array>",
      "to_component": "<component name matching an item from the components array>",
      "connector_type": "<one of: sync_call, async_message, event_publish, data_flow, shared_data>",
      "protocol": "<e.g., REST, gRPC, AMQP, Kafka>",
      "data_transferred": "<e.g., OrderRequest, PaymentResponse>"
    }
  ],
  "quality_provisions": [
    {
      "nfr_id": "<NFR-1>",
      "iso_characteristic": "<one of: performance_efficiency, reliability, security, maintainability, scalability>",
      "responsible_component": "<component name matching an item from the components array>",
      "mechanism": "<e.g., Redis read-through cache, Circuit breaker with Resilience4j>",
      "evidence_strength": "<one of: high, medium, low>"
    }
  ]
}"""

    # ── Layer 4: Constraint Specification ─────────────────
    constraint_layer = """# LAYER 4: ARCHITECTURAL CONSTRAINTS
Evaluate requirements systematically, then choose strictly from these 5 canonical styles:
- **Layered Architecture**: Best for clear separation of concerns, moderate scale, and standard CRUD workflows.
- **Event-Driven Architecture**: Best for real-time notifications, async workflows, data streaming, or highly decoupled components.
- **Microservices Architecture**: Reserved for systems with multiple complex, isolated domains or massive horizontal scale (>50k concurrent users across distinct subsystems).
- **Modular Monolith**: Best for strong module boundaries within a single deployment unit, avoiding distributed network complexity.
- **Pipe-and-Filter Architecture**: Best for transformation engines, sequential data pipelines, or stream processing.

STRUCTURAL CONSTRAINTS:
1. Define at least 3 distinct layers inside the "layers" array.
2. Generate at least 8 distinct components distributed across those layers.
3. Every component name must terminate with an explicit structural suffix (e.g., Service, Controller, Broker, Repository).
4. Connectors must accurately reflect structural execution flows."""

    # ── Layer 5: Quality Guardrails ───────────────────────
    guardrail_layer = """# LAYER 5: COVERAGE & INTEGRITY GUARDRAILS
1. COMPLETE REQ COVERAGE: Every single functional requirement ID provided (FR-1, FR-2, etc.) MUST map to at least one component's "requirement_ids" field.
2. REALISTIC PROVISIONS: Every non-functional requirement MUST map to a component architectural provision. Ensure:
   - Scalability uses stateless designs, read replicas, load balancing, or async queues.
   - Performance leverages explicit caching, specialized indexes, or low-latency protocols.
   - Security references authentication filters, gateway proxies, validation engines, or encrypted storage handlers.
   - Availability utilizes health checkers, circuit breakers, dead-letter queues, or active redundancy components.
3. DATA INTEGRITY: Ensure there are no isolated components; all components must be interconnected using valid connectors."""

    return "\n\n".join([role_layer, context_layer, schema_layer, constraint_layer, guardrail_layer])


def build_feedback_from_scores(scores: dict) -> str:
    """Build constructive feedback string for regeneration loops from score breakdown."""
    low_metrics = [k for k, v in scores.items() if isinstance(v, (int, float)) and v < 0.6 and k != "CAS"]
    if not low_metrics:
        return "Improve general architectural cohesion and component interface specificity."
    return f"Focus on improving the following low-scoring architectural quality metrics: {', '.join(low_metrics)}."


def build_diagram_prompt(
    architecture: dict,
    requirements: Optional[dict] = None,
    kind: str = "plantuml",
    diagram_kind: Optional[str] = None,
    title: Optional[str] = None,
    iteration: int = 1,
    previous_diagram: Optional[str] = None,
    previous_diagram_cas: Optional[float] = None,
    feedback_issues: Optional[list[str]] = None,
    user_feedback: Optional[str] = None,
    notes: Optional[str] = None,
    **kwargs,
) -> str:
    """Build structured diagram generation or refinement prompt for PlantUML or Mermaid."""
    d_kind = (diagram_kind or kind or "plantuml").lower()
    project = title or (requirements.get("project") if isinstance(requirements, dict) else "System Architecture")
    arch_style = architecture.get("architecture_style", "Layered Architecture")
    comps = architecture.get("components", [])
    conns = architecture.get("connectors", []) or architecture.get("interactions", [])

    comp_list = "\n".join(f"- [{c.get('name')}] (Layer: {c.get('layer', 'Core')}, Boundary: {c.get('boundary', 'business_logic')})" for c in comps)
    conn_list = "\n".join(f"- {c.get('from_component') or c.get('from')} --> {c.get('to_component') or c.get('to')} : {c.get('connector_type') or c.get('type', 'sync_call')}" for c in conns)

    req_text = ""
    if isinstance(requirements, dict):
        frs = requirements.get("functional_requirements", [])
        if frs:
            req_text = "FUNCTIONAL REQUIREMENTS:\n" + "\n".join(f"  - [{fr.get('id')}] {fr.get('description')}" for fr in frs)

    notes_combined = user_feedback or notes or ""
    user_req = f"\nUSER REFINEMENT INSTRUCTION:\n{notes_combined}" if notes_combined else ""

    prev_text = ""
    if previous_diagram:
        prev_text = f"\nPREVIOUS DIAGRAM REVISION (Iteration {iteration - 1}, Score: {previous_diagram_cas or 'N/A'}):\n```\n{previous_diagram}\n```\n"

    issues_text = ""
    if feedback_issues:
        issues_text = "\nISSUES TO FIX IN THIS ITERATION:\n" + "\n".join(f"  - {iss}" for iss in feedback_issues)

    if d_kind == "plantuml":
        schema_rule = (
            "Output ONLY raw PlantUML code starting with @startuml and ending with @enduml.\n"
            "Use package/rectangle groupings to visually group components by their layer.\n"
            "Format line breaks properly using actual newlines."
        )
    else:
        schema_rule = (
            "Output ONLY raw Mermaid code starting with graph TD.\n"
            "Use subgraph groupings to visually group components by their layer."
        )

    return (
        f"# DIAGRAM GENERATION TASK (Iteration {iteration})\n"
        f"Project: {project}\n"
        f"Architecture Style: {arch_style}\n\n"
        f"{req_text}\n\n"
        f"COMPONENTS:\n{comp_list}\n\n"
        f"CONNECTORS:\n{conn_list}\n"
        f"{prev_text}"
        f"{issues_text}"
        f"{user_req}\n\n"
        f"INSTRUCTION: Refactor and optimize the {d_kind.upper()} diagram code based on the components, connectors, and instructions above.\n"
        f"{schema_rule}"
    )

