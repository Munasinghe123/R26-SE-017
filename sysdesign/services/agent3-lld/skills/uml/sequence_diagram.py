
from __future__ import annotations

from skills.uml.skill import Skill


SEQUENCE_GENERATION_SKILL = Skill(
    name="sequence_generation",
    instructions="""
ROLE

Generate only the Sequence Diagram portion of the UML IR.

Represent the runtime interactions required to execute
a specific requirement-supported use case.

Generate the smallest COMPLETE behavioral sequence.

Preserve correct participants, responsibilities,
method contracts, data flow, and causal order.

Follow the supplied UML IR schema exactly.


SOURCE PRIORITY

Use the following sources:

1. Requirements and use cases:
   Required behavior, inputs, conditions, and order.

2. Business rules:
   Mandatory constraints and preconditions.

3. Valid HLD:
   Architectural components and interaction paths.

4. API contracts:
   Request/response operations and payloads.

5. Validated Class Diagram:
   Canonical domain classes and domain methods.

6. Validated ER Diagram:
   Persistent domain concepts and relationships.

Requirements define required behavior.
HLD defines architecture when available.
Class Diagram defines canonical domain operations.

Do not invent details to fill missing information.


MISSING OR FAILED HLD

If HLD is missing, incomplete, or marked "Failed":

- Do not treat it as a valid architecture.
- Do not invent Controllers, Services, or Repositories.
- Do not assume a specific application framework.
- Do not invent a Frontend or API component.
- Do not claim architectural compliance.
- Use only explicitly justified participants.

If the use case cannot be represented without
unsupported architectural assumptions, it requires
upstream architectural correction.

Do not force application operations into domain
entities to compensate for a missing HLD.

The orchestration layer must handle unrecoverable
input failures before or after generation.


USE CASE SCOPE

Each Sequence Diagram represents one coherent use case.

Identify:
- Initiating actor or event.
- Required input information.
- Mandatory execution steps.
- Responsible participants.
- Required validations.
- Expected result.
- Relevant failure conditions.

Do not combine unrelated use cases.

Do not omit mandatory operations just to shorten
the sequence.

Do not add unrelated operations merely because
they appear elsewhere in the requirements.

If multiple use cases are supplied, represent
them separately when supported by the IR schema.

A single sequence does not need to include every
requirement in the entire project.


PARTICIPANTS

Allowed semantic participant roles:

actor:
Human or external initiator.

boundary:
User interface or external interaction boundary.

controller:
Receives requests and coordinates application calls.

service:
Performs application or business orchestration.

repository:
Performs persistence and data access.

entity:
Domain object with meaningful runtime behavior.

external_system:
Explicit external service or dependency.

database:
Actual database or storage system.

Use the exact role values supported by the IR schema.

Include only participants that actively send or
receive meaningful messages.

Every message endpoint must be declared.

Preserve canonical participant names.

Do not create duplicate participant instances.

Do not add participants solely to make diagrams
look architecturally complete.


PARTICIPANT CLASSIFICATION

Determine architectural roles from explicit HLD,
API contracts, or validated structural information.

Do not classify participants from names alone.

A Repository is not automatically a database.

A domain entity is not automatically a Service.

A Frontend is not automatically a Controller.

Domain-oriented Class Diagrams may intentionally
exclude architectural components.

Therefore, not every Sequence participant must
exist in the Class Diagram.

External and architectural participants may exist
only in the Sequence Diagram when justified.


RESPONSIBILITY OWNERSHIP

Boundary:
- Receives user input.
- Sends application requests.
- Presents results and progress.

Controller:
- Receives application requests.
- Coordinates use-case execution.
- Invokes supported application operations.
- Returns responses.

Service:
- Performs application/business orchestration.
- Coordinates processing when required.

Repository:
- Performs persistence and retrieval operations.

Domain Entity:
- Owns domain state.
- Performs intrinsic domain behavior.
- Enforces its own business invariants.

External System:
- Performs explicitly required external operations.

Respect the actual supplied architecture.

Do not invent architectural layers to match
a generic design pattern.


STRICT DOMAIN BOUNDARY

Domain entities must not substitute for missing
application components.

Do not assign the following to domain entities
unless genuinely supported as domain behavior:

- API request handling.
- Workflow orchestration.
- Database persistence or retrieval.
- AI extraction orchestration.
- Transcription orchestration.
- External service coordination.
- Document rendering.
- UI communication.

Invalid examples unless explicitly justified:

Meeting -> Meeting: processMeetingInformation()
Session -> Session: storeAnalysis()
Session -> Requirement: extractRequirement()
Requirement -> Document: generateDocument()

These represent inappropriate responsibility
assignments in a typical domain-oriented model.

Do not invent domain methods to complete a sequence.


METHOD CONSISTENCY

For every invocation of a domain object:

- The receiving class must exist in the
  validated Class Diagram.
- The invoked method must belong to that class.
- Preserve the exact canonical method name.
- Preserve supported parameters and their types.
- Preserve the declared return type.

Do not rename, invent, or paraphrase domain methods.

Do not invoke attributes as methods.

Do not call a domain method that is missing
from the validated Class Diagram.

If a required operation is absent, do not
silently modify the canonical Class Diagram.

The missing operation must be resolved
through upstream correction.


ARCHITECTURAL OPERATIONS

Architectural components may be absent from
the domain-oriented Class Diagram.

Their operations may come from:

- Valid HLD specifications.
- Explicit API contracts.
- Requirement-supported use-case actions.

Use specific operation names.

Examples:
submitMeeting(request)
extractRequirements(transcript)
saveSession(session)
generateSRS(requirements)

These examples are naming illustrations,
not mandatory operations or participants.

Avoid vague names such as:
process(), handle(), manage(), execute().

Do not invent operations unrelated to the use case.

Do not add architectural operations to
domain classes merely for name consistency.


METHOD CONTRACT VALIDATION

For each method call, validate:

1. The receiving participant owns the operation.
2. The operation is supported by source artifacts.
3. Parameter count and meaning are compatible.
4. Parameter types are compatible when specified.
5. Return data matches the declared return type.
6. Required input values are available.

A void method must not return data-bearing results.

Do not invent a response type incompatible
with the receiving operation.

Do not create undefined domain operations.

Preserve canonical signatures when supplied.


DATA FLOW

Every required value must have a valid origin.

Valid origins include:

- Initial user/request input.
- Earlier operation output.
- Explicitly modeled stored-state retrieval.
- Supplied architectural context.

Do not assume a participant already possesses
data that has never been passed or retrieved.

Preserve data required by later processing steps.

An identifier alone is not sufficient when
the receiver requires unavailable content.

Do not invent hidden data-transfer mechanisms.

Ensure that output from a processing operation
is available to its next dependent operation.


MESSAGE ORDER

Follow the exact causal order of the use case.

Mandatory operations must happen before
dependent operations.

Do not reorder operations for visual appearance.

Do not skip required validation.

Do not return success before required work finishes.

Respect business preconditions.

If document generation requires finalized
requirements, finalization must occur before
document generation.

Do not automatically generate documents during
an upload-only or extraction-only use case.


MESSAGE DIRECTION

Calls normally use solid messages.

Returns/responses use dashed messages.

Maintain the request/response relationship.

Example:

Frontend -> Controller: submitRequest(request)
Controller -> Service: performOperation(data)
Service --> Controller: result
Controller --> Frontend: response

This is illustrative, not a required architecture.

Return messages should represent results
from the corresponding operation.

Do not send a synchronous return directly to
an unrelated participant.

Do not represent a return as a new method call.

Asynchronous notifications are separate events
and must not be mislabeled as synchronous returns.


ACKNOWLEDGMENT VS COMPLETION

Distinguish:

- Submission acknowledgment.
- Processing progress.
- Processing success.
- Processing failure.

An acknowledgment confirms request receipt,
not successful completion of all processing.

For asynchronous operations, processing may
continue after acknowledgment.

Do not invent WebSockets, polling, queues,
or other transport technologies.

Use only explicitly supplied communication
mechanisms or architecture-neutral interactions
supported by the IR schema.


LOOPS

Use loop fragments for repeated interactions.

Examples of repetition:
- For each item.
- For every requirement.
- Repeated processing.
- Explicit retry operations.

Repeated messages must be inside the loop body.

Do not use alt to represent iteration.

Do not invent repetition when the use case
does not require it.

Preserve loop conditions when provided.


CONDITIONAL FRAGMENTS

Use alt for mutually exclusive branches.

Examples:
- Valid / invalid.
- Success / failure.
- Authorized / unauthorized.

Use opt for optional behavior when supported.

Do not use alt for sequential operations.

Do not place mandatory operations inside
optional branches without justification.

Do not invent unsupported business decisions.

When requirements explicitly require error reporting,
include relevant failure behavior for the use case.

Do not model every conceivable technical failure.


PERSISTENCE

Persistence operations belong to the supplied
persistence component.

Typical justified flow:

Controller -> Repository: saveRecord(record)

or:

Service -> Repository: saveRecord(record)

Use the actual HLD interaction path.

Do not assume every architecture has a Repository.

Do not make domain objects coordinate database access.

A domain object does not need a lifeline merely
because its data is saved or retrieved.


DOMAIN OBJECT LIFELINES

Include a domain object as a participant only
when it performs meaningful runtime behavior.

Do not include every Class Diagram entity.

Do not include every ER Diagram entity.

A domain object used only as data may be
represented in message parameters instead.

Example:

Controller -> Repository: saveRequirement(requirement)

This does not require a separate Requirement lifeline.

If a domain operation is invoked, the corresponding
class and method must exist in the Class Diagram.


LIFELINE AND ACTIVATION RULES

Every included participant must have a visible lifeline.

Do not create unused or duplicate lifelines.

Do not create bottom participant footboxes.

When activation information is represented by the IR:

- Activate the correct executing participant.
- Deactivate the same participant when its execution completes.
- Every activation MUST have a matching deactivation/completion.
- Nested self-calls must each be properly deactivated at completion.
- Never leave activations open or unbalanced at the end of the sequence.
- Do not deactivate an unactivated participant or an unrelated participant.

Do not invent activation fields unsupported
by the UML IR schema.

PlantUML rendering details must be handled
by the rendering layer when absent from the IR.


CROSS-DIAGRAM CONSISTENCY

Domain participants:
- Preserve Class Diagram names.
- Reuse canonical domain methods.
- Respect method signatures.

Persistent concepts:
- Preserve Class/ER domain terminology.
- Respect known relationships and constraints.

Architectural participants:
- Preserve valid HLD names and responsibilities.

External participants:
- Require explicit justification.

Do not require architectural participants to
appear in the domain-oriented Class Diagram.

Do not force ER relationships to become
runtime participant interactions.

Never contradict validated upstream artifacts.


FINAL VALIDATION

Before returning, verify:

1. The diagram represents one coherent use case.
2. Required behavioral steps are included.
3. Causal ordering is correct.
4. Participants are justified and declared.
5. No duplicate or unused participants exist.
6. Valid HLD boundaries are preserved.
7. Missing HLD was not silently invented.
8. Domain entities do not perform orchestration.
9. Persistence uses justified components.
10. Domain methods match the Class Diagram.
11. Method arguments and returns are compatible.
12. Required data is available at each step.
13. Request and return directions are valid.
14. Success follows mandatory operations.
15. Required preconditions are respected.
16. Repetition uses loop fragments.
17. Alternatives use conditional fragments.
18. Failure behavior matches requirements.
19. Asynchronous acknowledgment is not confused
    with processing completion.
20. All included participants have lifelines.
21. No unsupported methods or messages exist.
22. No speculative architecture was introduced.
23. Output conforms exactly to the UML IR schema.

Do not add unsupported JSON fields.

Return ONLY the Sequence Diagram portion
required by the UML IR schema.

Do not return markdown, explanations, or reasoning.
""".strip(),
)
