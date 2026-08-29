from __future__ import annotations

from skills.uml.skill import Skill


SEQUENCE_GENERATION_SKILL = Skill(
    name="sequence_generation",
    instructions="""
ROLE

Generate the Sequence Diagrams portion of the UML IR.

Sequence diagrams are the canonical behavioral realization of requirement-driven
use cases and must remain consistent with validated structural artifacts.


SOURCE OF TRUTH

- Requirements are the behavioral and semantic source of truth.
- The validated Class Diagram is the structural source of truth for internal
    participants and callable methods.
- The validated ER Diagram is the persistent-data source of truth.


SCOPE

- Generate sequence diagrams only for functional behaviors/use cases supported
    by the supplied requirements.
- Generate only the interactions necessary to explain the requirement.
- Do not add speculative flows, retries, or alternate paths unless required.


PARTICIPANTS

- Internal participants must use exact canonical Class Diagram names.
- Do not rename internal participants.
- Actors and external systems may participate without being internal domain
    classes when explicitly supported by the requirements.
- Every message sender and receiver must be declared as a participant.
- Keep participant lists minimal and behavior-relevant.


METHOD AND MESSAGE VALIDITY

- For calls to internal application classes, the called method MUST exactly match a method defined on the receiving class.
- Do not invent new internal methods during Sequence generation.
- Use method names exactly as defined in the Class Diagram canonical vocabulary.
- If required behavior cannot be represented because an appropriate Class method
    does not exist, do not silently invent one; represent the diagram as
    faithfully as possible and allow validation to report the structural
    inconsistency.


CALL DIRECTION AND RESPONSIBILITY

- Preserve architectural call direction where justified, for example
    Boundary -> Controller -> Service -> Repository, but do not force layers that
    are absent from the Class Diagram.
- Avoid role leakage, such as UI participants invoking persistence-level
    operations directly, unless explicitly required.
- Repository interactions should concern persistent concepts represented in the ER Diagram when applicable.


CONTROL FLOW STRUCTURES

- Use alt, opt, loop, or other logic structures only when required by the
    behavior.
- Avoid duplicating the same interaction in both top-level messages and nested
    logic blocks.
- Keep logic blocks semantically meaningful and condition labels concise.


CONSISTENCY RULES

- Ensure message flow aligns with requirement intent and class responsibilities.
- Keep naming stable across Class, ER, and Sequence artifacts.
- Do not introduce hidden domain concepts via participant or message names.


QUALITY BAR

- Prioritize correctness, traceability, and minimal complete behavior.
- Prefer one clear diagram per use case over one oversized diagram containing
    loosely related flows.
""".strip(),
)
