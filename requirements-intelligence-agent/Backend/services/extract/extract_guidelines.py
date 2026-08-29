
PURPOSE_GUIDELINES = """
Extract the purpose of the software as expressed or clearly described in the meeting.
Describe why the software is being proposed or what problem it is intended to address.
Do not invent objectives, benefits or functionality that are not supported by the meeting.
"""

SCOPE_GUIDELINES = """
Extract the scope of the software discussed in the meeting.

Identify:
- what software/product is being considered;
- what the software is intended to do;
- the application or problem domain;
- objectives or benefits explicitly discussed.

Do not invent functionality or boundaries that are not supported by the meeting.
"""
PRODUCT_PERSPECTIVE_GUIDELINES = """
Extract information relevant to the Product Perspective section.

For each category below, extract information only when it is supported by
the meeting transcript.

- system_interfaces:
  Relationships or interactions between the software and other systems.

- user_interfaces:
  Information about how users interact with the software, when explicitly discussed.

- hardware_interfaces:
  Hardware devices or hardware interactions explicitly mentioned.

- software_interfaces:
  Other software applications or software components that the system interacts with.

- communications_interfaces:
  Communication mechanisms or communication requirements explicitly discussed.

- memory_constraints:
  Memory-related constraints explicitly mentioned.

- operations:
  Operational aspects of how the software is expected to operate or be used,
  when explicitly discussed.

- site_adaptation_requirements:
  Requirements related to adapting the software to different sites,
  locations or installations, when explicitly discussed.

- service_interfaces:
  Interfaces with external services explicitly mentioned.

Do not invent APIs, databases, architectures, hardware, protocols,
deployment environments or external services.

If a category is not supported by the meeting, return an empty array.
"""

PRODUCT_FUNCTIONS_GUIDELINES = """
Extract the major functions the software is intended to perform.

Provide a high-level summary of the major capabilities discussed in the meeting.

Do not copy functional requirements verbatim.

Do not include implementation details, algorithms, APIs or technical design.

Do not invent functions that are not supported by the meeting.

Return an array of concise descriptive strings.
"""

USER_CHARACTERISTICS_GUIDELINES = """
Extract the intended user groups and their general characteristics when
these are supported by the meeting.

For each user group:
- identify the user group;
- describe relevant characteristics or role explicitly discussed.

Do not invent education level, technical expertise, experience,
disabilities or other characteristics.

Do not state specific software requirements in this field.

If no user characteristics can be determined from the meeting, return an empty array.
"""

ASSUMPTIONS_AND_DEPENDENCIES_GUIDELINES = """
Extract assumptions and dependencies only when they are supported by
explicit statements in the meeting.

An assumption is a condition that stakeholders expect to remain true
and that affects the validity of the software requirements.

A dependency is an external system, service, process, resource, or
condition that the software explicitly relies upon.

STRICT RULES:

- Do not infer assumptions from normal business context.
- Do not invent assumptions about data accuracy, availability,
  infrastructure, users, or organizational processes.
- Do not treat an existing manual process as an external system dependency
  unless the meeting explicitly states that the new software will depend
  on that process or system.
- Do not convert requirements, goals, preferences, priorities, or
  business problems into assumptions or dependencies.
- If the meeting does not explicitly provide a genuine assumption or
  dependency, return an empty array.

Use only evidence from the meeting.
"""

SPECIFIED_REQUIREMENTS_GUIDELINES = """
Extract software requirements explicitly stated or clearly expressed
by the stakeholders in the meeting.

FUNCTIONAL REQUIREMENTS:

Functional requirements describe what the software must do.

Each functional requirement must:
- describe one independently identifiable system behavior;
- be independently testable;
- begin with "The system shall...";
- preserve the stakeholder's intended meaning.

If a stakeholder statement contains multiple independent behaviors,
split them into separate requirements when they can be tested
independently.

Do not combine unrelated behaviors into one requirement.

NON-FUNCTIONAL REQUIREMENTS:

Non-functional requirements describe quality attributes or constraints
that apply to the software system itself.

Extract an NFR ONLY when the meeting provides explicit evidence for it.

Examples include:
- performance
- response time
- security
- privacy
- reliability
- availability
- usability
- scalability
- maintainability
- portability

Security and privacy requirements should be classified as NFRs when
they describe how the system must protect information or control
access.

Do not infer NFRs from common software engineering practice.

Do not create security, performance, scalability, reliability,
usability, or other quality requirements unless the stakeholder
provides evidence for them.

PROJECT INFORMATION:

Project information is not automatically a software requirement.

Do not classify the following as NFRs:
- project deadlines
- development timelines
- delivery dates
- project schedules
- milestones
- budgets
- project priorities
- business goals
- planning statements

Do not convert project information into software requirements.

SCOPE:

Do not convert future considerations into current requirements.

If a feature is explicitly excluded from the current version,
do not create a requirement for that feature.

If a feature is only mentioned as a possible future feature,
do not treat it as a current requirement.

QUALITY:

- Do not invent requirements.
- Do not duplicate requirements.
- Do not combine unrelated requirements.
- Do not introduce stronger constraints than the stakeholder stated.
- Preserve the original meaning and level of certainty.
- Use only information supported by the meeting.

SOURCE EVIDENCE:

For every requirement, identify the exact meeting statement(s) that
provide evidence for it.

Evidence MUST come directly from the provided transcript.

Do not fabricate or infer source evidence.

EMPTY IS VALID:

If the meeting contains no functional requirements, return an empty
functional_requirements array.

If the meeting contains no non-functional requirements, return an
empty non_functional_requirements array.

Do not create requirements simply because the output schema contains
those fields.
"""



