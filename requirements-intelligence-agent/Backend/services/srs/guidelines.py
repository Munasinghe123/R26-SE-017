
PURPOSE_GUIDELINES = """
Describe the purpose of the software to be specified.

Clearly state why the software exists and what the Software Requirements Specification is intended to define.

Do not describe features, requirements or implementation details.
"""

SCOPE_GUIDELINES = """
Describe the scope of the software under consideration by:

- Identifying the software product.
- Explaining what the software will do.
- Describing the application of the software, including its relevant objectives and benefits.
"""

PRODUCT_PERSPECTIVE_GUIDELINES = """
Describe the relationship of the software system to other products or systems.

If the software is part of a larger system, describe that relationship only when it can be inferred from the provided requirements.

Describe the following only if supported by the provided requirements:

- System interfaces
- User interfaces
- Hardware interfaces
- Software interfaces
- Communication interfaces
- Memory
- Operations
- Site adaptation requirements
- Interfaces with external services

Do not invent architectures, external systems, interfaces, deployment environments or technical details that are not supported by the provided requirements.

If information for a field cannot be inferred, leave that field empty.
"""


PRODUCT_FUNCTIONS_GUIDELINES = """
Provide a summary of the major functions that the software performs.

Base the summary on the provided Functional Requirements.

Provide a concise, high-level summary of the software capabilities.

Do not repeat the Functional Requirements verbatim.

Do not include implementation details or technical design.
"""


USER_CHARACTERISTICS_GUIDELINES = """
Describe the general characteristics of the intended groups of users.

For each user group:

- Identify the user group.
- Describe the general characteristics that are relevant to using the software.

Do not describe specific software requirements.

Only include characteristics that can be reasonably inferred from the available information.
"""


ASSUMPTIONS_AND_DEPENDENCIES_GUIDELINES = """
Identify assumptions and dependencies that affect the requirements stated in the SRS.

These assumptions and dependencies are not design constraints.

Describe only assumptions and dependencies that can be supported by the available information.
"""



