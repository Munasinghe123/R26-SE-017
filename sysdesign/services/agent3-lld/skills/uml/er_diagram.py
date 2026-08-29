from __future__ import annotations

from skills.uml.skill import Skill


ER_GENERATION_SKILL = Skill(
    name="er_generation",
    instructions="""
ROLE

Generate the ER Diagram portion of the UML IR.

The ER Diagram is the canonical persistent data model derived from requirements
and from the validated Class Diagram.


SOURCE OF TRUTH

- Requirements are the semantic source of truth.
- The validated Class Diagram is the structural source of truth.
- No existing database schema is supplied.
- Design the persistent model implied by Requirements + validated Class Diagram.


SCOPE

- Generate only persistent entities, their attributes, primary keys, and
    persistent relationships.
- Exclude non-persistent runtime components.


ENTITY ELIGIBILITY

- Create entities only for persistent domain concepts.
- Do not turn Controller, Service, Repository, Boundary/UI, external systems,
    or utilities into entities merely because they exist in the Class Diagram.
- Do not create bridge entities, lookup tables, or auxiliary entities unless
    requirements or domain structure clearly justify them.
- Generate the smallest complete persistent data model.


NAMING

- Preserve canonical domain concept naming from the Class Diagram.
- Use one canonical entity name per concept.
- Do not introduce synonyms for concepts already represented.


PRIMARY KEYS

- Every persistent entity must have a primary key.
- Primary keys must reference an attribute present on the same entity.
- Avoid speculative surrogate keys when a clear requirement-backed key exists.


ATTRIBUTES

- Attributes should originate from persistent domain state represented in the
    Class Diagram and/or clearly required by requirements.
- Do not invent unsupported attributes.
- Do not include transient process state, UI-only fields, framework metadata,
    or transport-specific fields unless explicitly persisted by requirements.
- Keep attributes minimal but sufficient to support required behaviors.


RELATIONSHIPS

- ER relationships must be justified by requirements and structural
    relationships.
- Every relationship endpoint must reference a generated entity.
- Use only supported relationship types:
    one-to-one, one-to-many, many-to-one, many-to-many.
- Do not create decorative or speculative relationships.
- Do not force relationships between entities that only share naming similarity.


CARDINALITY AND OWNERSHIP

- Relationship multiplicity must be semantically justified.
- Prefer conservative multiplicity when requirements are ambiguous.
- Do not infer strong ownership/lifecycle semantics unless clearly supported.


CROSS-DIAGRAM CONSISTENCY

- Keep entity concepts consistent with Class Diagram domain entities.
- Persistent structures should be suitable for repository-facing interactions
    later referenced by Sequence generation.
- If requirements imply persistence for a concept absent from Class Diagram,
    still avoid speculative expansion beyond the minimum required model.


QUALITY BAR

- Prioritize correctness, traceability to requirements, naming consistency,
    and minimum necessary complexity.
- Do not create speculative database entities just to make the ER diagram look
    complete.
""".strip(),
)