EXTERNAL_INTERFACES_GUIDELINES = """
Extract external interface information only when the meeting explicitly
describes an interface between the software and an external entity.

Relevant external entities may include:

- external software systems
- external applications
- hardware devices
- external services
- communication systems
- other systems with which the software exchanges information

Do not classify an ordinary user or user interaction as an external
interface.

User interaction belongs under the relevant user-interface information
and/or functional requirements.

For each external interface, extract only information explicitly
supported by the meeting, such as:

- interacting external entity
- purpose
- information exchanged
- protocol, format, or communication mechanism, if explicitly stated

Do not invent APIs, endpoints, protocols, data formats, integrations,
or external systems.

If no external system, application, device, service, or other external
interface is explicitly discussed, return an empty array.
"""

DESIGN_CONSTRAINTS_GUIDELINES = """
Extract design constraints explicitly imposed on the software by the meeting.

Examples may include:
- mandatory technologies;
- required platforms;
- mandated architectural constraints;
- compatibility requirements;
- organizational technical policies.

Do not invent technical constraints.

Do not treat ordinary implementation choices as constraints.

If no design constraints are explicitly supported by the meeting,
return an empty array.
"""

STANDARDS_COMPLIANCE_GUIDELINES = """
Extract standards, regulations, policies or compliance obligations explicitly
mentioned in the meeting that the software must satisfy.

Do not assume standards or regulations merely because they are common
for the application domain.

If no compliance requirements are mentioned, return an empty array.
"""

SUPPORTING_INFORMATION_GUIDELINES = """
Extract relevant supporting information explicitly provided during the meeting
that may help understand or document the software requirements.

Examples include:
- important domain background;
- examples provided by stakeholders;
- sample inputs or outputs;
- contextual information;
- other supporting material discussed during elicitation.

Do not create requirements from supporting information unless the information
itself clearly expresses a requirement.

If no relevant supporting information is available, return an empty array.
"""
GLOBAL_RULES = """
STRICT EXTRACTION RULES:

1. Use ONLY the meeting transcript as evidence.

2. Do NOT use general software engineering assumptions to fill missing information.

3. Do NOT invent functionality, requirements, interfaces, architecture,
   technologies, databases, hardware, security mechanisms or constraints.

4. If information required by a field is not available in the transcript,
   return an empty string or empty array as appropriate.

5. Distinguish between:
   - information explicitly stated by stakeholders;
   - information that can be directly summarized from stakeholder statements;
   - information that would require speculation.

   Only the first two are allowed.

6. Preserve the meaning of stakeholder statements.

7. A single client statement must be classified as EITHER a functional
   requirement OR a non-functional requirement — never both.

   If a statement describes a system behavior (what the system does),
   classify it as functional.

   If the same statement also implies a quality attribute (how well/fast/
   securely it does it), that quality attribute may ALSO become a
   separate NFR only if it describes a distinct, independently
   verifiable quality constraint — not a restatement of the FR.

   Do not create an NFR whose source_evidence is identical or
   near-identical to an FR's source_evidence unless the NFR adds a
   quantifiable constraint not captured by the FR (e.g. a numeric
   threshold).

8. Functional and non-functional requirements must remain inside
   "specified_requirements".

9. External interfaces must remain separate from "specified_requirements".

10. Do not generate the final SRS document.
    This node only extracts structured information for the SRS generator.

11. Return ONLY valid JSON.
    Do not return markdown.
    Do not return explanations.
    
SPECULATIVE LANGUAGE:
If a stakeholder statement uses hedging or speculative language
("possibility," "may," "might," "could," "eventually," "in the future,"
"considering," "thinking about") to describe a feature, DO NOT create a
requirement from it — regardless of FR or NFR. Only extract requirements
from statements describing current, committed scope.

ATOMICITY CHECK:
Before finalizing a requirement, check if the description lists more than
one distinct capability, metric, or object (e.g. "reports on X, Y, Z, and W")
under a single "shall" statement. If so, split into separate requirements,
one per distinct capability — do not combine multiple reportable items,
data types, or actions into one requirement description.    
    
"""

OUTPUT_SCHEMA = """
Return exactly this JSON structure:

{
    "purpose": "",

    "scope": "",

    "product_perspective": {
        "system_interfaces": [],
        "user_interfaces": [],
        "hardware_interfaces": [],
        "software_interfaces": [],
        "communications_interfaces": [],
        "memory_constraints": [],
        "operations": [],
        "site_adaptation_requirements": [],
        "service_interfaces": []
    },

    "product_functions": [],

    "user_characteristics": [],

    "assumptions_and_dependencies": [],

    "specified_requirements": {
        "functional": [
            {
                "id": "FR-1",
                "description": "The system shall ...",
                "source_evidence": [
                  {
                    "speaker": "Client or Business Analyst",
                    "statement": "exact statement from the meeting transcript"
                    }
                ]
            }
        ],
        "non_functional": [
            {
                "id": "NFR-1",
                "description": "The system shall ...",
                "source_evidence": [
                  {
                    "speaker": "Client or Business Analyst",
                    "statement": "exact statement from the meeting transcript"
                    }
                ]
            }
        ]
    },

    "external_interfaces": [],

    "design_constraints": [],

    "standards_compliance": [],

    "supporting_information": []
}
"""







