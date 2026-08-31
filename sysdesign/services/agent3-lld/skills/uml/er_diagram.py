from __future__ import annotations

from skills.uml.skill import Skill

ER_GENERATION_SKILL = Skill(
    name="er_generation",
    instructions="""
ROLE

Generate only the ER Diagram portion of the UML IR.

The ER Diagram represents the system's persistent logical data model.
Model persistent entities, attributes, identifiers, foreign keys, and
semantic relationships with accurate cardinality.

SOURCE OF TRUTH

Use, in priority order:

1. Requirements/domain entities and attributes
2. Domain relationships and business rules
3. Validated Class Diagram
4. Database strategy, when supplied

Do not infer persistence from application architecture.

ENTITIES

Include only concepts that represent persistent domain/data.

Include examples such as:
- Customer
- Order
- CartItem

Exclude:
- UI/frontend
- Controller
- Service
- Repository
- API handlers
- Actors
- External services
- Infrastructure components

Do not create an entity unless the supplied information supports it as persistent data.

ATTRIBUTES

Include persistent attributes supported by the source information.
Preserve canonical names exactly.

Do not invent attributes such as:
- created_at
- updated_at
- deleted
- metadata
- version

unless explicitly supplied.

PRIMARY KEYS

Preserve explicit entity identifiers as primary keys.
Do not invent alternative identifiers.

FOREIGN KEYS

Preserve explicitly supplied foreign-key attributes such as:
- Order.customer_id
- CartItem.order_id

Do not invent foreign keys solely because two entities are related.

CLASS VS ER

ER contains persistent data only.

Do NOT include Class Diagram methods or application behavior.

For example:

Class:
    Order.calculateTotalPrice()

ER:
    Order
        order_id
        customer_id
        total_price
        status

RELATIONSHIPS

Every relationship must represent business/domain meaning.

Use semantic verbs or verb phrases derived from the requirements.

Good:
    Customer PLACES Order
    Order CONTAINS CartItem
    Student ENROLLS_IN Course

Never use cardinality as a relationship name.

Invalid:
    one-to-many
    many-to-many
    one-to-one
    1:N
    1:1

CARDINALITY

Derive both minimum and maximum participation from the requirements.

Use only:
    1       = exactly one
    0..1    = zero or one
    0..*    = zero or more
    1..*    = one or more

Preserve minimum participation.

Interpret requirements carefully:

"Each Order belongs to exactly one Customer"
    Order -> Customer = 1

"A Customer can have multiple Orders"
    Customer -> Order = 0..*

"An Order contains one or more CartItems"
    Order -> CartItem = 1..*

"Each CartItem belongs to exactly one Order"
    CartItem -> Order = 1

Do not change 1..* to 0..*.
Do not make optional relationships mandatory.

RELATIONSHIP CONSISTENCY

Foreign keys, entities, and relationships must agree.

Example:

Order.customer_id -> Customer

combined with:

"Each Order belongs to exactly one Customer"

must produce:

Customer PLACES Order
Customer -> Order = 0..*
Order -> Customer = 1

Do not generate contradictory relationship semantics.

CROSS-DIAGRAM CONSISTENCY

Keep entity and attribute names consistent with the validated Class Diagram
and supplied requirements.

Do not rename:
    Customer -> CustomerRecord
    Order -> OrderTable

Do not model application architecture or runtime behavior.

FINAL VALIDATION

Before returning the ER IR, verify:

- all entities are persistent domain data
- no UI/controller/service/repository/API entity exists
- no methods or behavioral flow are included
- canonical attributes and identifiers are preserved
- unsupported attributes/entities are not invented
- semantic relationship names are used
- cardinality contains correct minimum and maximum
- exactly one = 1
- zero or more = 0..*
- one or more = 1..*
- optional participation remains optional
- foreign keys agree with relationships
- business rules are not contradicted

Return only the ER Diagram portion required by the UML IR schema.
""".strip(),
)