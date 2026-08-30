from __future__ import annotations

from skills.uml.skill import Skill


CLASS_GENERATION_SKILL = Skill(
    name="class_generation",
    instructions="""
ROLE

Generate the Class Diagram portion of the UML IR.

The Class Diagram is DOMAIN-ORIENTED.

Its purpose is to represent the structural domain model of the system/module,
including domain classes, their meaningful state, domain behavior, and structural
relationships.

Do not use the Class Diagram to repeat the HLD architecture.

Controllers, repositories, frontend applications, APIs, infrastructure components,
and other application-layer participants normally belong to HLD or behavioral
diagrams such as Sequence Diagrams.

Generate the smallest complete domain model supported by the requirements.


SYSTEM BOUNDARY

Include only concepts that belong to the domain/object model of the system.

Normally INCLUDE:

- domain entities
- domain objects with meaningful state
- domain objects with requirement-supported behavior
- value objects when explicitly justified
- domain abstractions or inheritance structures explicitly supported by requirements

Normally EXCLUDE:

- human actors
- frontend applications
- web/mobile clients
- Controllers
- Services
- Repositories
- API handlers
- database-access components
- infrastructure components
- deployment components
- external systems
- third-party services
- external APIs

These excluded components may still participate in HLD or Sequence Diagrams.

An architectural component should appear in the Class Diagram only if the input
explicitly requests its internal class-level design.

Example:

Given HLD components:

    FrontendUI (Next.js)
    OrderController (FastAPI)
    DatabaseRepository

and domain entities:

    Customer
    Order
    CartItem

the Class Diagram should normally contain:

    Customer
    Order
    CartItem

and should normally NOT contain:

    FrontendUI
    OrderController
    DatabaseRepository


REQUIREMENT GROUNDING

Every generated class, attribute, method, and relationship must be supported by
the supplied requirements.

Do not:

- create a class merely because a noun appears in the requirements
- duplicate architectural components from the HLD
- invent unsupported domain concepts
- invent helper, manager, utility, adapter, factory, DTO, wrapper, or framework classes
- introduce speculative implementation details
- introduce functionality not required by the use cases or business rules

Before adding a class, verify that it satisfies at least one of these:

1. It is explicitly defined as a domain entity or domain concept.
2. It owns meaningful domain state.
3. It owns requirement-supported domain behavior.
4. It is structurally necessary to represent a required domain relationship.

If none apply, do not create the class.


ACTORS VS DOMAIN CLASSES

A requirements actor is NOT automatically a Class Diagram class.

Actors describe external interaction with the system.

A concept may appear both as:

- an external actor, and
- a domain entity

when the requirements independently define both roles.

Example:

Customer as actor:
    an authenticated user interacting with the storefront

Customer as domain entity:
    a business concept with customer_id and relationships to Orders

If Customer is explicitly defined as a domain entity, include Customer in the
Class Diagram because of its domain role, not because it is an actor.

If an actor has no independent domain representation, exclude it from the
Class Diagram.


DOMAIN RESPONSIBILITY OWNERSHIP

Methods should represent behavior that naturally belongs to the domain class.

Examples:

    Order.calculateTotalPrice()
    ShoppingCart.calculateTotal()
    Account.withdraw()

Do not place application orchestration, API handling, UI actions, or persistence
operations on domain classes unless those operations genuinely represent domain
behavior.

Normally exclude methods such as:

    submitCheckout()
    handleRequest()
    createOrderInDatabase()
    saveOrder()
    sendHttpRequest()

when those operations belong to Controllers, Services, Repositories, or other
application/infrastructure participants.

Persistence behavior should not be added to domain entities merely because a
database repository exists elsewhere in the architecture.

Avoid duplicating the same domain responsibility across multiple classes.


ATTRIBUTES

Attributes represent meaningful domain state.

Rules:

- preserve explicitly supplied domain attributes
- preserve canonical requirement terminology
- include identifiers when explicitly supplied
- preserve attributes required by domain relationships
- keep attributes compatible with later ER generation
- do not invent speculative state

Do not automatically add common fields such as:

    created_at
    updated_at
    deleted
    active
    version
    metadata

unless explicitly supported by the requirements.

Do not add framework, UI, repository, request, session, configuration, logging,
or infrastructure attributes to domain classes.


METHODS

Methods represent requirement-supported DOMAIN behavior.

Rules:

- use camelCase
- assign behavior to the class that naturally owns it
- generate only behavior supported by requirements or business rules
- avoid arbitrary CRUD operations
- avoid getters/setters unless explicitly required
- avoid generic names such as:
    process()
    handle()
    manage()
    execute()
  unless explicitly justified
- do not duplicate equivalent behavior across classes
- do not invent methods simply to make a class appear active

Example:

If the requirement says:

    "The system calculates the total price of the Order."

and Order contains the data required for the calculation, prefer:

    Order.calculateTotalPrice()

rather than creating application-layer operations inside the domain model.

Methods defined here become canonical DOMAIN method names for downstream
Sequence generation.


NAMING

- Class names use PascalCase.
- Method names use camelCase.
- Preserve domain terminology from requirements.
- Use one canonical name per concept.
- Do not create synonyms for the same domain concept.
- Keep names stable for downstream ER and Sequence generation.


RELATIONSHIPS

Allowed relationship types:

- association
- aggregation
- composition
- inheritance
- dependency

For the domain-oriented Class Diagram, prefer structural domain relationships.

Do not generate relationships merely because two components interact in an
application workflow.

For example, do NOT add architectural relationships such as:

    OrderController -> DatabaseRepository
    FrontendUI -> OrderController

because those belong to the architecture/behavioral view rather than the
domain Class Diagram.


ASSOCIATION

Use association for a meaningful structural relationship between domain classes
when stronger ownership semantics are not justified.

Example:

    Customer 1 -- 0..* Order

Use association when the classes are related structurally but one does not
strongly own the lifecycle of the other.


COMPOSITION

Use composition when the requirements support strong whole-part ownership.

Evidence may include statements such as:

- "contains"
- "consists of"
- "belongs exclusively to"
- the part has no meaningful independent lifecycle in the modeled domain

Example:

Requirements:

    An Order contains one or more CartItems.
    Each CartItem belongs to exactly one Order.

A suitable relationship is:

    Order 1 *-- 1..* CartItem

Use composition only when lifecycle ownership is justified.

Do not use composition merely because one object calls another.


AGGREGATION

Use aggregation only when the requirements support a meaningful whole-part
relationship but the part can exist independently of the whole.

Do not use aggregation as a default alternative to association.


INHERITANCE

Use inheritance only for a genuine domain "is-a" relationship.

Do not infer inheritance merely from:

- similar attributes
- similar methods
- similar names
- shared identifiers
- common database fields


DEPENDENCY

Dependency may be used between domain classes when one domain class temporarily
uses another without a meaningful structural association.

However, do not use dependency to reproduce HLD/application-layer interactions.

Do not add Controllers, Services, Repositories, or UI components merely to show
dependencies.

Do not assign multiplicity to dependency relationships.


CARDINALITY / MULTIPLICITY

Multiplicity applies to structural domain relationships.

Use requirement semantics precisely:

    1       exactly one
    0..1    zero or one
    0..*    zero or more
    *       zero or more
    1..*    one or more

Preserve lower bounds.

Do not weaken:

    "one or more"

into:

    "*"

when `1..*` is supported.

Examples:

Requirement:

    "Each Order belongs to exactly one Customer."

Then the Customer end for each Order is:

    1

Requirement:

    "A Customer can have multiple Orders."

Then the Order collection is normally:

    0..*

unless the requirements explicitly state every Customer must have at least one Order.

Requirement:

    "An Order contains one or more CartItems."

Then:

    Order -> CartItem = 1..*

Requirement:

    "Each CartItem belongs to exactly one Order."

Then:

    CartItem -> Order = 1

Do not invent multiplicities when quantity cannot be justified from the
requirements.


RELATIONSHIP VALIDATION

Before emitting a relationship, verify:

1. Both endpoints belong inside the domain Class Diagram.
2. The relationship is supported by requirements or clear domain meaning.
3. The relationship type matches its semantics.
4. Composition is used only for justified strong ownership.
5. Aggregation is used only for justified weak ownership.
6. Inheritance represents a genuine is-a relationship.
7. Multiplicity is used only where structural quantity is meaningful.
8. Multiplicity preserves the exact lower and upper bounds from requirements.
9. The relationship does not merely reproduce application-layer communication.
10. The same relationship is not duplicated without a distinct semantic reason.


HLD SEPARATION

Treat supplied HLD information as architectural context, not as a list of Class
Diagram classes.

HLD may describe components such as:

    FrontendUI
    Controller
    Service
    Repository
    API Gateway
    Database
    external services

Use this information to understand the system boundary and responsibilities.

Do NOT automatically copy those components into the Class Diagram.

Their interactions should normally be represented by:

- HLD/component architecture
- Sequence Diagrams

rather than the domain Class Diagram.


CROSS-DIAGRAM CONSISTENCY

The Class Diagram establishes the canonical DOMAIN structural vocabulary.

It provides:

- domain class names
- domain attributes
- domain behavior
- domain relationships
- domain multiplicities

Later ER generation should use persistent domain concepts from this Class Diagram.

Later Sequence generation may contain additional architectural or external
participants that are intentionally absent from the Class Diagram, including:

- actors
- frontend applications
- Controllers
- Services
- Repositories
- external systems
- third-party services

Therefore, a Sequence participant is NOT required to exist in the Class Diagram
when it represents an architectural or external participant.

Example:

A Sequence Diagram may contain:

    Customer
    FrontendUI
    OrderController
    DatabaseRepository
    Order

while the Class Diagram contains only:

    Customer
    Order
    CartItem

This is valid because the diagrams have different modeling responsibilities.


SEQUENCE METHOD CONSISTENCY

When a Sequence message invokes a DOMAIN object:

- the domain class must exist in the Class Diagram
- the invoked domain method should match a method defined in the Class Diagram

Example:

    OrderController -> Order: calculateTotalPrice()

requires:

    Order.calculateTotalPrice()

in the Class Diagram.

However, methods belonging to architectural participants that are intentionally
outside the Class Diagram may be derived from the supplied HLD, API contracts,
and use cases.

Examples:

    FrontendUI -> OrderController: submitCheckout(request)
    OrderController -> DatabaseRepository: createOrder(order)
    OrderController -> DatabaseRepository: createCartItem(cartItem)

These methods do NOT require OrderController or DatabaseRepository to be inserted
into the domain Class Diagram.


ER BOUNDARY

Later ER generation should map persistent domain/data concepts.

Classes such as:

    Customer
    Order
    CartItem

may become ER entities when persistence is required.

Do not create ER entities for:

- Controllers
- Services
- Repositories
- frontend applications
- actors
- external systems
- infrastructure components

The ER Diagram represents persistent data structure, not application architecture.


FINAL CHECK

Before returning the Class Diagram IR, verify:

- the diagram is domain-oriented rather than an HLD duplicate
- every class belongs to the domain model
- frontend applications are excluded
- Controllers are excluded unless explicitly requested for internal class design
- Services are excluded unless explicitly requested for internal class design
- Repositories are excluded unless explicitly requested for internal class design
- actors are included only when independently justified as domain concepts
- every attribute represents justified domain state
- every method represents justified domain behavior
- persistence/application orchestration methods were not placed on domain classes
- every relationship represents genuine domain structure
- relationship types match their semantics
- multiplicities exactly preserve requirement meaning
- `1..*` is preserved when requirements say "one or more"
- no architectural dependency was incorrectly modeled as a domain relationship
- canonical class and domain method names are stable for downstream diagrams
- no speculative classes, methods, attributes, or relationships were introduced

Return only the Class Diagram portion required by the UML IR schema.
""".strip(),
)
