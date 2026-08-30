
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

7. Do not duplicate the same information across multiple fields unless
   the information genuinely belongs to both fields.

8. Functional and non-functional requirements must remain inside
   "specified_requirements".

9. External interfaces must remain separate from "specified_requirements".

10. Do not generate the final SRS document.
    This node only extracts structured information for the SRS generator.

11. Return ONLY valid JSON.
    Do not return markdown.
    Do not return explanations.
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
                "description": "The system shall ..."
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
                "description": "The system shall ..."
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







