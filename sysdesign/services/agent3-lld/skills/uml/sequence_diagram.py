from __future__ import annotations

from skills.uml.skill import Skill


SEQUENCE_GENERATION_SKILL = Skill(
    name="sequence_generation",
    instructions="""
ROLE

Generate only the Sequence Diagram portion of the UML IR.

The Sequence Diagram describes the runtime interaction required to execute
a supported use case.

SOURCE OF TRUTH

Use the supplied artifacts in this priority order:

1. Requirements / Use Cases
   - determine required behavior and execution order

2. HLD
   - determine architectural participants and interaction boundaries

3. Validated Class Diagram
   - determine canonical internal class names and callable methods

4. Validated ER Diagram
   - determine persistent domain concepts when persistence is involved


PARTICIPANTS

Include only participants that actively send or receive a message.

Preserve canonical names exactly.

Participant roles MUST come from the supplied architecture/class information.
Do not infer or rename a participant based only on its name.

Use these roles when supported by the source artifacts:

- actor
- boundary
- controller
- service
- repository
- entity
- external system

Every message sender and receiver MUST exist in the participant list.

Do not add unused participants.


PARTICIPANT RESPONSIBILITY

Use the supplied architecture.

Typical flow:

Actor -> Boundary -> Controller -> Service -> Repository

or:

Actor -> Boundary -> Controller -> Entity

Do not skip an architectural layer when the supplied HLD requires it.

Do not make Boundary call Repository directly unless explicitly required.

Do not make Entity coordinate persistence unless explicitly required.


CLASS AND METHOD CONSISTENCY

For internal classes:

- use the exact canonical Class Diagram class name
- use only methods that exist on the receiving class
- preserve method names exactly
- do not invent, rename, or paraphrase domain methods

Architectural methods may come from HLD, API contracts, or requirements
when the participant is not represented as a domain class.


MESSAGE ORDER

Preserve the exact causal order required by the use case.

Mandatory operations must occur before the final success response.

Do not reorder operations for visual convenience.

Do not omit required operations.


REQUEST DATA

Preserve required request parameters.

If the requirement/API specifies:

customer_id
cart_items

represent them explicitly or through an equivalent request object.

Do not silently remove required input data.


LOOPS

Use a LOOP fragment for repeated behavior.

The repeated message MUST be INSIDE the loop fragment.

Correct:

OrderController -> DatabaseRepository: createOrder(order)

loop [for each cart item]
    OrderController -> DatabaseRepository: createCartItem(cartItem)
end

Incorrect:

loop [for each cart item]

OrderController -> DatabaseRepository: createCartItem(cartItem)


Do not use alt for repetition.

Use alt only for genuine conditional branches.


RETURN MESSAGES

Calls are synchronous solid messages.

Returns/responses MUST be represented as return messages.

Return messages MUST use a dotted/dashed message representation in the IR.

Example:

FrontendUI -> OrderController: submitCheckout(request)

OrderController --> FrontendUI: successResponse(...)

Do not represent a return message as a solid call.

A success response MUST occur only after all mandatory operations complete.


LIFELINES

Every included participant MUST have exactly one continuous visible lifeline.

Do not create duplicate participant instances.

Do not create bottom participant headers or footboxes.

Do not omit a participant lifeline.


SEQUENCE STRUCTURE

For each use case, produce:

1. participant declarations
2. ordered messages
3. required loop/alt/opt fragments
4. return messages

Do not include unrelated interactions.

Do not add speculative participants or messages.


FINAL VALIDATION

Before returning the Sequence Diagram IR verify:

- participant names match canonical source names
- participant roles match supplied architecture
- every sender/receiver is declared
- every included participant has one lifeline
- no unused participant exists
- internal methods exist on the receiving class
- required parameters are preserved
- message order matches the use case
- loops contain the repeated messages
- alt is used only for conditional behavior
- return messages are marked as returns
- success occurs after mandatory operations
- no duplicate participant declarations exist
- no bottom participant/footbox representation is requested

Return only the Sequence Diagram portion required by the UML IR schema.
""".strip(),
)