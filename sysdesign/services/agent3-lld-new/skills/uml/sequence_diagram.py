from __future__ import annotations

from skills.uml.skill import Skill

SEQUENCE_GENERATION_SKILL = Skill(
    name="sequence_generation",
    instructions="""
ROLE

Generate the Sequence Diagram portion of the UML IR.

A Sequence Diagram represents the runtime interaction required to execute a use case.

Show only participants and messages that actively contribute to the use case.
Preserve the required behavioral order exactly.


SOURCE OF TRUTH

Use:

Requirements/use cases:
    required behavior and causal order

Business rules:
    mandatory domain constraints

HLD:
    architectural participants and system boundaries

API contracts:
    request/response operations and payloads

Validated Class Diagram:
    canonical domain classes and domain methods

Validated ER Diagram:
    persistent domain concepts

Do not require every Sequence participant to exist in the Class Diagram.
Architectural and external participants may legitimately exist only in the Sequence Diagram.


PARTICIPANTS

Possible participant roles:

Actor:
    human/external initiator

Boundary:
    frontend, UI, mobile/web client

Controller:
    receives requests and coordinates the use case

Service:
    coordinates application/business behavior when explicitly supplied

Repository:
    performs persistence/data access

Domain Object:
    performs domain behavior defined by the Class Diagram

External System:
    explicitly required third-party/external dependency

Database:
    actual database/storage only when explicitly supplied

Include a participant only when it sends or receives at least one meaningful message.

Do not add unused lifelines merely because a class/entity exists elsewhere.


ARCHITECTURAL BOUNDARIES

Preserve the supplied HLD interaction path.

If HLD provides:

    FrontendUI
    OrderController
    DatabaseRepository

normally preserve:

    Customer -> FrontendUI
    FrontendUI -> OrderController

Do not bypass OrderController and invoke domain/repository behavior directly from
FrontendUI unless the architecture explicitly says so.

Persistence should flow through the supplied Repository.

A domain object must not coordinate persistence when a Controller or Service owns
the use case.


RESPONSIBILITY OWNERSHIP

Frontend/Boundary:
- receives user input
- sends application/API requests
- presents responses

Controller:
- receives requests
- performs request-level coordination
- invokes domain operations
- invokes persistence operations
- returns application responses

Service:
- performs application/business orchestration when explicitly supplied

Domain Object:
- performs domain behavior
- does not coordinate application persistence

Repository:
- performs persistence/data access

Do not move responsibilities between these roles without requirement justification.


DOMAIN METHOD CONSISTENCY

When invoking a domain object, use the exact canonical method from the validated
Class Diagram.

Example:

Class Diagram:

    Order.validateCartNotEmpty()
    Order.calculateTotalPrice()

Sequence must use:

    OrderController -> Order: validateCartNotEmpty()
    OrderController -> Order: calculateTotalPrice()

Do not rename these operations.


ARCHITECTURAL METHODS

Controllers, Services, Repositories, and Frontend components may intentionally
not appear in the domain-oriented Class Diagram.

Their methods may be derived from:

- HLD
- API contracts
- use-case steps

Use concrete names such as:

    submitCheckout(request)
    createOrder(order)
    createCartItem(cartItem)

Avoid vague methods such as process(), manage(), handle(), or execute() unless
explicitly required.


REQUEST FLOW

Preserve required request information.

If an API contract contains:

    customer_id
    cart_items

then represent that information or a clearly equivalent request object.

For example:

    Customer -> FrontendUI:
        submitCheckout(customer_id, cart_items)

    FrontendUI -> OrderController:
        submitCheckout(request)

Do not silently discard required request data.


CAUSAL ORDER

Use-case steps define mandatory execution order.

Every required step must complete before a later dependent step occurs.

Example:

1. submit checkout
2. validate cart/request
3. calculate total
4. create Order
5. create CartItems
6. return success

The Sequence Diagram MUST preserve:

    submit
      ->
    validate
      ->
    calculate
      ->
    create Order
      ->
    create CartItems
      ->
    success response

NEVER emit a success response before all mandatory preceding operations complete.


VALIDATION

If a required validation is domain behavior already defined in the Class Diagram,
invoke that domain method.

Example:

    Order.validateCartNotEmpty()

If request-level validation belongs to the Controller and is explicitly required,
a Controller self-message may be used.

Do not invent a ValidationService unless supplied by the architecture.


LOOPS

Repeated collection processing MUST use a LOOP fragment.

Phrases such as:

- for each
- for every
- each item
- repeat for
- iterate through

indicate iteration.

Example:

    loop [for each cart item]

        OrderController -> DatabaseRepository:
            createCartItem(cartItem)

    end

Do NOT represent iteration using `alt`.

This is invalid:

    alt [for each cart item]

`alt` represents conditional alternatives, not repetition.


ALTERNATIVES

Use `alt` only for genuine mutually exclusive branches such as:

    success / failure
    authorized / unauthorized
    available / unavailable

Do not use `alt` for:

- loops
- sequential behavior
- collection processing
- normal mandatory operations

Do not invent alternative branches not supported by requirements.


RETURN MESSAGES

Responses must originate from the participant responsible for the request.

If:

    FrontendUI -> OrderController:
        submitCheckout(request)

then the application response normally returns:

    OrderController --> FrontendUI:
        successResponse(...)

Do not return the response from Order or Repository unless explicitly justified.

Most importantly:

A success response MUST be emitted only after every mandatory operation in the
successful main flow has completed.


PERSISTENCE

Repository operations should be initiated by the use-case coordinator.

Example:

    OrderController -> DatabaseRepository:
        createOrder(order)

    loop [for each cart item]

        OrderController -> DatabaseRepository:
            createCartItem(cartItem)

    end

Avoid:

    Order -> DatabaseRepository:
        persistOrder()

when the Controller owns orchestration.


REPOSITORY VS DATABASE

A Repository is NOT a database.

DatabaseRepository is an application persistence abstraction and should be rendered
as a normal repository/object participant.

Do not classify a participant as a database merely because its name contains
"Database".

Only use a database/storage participant type when the input explicitly describes an
actual database or storage system.


DOMAIN OBJECT LIFELINES

Do not include an entity merely because it is persisted.

Example:

CartItem does not need its own lifeline if no CartItem method is invoked.

It can be passed as data:

    OrderController -> DatabaseRepository:
        createCartItem(cartItem)

Domain participants should appear when they perform meaningful runtime behavior.


MESSAGE DIRECTION

Preserve responsibility direction.

Typical flow:

    Actor -> Frontend
    Frontend -> Controller
    Controller -> Domain Object
    Controller -> Repository

Do not generate:

    Repository -> Controller
    Domain Entity -> Frontend
    Frontend -> Repository

unless explicitly justified.


CROSS-DIAGRAM CONSISTENCY

For domain participants:

- class name must match the validated Class Diagram
- invoked domain methods must exist in the Class Diagram
- method names must match exactly

For persistent domain concepts:

- preserve canonical names from Class/ER diagrams

For architectural participants:

- preserve HLD names and responsibilities

External participants may appear without being Class Diagram classes.


DIAGRAM RENDERING

- Hide the sequence diagram footbox.
- The generated Sequence Diagram must use the `hide footbox` directive.


FINAL CHECK

Before returning each Sequence Diagram verify:

- every mandatory use-case step is represented
- causal ordering matches the use case
- HLD boundaries are preserved
- Controller/Service owns orchestration
- domain objects perform domain behavior only
- Repository owns persistence
- Repository is not mistaken for the physical database
- domain methods exactly match Class Diagram methods
- repeated behavior uses `loop`
- `alt` is used only for actual conditional alternatives
- success occurs only after all mandatory work finishes
- every included participant has a visible lifeline
- response/return messages use dotted or dashed lines
- sequence diagram footbox is hidden
- no unused lifelines exist
- no unsupported participant or message was invented

Return only the Sequence Diagram portion required by the UML IR schema.
""".strip(),
)
