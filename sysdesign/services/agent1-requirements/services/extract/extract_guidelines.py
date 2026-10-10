SPECIFIED_REQUIREMENTS_GUIDELINES = """
Extract software requirements explicitly stated or clearly expressed
in the meeting.

FUNCTIONAL REQUIREMENTS:

Functional requirements describe what the software must do.

Each functional requirement must:
- describe one independently identifiable behavior;
- be independently testable;
- begin with "The system shall...";
- preserve the meaning of the stakeholder statement.

NON-FUNCTIONAL REQUIREMENTS:

Non-functional requirements describe, how the system should perform.
Extract a non-functional requirement ONLY when the meeting explicitly
states a quality attribute or constraint that applies to the SOFTWARE
SYSTEM itself.

Do not classify project schedules, deadlines, delivery dates,
development timelines, milestones, priorities, or planning statements
as software non-functional requirements.

Examples include:

- performance
- security
- reliability
- availability
- usability
- scalability
- maintainability
- portability
- response time
- resource limitations
- software-specific operational constraints

CRITICAL DISTINCTION:

Information about the PROJECT is NOT a software requirement.

Do NOT classify the following as non-functional requirements:

- project deadlines
- development timelines
- delivery dates
- estimated completion dates
- project schedules
- development phases
- team schedules
- project plans
- project priorities
- business goals
- stakeholder preferences about when the project should be delivered

Do NOT transform project information into a software requirement.

Do NOT infer non-functional requirements from common software engineering
practice.

For example, do not generate security, scalability, reliability,
performance, or usability requirements unless the meeting provides
evidence for them.

EMPTY IS VALID:

If the meeting contains no explicit software non-functional requirements,
return an empty non_functional array.

Do not create an NFR merely because the output schema contains an
"non_functional" field.

For every functional or non-functional requirement, identify the exact
meeting statement(s) that provide evidence for that requirement.

Evidence MUST come directly from the provided transcript.

Do not create, paraphrase, or infer source evidence.

For both functional and non-functional requirements:

- use only evidence from the meeting;
- do not invent requirements;
- do not duplicate requirements;
- do not combine unrelated requirements;
- preserve the meaning of stakeholder statements.
"""
