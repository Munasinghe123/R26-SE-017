from __future__ import annotations

from skills.uml.skill import Skill

CLASS_GENERATION_SKILL = Skill(
    name="class_generation",
    instructions="""
ROLE

Generate the Class Diagram portion of the UML IR.

The Class Diagram becomes the canonical structural source of truth for later
ER and Sequence generation.


REQUIREMENT GROUNDING

- Generate the smallest complete structural design that supports the requirements.
- Every class, attribute, method, and relationship must have a requirement-based
  or explicitly supplied architectural justification.
- Do not create a class merely because a noun appears in the requirements.
- Do not invent architectural layers or unsupported functionality.


ACTORS VS CLASSES

- A requirements actor is NOT automatically a Class Diagram class.
- Do not convert an actor into a class unless the requirements also establish
  that concept as a domain entity, data concept, or structural system component.
- Actors that only interact with the system should normally be represented later
  as external participants in behavioral diagrams rather than application classes.


ARCHITECTURAL COMPONENTS

Do not automatically create Controller, Service, Repository, UI, or other
architectural layers.

However, when an architectural component is explicitly supplied and actively
participates in a required use case, represent it as a structural participant.

When present:

- Boundary/UI represents interaction with users or external systems.
- Controller handles incoming requests and use-case coordination.
- Service performs business/application logic.
- Repository performs persistence and data access.
- Domain Entity represents meaningful domain state and domain behavior.

Do not create additional layers merely to follow a generic architecture pattern.


RESPONSIBILITY OWNERSHIP

Assign each behavior to the class responsible for performing it.

- Request handling and payload/request validation belong to Controller/Boundary
  responsibilities when applicable.
- Business calculations and domain behavior belong to an appropriate Service or
  Domain Entity.
- Persistence operations belong to Repository classes when a Repository exists.
- Domain Entities must not perform database persistence operations when a
  Repository is present.
- Repositories must not contain business calculations or request-handling logic.
- Controllers must not contain persistence operations when a Repository exists.

Avoid duplicating the same responsibility across multiple classes.


ATTRIBUTES

- Attributes represent meaningful class state.
- Persistent domain attributes should support later ER mapping.
- Avoid speculative framework, configuration, metadata, audit, or generic attributes.
- Do not place domain-state attributes on Controllers, Services, Repositories, or
  Boundary classes without explicit justification.


METHODS

- Methods represent requirement-supported behavior.
- Use camelCase.
- Assign each method to the class that owns that responsibility.
- Avoid arbitrary CRUD methods.
- Avoid generic names such as process(), handle(), manage(), or execute() unless
  specifically justified.
- Do not create duplicate methods representing the same operation in different classes.
- Method names become canonical vocabulary for later Sequence generation.
- Later Sequence diagrams must reuse these exact method names.


NAMING

- Class names use PascalCase.
- Use one canonical name per concept.
- Do not create synonyms representing the same concept.
- Preserve stable naming for downstream ER and Sequence stages.


RELATIONSHIPS

Allowed relationship types:
association, aggregation, composition, inheritance, dependency.

Use:

- inheritance only for a genuine is-a relationship.
- composition only for strong lifecycle ownership.
- aggregation only for weak ownership.
- dependency when one class uses another without structural ownership.
- association for meaningful structural/domain relationships when stronger
  semantics are not justified.

Every relationship must have a semantic reason.

Relationship direction for dependencies follows usage:

    caller / user  ->  dependency

Examples of architectural direction when those components exist:

    Boundary/UI -> Controller
    Controller -> Service
    Service -> Repository

If no Service exists and the supplied architecture directly connects them:

    Controller -> Repository

A Repository must not depend on a Controller.

Do not use composition merely because one class calls another.
Do not use inheritance merely because classes share attributes.
Do not create decorative relationships.


CARDINALITY

Use multiplicity/cardinality primarily for structural domain relationships
where quantity can be justified from requirements or domain meaning.

Do not assign cardinality to ordinary architectural dependencies such as:

    Boundary -> Controller
    Controller -> Service
    Controller -> Repository
    Service -> Repository

unless the requirements explicitly describe a meaningful structural multiplicity.

Do not invent cardinalities when they cannot be justified.


CROSS-DIAGRAM ROLE

The Class Diagram establishes:

- canonical class names
- canonical method names
- domain concepts
- architectural participants

Later ER and Sequence generation must use these as structural source-of-truth inputs.

Do not include detailed ER-specific database rules or Sequence-specific control-flow
rules in this skill.
""".strip(),
)
