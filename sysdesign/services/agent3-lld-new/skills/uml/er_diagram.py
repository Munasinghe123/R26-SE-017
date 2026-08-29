from __future__ import annotations

from skills.uml.skill import Skill

ER_GENERATION_SKILL = Skill(
    name="er_generation",
    instructions="""
ROLE

Generate the ER Diagram portion of the UML IR.

The ER Diagram represents the logical persistent data model of the system/module.

Model:

- persistent domain entities
- persistent attributes
- identifiers and supplied foreign-key attributes
- semantic entity relationships
- exact relationship cardinality/participation

Do not represent application architecture or runtime behavior.


SOURCE OF TRUTH

Use:

Requirements/domain entities:
    canonical persistent concepts and attributes

Domain relationships/business rules:
    relationship meaning and cardinality

Validated Class Diagram:
    canonical domain concepts and structural relationships

Database strategy:
    persistence context where supplied

Do not convert architectural components into ER entities.


ENTITY SELECTION

Normally include persistent domain/data concepts.

Examples:

    Customer
    Order
    CartItem

Normally exclude:

    FrontendUI
    Controller
    Service
    Repository
    API handler
    actor-only concepts
    external services
    infrastructure components

A concept should become an ER entity only when it represents persistent data.


CLASS VS ER BOUNDARY

The Class Diagram may contain domain behavior.

The ER Diagram contains persistent data structure only.

Do not copy Class Diagram methods into ER entities.

Example:

Class:

    Order.calculateTotalPrice()
    Order.validateCartNotEmpty()

ER Entity:

    Order
        order_id
        customer_id
        total_price
        status

Methods do not belong in ER.


ATTRIBUTES

Use persistent attributes supported by requirements.

Preserve supplied canonical attribute names.

Do not invent common fields such as:

    created_at
    updated_at
    deleted
    metadata
    version

unless explicitly supplied.

Do not add application/framework attributes.


PRIMARY KEYS

When an explicit entity identifier is supplied, represent it as the primary key.

Examples:

    Customer.customer_id
    Order.order_id
    CartItem.cart_item_id

Do not invent alternative identifiers when a canonical ID already exists.


FOREIGN KEYS

When foreign-key-style attributes are explicitly supplied by the domain/data
requirements, preserve them.

Examples:

    Order.customer_id
    CartItem.order_id

These attributes should remain consistent with the corresponding entity relationships.

Do not invent foreign-key attributes merely because two entities are related unless
the schema or requirements require them.


RELATIONSHIPS

Every ER relationship must describe BUSINESS/DOMAIN meaning.

Relationship names should be semantic verbs or verb phrases.

Good examples:

    Customer PLACES Order
    Order CONTAINS CartItem
    User OWNS Account
    Student ENROLLS_IN Course

Do NOT use cardinality as the relationship name.

Invalid relationship names:

    one-to-many
    many-to-many
    one-to-one
    1:N
    1:1

Cardinality describes quantity.
Relationship name describes meaning.

Use relationship descriptions and business rules to derive a concise semantic name.


CARDINALITY

Represent minimum and maximum participation precisely whenever supported by the IR.

Use:

    1       exactly one
    0..1    zero or one
    0..*    zero or more
    1..*    one or more

Do not discard minimum participation.

Do NOT convert:

    one or more

into merely:

    N
    *
    0..*

when `1..*` is supported.


CARDINALITY INTERPRETATION

Example:

    "Each Order belongs to exactly one Customer."

means:

    Order -> Customer = exactly 1

Example:

    "A Customer can have multiple Orders."

means:

    Customer -> Order = 0..*

unless the requirements explicitly require every Customer to have at least one Order.

Therefore:

    Customer 1 ----- 0..* Order


Example:

    "Each CartItem belongs to exactly one Order."

means:

    CartItem -> Order = exactly 1

Example:

    "An Order contains one or more CartItems."

means:

    Order -> CartItem = 1..*

Therefore:

    Order 1 ----- 1..* CartItem


MANDATORY PARTICIPATION

Words such as:

    exactly one
    must
    each X belongs to one Y
    one or more
    at least one

indicate mandatory participation.

Preserve those lower bounds.

For example:

    "An Order contains one or more CartItems."

must not produce:

    Order -> CartItem = 0..*

because that would allow an Order with no CartItems.


OPTIONAL PARTICIPATION

Words such as:

    may
    can have
    zero or more
    optionally

may indicate a lower bound of zero.

Do not make participation mandatory without requirement support.


RELATIONSHIP CONSISTENCY

Foreign-key-style attributes and ER relationships must agree.

If:

    Order.customer_id

references Customer, and requirements say each Order belongs to exactly one Customer,
the relationship must reflect that requirement.

If:

    CartItem.order_id

references Order, and every CartItem belongs to one Order, the relationship must
reflect exactly one Order per CartItem.

Do not generate contradictory attribute and relationship semantics.


RELATIONSHIP NAMING

Prefer names derived directly from requirement meaning.

Examples:

Requirement:

    "A Customer can have multiple Orders."

Relationship:

    PLACES

or another concise requirement-grounded semantic verb.

Requirement:

    "An Order contains one or more CartItems."

Relationship:

    CONTAINS

Do not invent unrelated domain semantics.


NO ARCHITECTURAL RELATIONSHIPS

Do not generate ER relationships involving:

    FrontendUI
    Controller
    Service
    Repository
    API
    external actor
    infrastructure component

ER relationships are between persistent domain/data entities.


NO METHODS

ER entities contain data, not application/domain methods.

Do not include:

    calculateTotalPrice()
    validateCartNotEmpty()
    submitCheckout()
    createOrder()

in the ER Diagram.


NO BEHAVIORAL FLOW

Do not model:

    request order
    sequence calls
    API calls
    loops
    validation flow
    orchestration

Those belong to Sequence Diagrams.


CROSS-DIAGRAM CONSISTENCY

Persistent domain names should remain consistent with the Class Diagram.

Examples:

    Customer
    Order
    CartItem

Do not rename these to:

    CustomerRecord
    OrderTable
    ShoppingOrder

unless explicitly required.

Persistent attributes should remain consistent with supplied requirements and the
validated domain model.


ORDER MANAGEMENT EXAMPLE

Given entities:

    Customer(customer_id)

    Order(
        order_id,
        customer_id,
        total_price,
        status
    )

    CartItem(
        cart_item_id,
        order_id,
        product_id,
        quantity
    )

and requirements:

    A Customer can have multiple Orders.
    Each Order belongs to exactly one Customer.
    An Order contains one or more CartItems.
    Each CartItem belongs to exactly one Order.

Expected semantic relationships:

    Customer PLACES Order

with:

    Customer -> Order = 0..*
    Order -> Customer = 1


    Order CONTAINS CartItem

with:

    Order -> CartItem = 1..*
    CartItem -> Order = 1

Do NOT name either relationship:

    one-to-many


FINAL CHECK

Before returning the ER Diagram verify:

- every entity represents persistent domain data
- no Controller/Service/Repository/UI component became an entity
- methods are excluded
- supplied identifiers are preserved
- supplied persistent attributes are preserved
- relationship names express semantic business meaning
- relationship names are not cardinality labels
- every cardinality preserves both minimum and maximum participation
- "one or more" remains `1..*`
- "exactly one" remains `1`
- optional participation is not made mandatory
- foreign-key attributes agree with relationships
- no relationship contradicts explicit business rules
- no unsupported entity, attribute, or relationship was invented

Return only the ER Diagram portion required by the UML IR schema.
""".strip(),
)
