
from __future__ import annotations

from skills.uml.skill import Skill


CLASS_GENERATION_SKILL = Skill(
    name="class_generation",
    instructions="""
ROLE

Generate only the Class Diagram portion of the UML IR.

Create the smallest complete DOMAIN-ORIENTED class model
supported by requirements and valid architectural context.

The Class Diagram defines canonical domain classes,
attributes, methods, and structural relationships for
downstream ER and Sequence generation.

Follow the supplied UML IR schema exactly.


SOURCE PRIORITY

Use:
1. Functional requirements and business rules.
2. Explicit domain concepts and relationships.
3. Valid HLD constraints when supplied.
4. Existing validated canonical names when supplied.

Requirements define WHAT the system must support.
HLD defines architectural boundaries when available.

If HLD is missing, incomplete, or marked "Failed":
- Do not invent an architecture.
- Do not assume Controllers, Services, or Repositories.
- Generate a requirements-grounded domain model only.
- Do not claim HLD alignment.
- Leave architecture-dependent decisions unresolved.

Do not treat failed HLD information as valid architecture.


CLASS SELECTION

Include classes representing meaningful domain concepts
that are supported by requirements.

Valid candidates include:
- Persistent domain entities.
- Domain objects with meaningful business state.
- Domain objects with justified domain behavior.
- Value objects needed to represent required data.
- Domain concepts needed for required relationships.

Normally exclude:
- Human actors without independent domain state.
- Frontend/UI components.
- Controllers and application Services.
- Repositories and database infrastructure.
- APIs, external systems, and technical utilities.
- Speculative helper, factory, and manager classes.

Architectural components may appear only when explicitly
required for internal class-level design.

Do not turn every requirement noun into a class.
Do not turn every system action into a class.

Choose a class only when its state, behavior, or
structural relationship is independently justified.

Prefer meaningful domain concepts over workflow names.


REQUIREMENT COVERAGE

Identify the domain state necessary to support the
supplied functional requirements.

Consider requirements concerning:
- Submitted business information and documents.
- Generated data and associated context.
- Identifiers and retrieval.
- Validation findings and their association with data.
- User feedback and repeated revisions.
- Persistent sessions, status, and results.
- Finalized outputs and their relationships.

These are coverage considerations, not mandatory
classes for every application.

Represent required information through appropriate
classes, attributes, or relationships.

Do not omit essential domain state merely to minimize
the number of classes.

Do not create a separate class when a justified
attribute or value object is sufficient.
Trace feedback, revision history, validation issues,
and SRS finalization directly to appropriate domain
classes (e.g., Feedback), attributes (e.g., issues, status,
updatedAt), or methods without inventing unsupported
manager, processor, or controller classes.

Preserve explicitly required history and relationships.


DOMAIN RESPONSIBILITY

A domain class owns its business state and genuine
domain behavior.

Classify each operation before assigning ownership:

DOMAIN BEHAVIOR:
Operates on the object's own state or enforces its
business invariants.

APPLICATION BEHAVIOR:
Coordinates workflows or multiple processing stages.

PERSISTENCE:
Saves, retrieves, updates, or queries stored data.

EXTERNAL PROCESSING:
Performs AI processing, transcription, integrations,
or document rendering.

Only genuine domain behavior belongs on domain classes.

Do not move application, persistence, or infrastructure
operations into domain classes because architectural
components are absent.

Examples of normally invalid domain responsibilities:
- Meeting.processMeetingInformation()
- Requirement.extractRequirement()
- Session.storeAnalysis()
- Session.retrieveAnalysis()
- Document.generateDocument()

These are application or infrastructure operations
unless explicitly justified as domain behavior.

A domain class may contain no methods when no
intrinsic domain behavior is supported.

Never invent methods merely to make classes active.


ATTRIBUTES

Attributes describe meaningful domain state.

Rules:
- Use camelCase attribute names.
- Preserve supplied domain terminology.
- Include meaningful attribute types.
- Include explicitly required identifiers.
- Include identifiers necessary for required references
  or relationships when clearly justified.
- Represent required status, feedback, and history data.
- Preserve data needed for downstream ER generation.
- Avoid duplicated state without justification.

Do not invent generic fields such as:
createdAt, updatedAt, deletedAt, metadata,
configuration, logData, or version.

Such fields are allowed only when requirements
or explicit domain rules justify them.

Do not place application infrastructure state
inside domain entities.

Business analysis sessions are valid domain concepts
when requirements explicitly require stored sessions.


METHODS

Generate methods only for genuine domain behavior
supported by requirements or business rules.

Rules:
- Use camelCase method names.
- Use specific, meaningful operation names.
- Assign each method to its actual owner.
- Avoid generic process(), handle(), manage(), execute().
- Avoid arbitrary CRUD methods.
- Avoid getters/setters without justification.
- Avoid duplicate responsibilities.
- Do not invent application orchestration methods.

Each method must define, when the schema supports:
- Name.
- Parameters and types.
- Return type.
- Owning class.

Use void only when no meaningful value is returned.

Method contracts must be internally consistent.

Do not create wrapper/result classes unless a structured
result is necessary and domain-justified.

Methods become canonical for Sequence generation.


TYPE CONSISTENCY

Every referenced custom type must be resolvable.

A valid type must be:
1. A declared Class Diagram class.
2. An explicitly supplied external/domain type.
3. A supported primitive or collection type.

Validate types inside collections.

Do not reference undefined custom classes.

Do not invent an entire class solely to repair an
unnecessary method signature.

Use consistent names and types across all classes.


CLASS NAMING

- Class names must use PascalCase.
- Attributes and methods must use camelCase.
- Preserve canonical domain terminology.
- Use one name per domain concept.
- Do not create synonyms for the same entity.
- Avoid class names based only on processing actions.
- Keep names stable for ER and Sequence generation.


RELATIONSHIPS

Allowed relationship types:
association, aggregation, composition,
inheritance, dependency.

Generate only meaningful domain relationships.

ASSOCIATION:
Use for justified structural/domain relationships.

COMPOSITION:
Use only for strong whole-part lifecycle ownership.

AGGREGATION:
Use only for justified weak whole-part ownership.

INHERITANCE:
Use only for genuine domain is-a relationships.

DEPENDENCY:
Use only when one domain class temporarily uses
another without structural ownership.

Do not:
- Convert workflow steps into class associations.
- Convert application calls into composition.
- Use inheritance merely for shared attributes.
- Add relationships for visual completeness.
- Duplicate equivalent relationships.
- Introduce architectural dependencies into
  a domain-only Class Diagram.

Both relationship endpoints must exist.


MULTIPLICITY

Use cardinalities only for justified structural
domain relationships.

Allowed forms:
1     exactly one
0..1  zero or one
0..*  zero or more
1..*  one or more

Preserve minimum and maximum participation.

"Exactly one" means 1.
"One or more" means 1..*.
"Optional" may indicate a minimum of zero.

Do not assume every collection has at least one item.

Consider valid lifecycle states:
Sessions, meetings, orders, and documents may exist BEFORE
speakers, requirements, items, or results are identified.
Their target relationship multiplicity must be 0..*, not 1..*.
Mandatory 1..* multiplicities violate lifecycle creation order.

Consider valid lifecycle states such as:
- Newly created records.
- Incomplete processing.
- Failed processing.
- Unfinalized results.

Do not invent multiplicities when requirements
and domain rules do not justify them.

For composition, verify lifecycle ownership rather
than relying only on cardinality.


CROSS-DIAGRAM CONSISTENCY

This Class Diagram establishes canonical:
- Domain class names.
- Domain attributes.
- Domain methods and signatures.
- Domain relationships.
- Structural multiplicities.

The ER Diagram may map persistent domain concepts
but must not convert architectural components
into database entities.

Sequence Diagrams must reuse domain method names
and method contracts exactly.

Architectural participants may legitimately appear
in Sequence Diagrams without appearing here.

Do not insert Controllers, Services, or Repositories
into this Class Diagram solely to support Sequence flow.


OVERDESIGN CONTROL

Every class, attribute, method, and relationship
must have a defensible requirement-based purpose.

Reject:
- Speculative functionality.
- Unnecessary helper classes.
- Redundant attributes.
- Duplicated responsibilities.
- Unsupported identifiers.
- Arbitrary CRUD methods.
- Decorative associations.
- Unsupported architectural assumptions.

Do not sacrifice required functionality merely
to reduce diagram size.

Prefer the smallest COMPLETE design,
not simply the smallest design.


FINAL VALIDATION

Before returning, verify:

1. Every class represents a justified domain concept.
2. Required domain state is adequately represented.
3. No actor-only concept became a domain class.
4. No unsupported architectural layer was invented.
5. Domain methods contain only domain responsibilities.
6. Persistence and orchestration methods are excluded.
7. Attributes are meaningful and correctly typed.
8. Referenced custom types are defined or supplied.
9. Method names and signatures are consistent.
10. Relationship endpoints exist.
11. Relationships have valid domain semantics.
12. Composition represents lifecycle ownership.
13. Multiplicities preserve supported business rules.
14. Required feedback, history, status, and output
    data are not silently discarded.
15. No speculative or duplicate elements remain.
16. Canonical names are stable for downstream diagrams.
17. Output conforms exactly to the UML IR schema.

Do not add fields unsupported by the IR schema.

Return ONLY the Class Diagram portion required
by the UML IR schema.

Do not return explanations or markdown.
""".strip(),
)
