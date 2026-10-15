import os
import sys
import unittest
import inspect
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

import graph.candidate_prompts as candidate_prompts  # noqa: E402
from graph.candidate_prompts import (  # noqa: E402
    build_class_prompt,
    build_er_prompt,
    build_sequence_prompt,
)
from skills.uml import SkillRegistry  # noqa: E402


REQUIREMENTS = "REQ-001: Customers can place orders and cancel pending orders."
REQ_IDS = ["REQ-001", "REQ-002"]
CLASS_DIAGRAM = {
    "classes": [
        {
            "name": "Order",
            "attributes": ["orderId", "status"],
            "methods": ["cancelOrder()"],
        },
        {
            "name": "OrderService",
            "attributes": [],
            "methods": ["placeOrder()", "cancelOrder()"],
        },
        {
            "name": "OrderRepository",
            "attributes": [],
            "methods": ["saveOrder()", "findOrder()"],
        },
    ],
    "relationships": [
        {
            "source": "OrderService",
            "target": "OrderRepository",
            "type": "dependency",
            "cardinality": "",
        }
    ],
}
ER_DIAGRAM = {
    "entities": [
        {
            "name": "Order",
            "attributes": ["orderId", "status"],
            "primary_key": "orderId",
        }
    ],
    "relationships": [],
}


def build_phase2_class_prompt_baseline(requirements: str, requirement_ids: list[str] | None = None) -> str:
    common = SkillRegistry().get("common_uml").instructions
    req_ids = ", ".join(requirement_ids or [])
    return f"""
{common}

ROLE
You are the Class Diagram Generation Agent for a dependency-aware UML candidate pipeline.
Generate only the Class Diagram portion of the UML Intermediate Representation (IR).

INPUT
Requirement IDs:
{req_ids}

Requirements:
{requirements}

GOAL
Generate the smallest complete structural model that supports the supplied requirements.
The Class Diagram is the structural source of truth for later ER and Sequence generation.
Its class names, method names, domain concepts, and architectural participants must remain stable.
Method names defined here become the canonical method vocabulary for later Sequence generation.

DESIGN RULES
- Every class must be justified by a requirement or explicit architectural responsibility.
- Do not invent unsupported classes, responsibilities, functionality, or abstractions.
- Do not create a one-class-per-requirement mapping unnecessarily.
- A single class may support multiple requirements when its responsibility naturally covers them.
- Multiple classes may support one requirement when the architecture or behavior requires collaboration.
- Include a component as a class only when it represents a meaningful structural participant required by the requirements or explicitly stated architecture.
- Do not automatically create FrontendUI, Controller, Service, Repository, Database, DTO, Manager, Utility, Adapter, or Interface classes unless justified.
- Do not create empty placeholder classes.
- Respect architectural responsibilities explicitly stated in the requirements.
- When Controller / Service / Repository layers are present: Controller handles incoming requests and use-case coordination; Service handles business/application logic; Repository handles persistence/data access; Domain entities represent domain state and, when appropriate, domain behavior; Boundary/UI components represent user or external-system interaction.
- Do not force these layers if the requirements do not justify them.
- Domain classes are not limited to persistence; include domain behavior only when requirements imply it.
- Attributes represent meaningful state.
- Do not invent framework, configuration, or audit attributes unless requirements justify them.
- Avoid attributes in Controller, Service, or Repository classes unless structurally meaningful.
- Methods must represent requirement-supported behavior and use camelCase.
- Write methods as concise signatures such as methodName().
- Avoid arbitrary CRUD operations.
- Avoid generic methods such as process(), handle(), manage(), execute(), or doSomething() unless specifically justified.
- Later Sequence messages to internal classes must reuse the exact receiver method names defined here; choose stable canonical method names.
- Class names use PascalCase.
- Use one canonical name per concept and avoid synonyms for the same domain concept.
- Allowed relationship types: association, aggregation, composition, inheritance, dependency.
- Use inheritance only for genuine is-a relationships.
- Use composition only for strong lifecycle ownership.
- Use aggregation only for weak ownership.
- Use dependency for temporary usage.
- Use association as the default general structural relationship.
- Every relationship endpoint must reference an existing class.
- Do not add decorative relationships.
- The current IR uses one relationship cardinality field. This is ambiguous about relationship ends, so include cardinality only when clearly inferable and keep it simple.
- Prefer requirement coverage, correct responsibilities, consistency, and minimum necessary complexity.

OUTPUT SCHEMA

{{
  "class_diagram": {{
    "classes": [
      {{
        "name": "string",
        "attributes": ["string"],
        "methods": ["string"]
      }}
    ],
    "relationships": [
      {{
        "source": "string",
        "target": "string",
        "type": "association",
        "cardinality": "string"
      }}
    ]
  }}
}}

Allowed cardinality values include "1", "0..1", "1..*", and "0..*".

FINAL CHECK
Before returning JSON, ensure the model is requirement-driven, minimally complete, consistently named, responsibility-correct, and usable as the structural source of truth for ER and Sequence generation.
"""


class CandidatePromptTests(unittest.TestCase):
    def test_all_candidate_prompts_include_common_uml_skill(self):
        common = SkillRegistry().get("common_uml").instructions

        prompts = [
            build_class_prompt(REQUIREMENTS, REQ_IDS),
            build_er_prompt(REQUIREMENTS, CLASS_DIAGRAM),
            build_sequence_prompt(REQUIREMENTS, CLASS_DIAGRAM, ER_DIAGRAM),
        ]

        for prompt in prompts:
            self.assertIn(common, prompt)

    def test_class_prompt_includes_active_class_generation_skill(self):
        class_skill = SkillRegistry().get("class_generation").instructions
        prompt = build_class_prompt(REQUIREMENTS, REQ_IDS)

        self.assertIn(class_skill, prompt)

    def test_phase2_class_prompt_baseline_is_preserved_for_experiment_comparison(self):
        baseline = build_phase2_class_prompt_baseline(REQUIREMENTS, REQ_IDS)
        active = build_class_prompt(REQUIREMENTS, REQ_IDS)

        self.assertIn("DESIGN RULES", baseline)
        self.assertIn("FINAL CHECK", baseline)
        self.assertNotEqual(active, baseline)

    def test_common_uml_rules_are_not_duplicated_in_candidate_prompts(self):
        prompts = [
            build_class_prompt(REQUIREMENTS, REQ_IDS),
            build_er_prompt(REQUIREMENTS, CLASS_DIAGRAM),
            build_sequence_prompt(REQUIREMENTS, CLASS_DIAGRAM, ER_DIAGRAM),
        ]
        common_rules = [
            "Return ONLY valid JSON.",
            "Use the supplied requirements as the semantic source of truth.",
            "Do not introduce functionality, concepts, responsibilities, or data that are",
        ]

        for prompt in prompts:
            for rule in common_rules:
                self.assertEqual(prompt.count(rule), 1, rule)

    def test_class_prompt_has_required_source_and_architecture_rules(self):
        prompt = build_class_prompt(REQUIREMENTS, REQ_IDS)

        self.assertIn(REQUIREMENTS, prompt)
        for req_id in REQ_IDS:
            self.assertIn(req_id, prompt)
        self.assertIn('"class_diagram"', prompt)
        self.assertIn('"classes"', prompt)
        self.assertIn('"relationships"', prompt)
        self.assertIn("canonical DOMAIN structural vocabulary", prompt)
        self.assertIn("Controllers, repositories, frontend applications, APIs, infrastructure components", prompt)
        self.assertIn("Do not add Controllers, Services, Repositories, or UI components merely to show", prompt)
        self.assertIn("Methods defined here become canonical DOMAIN method names for downstream", prompt)
        self.assertIn("Keep names stable for downstream ER and Sequence generation", prompt)
        self.assertIn("Class names use PascalCase", prompt)
        self.assertIn("Methods represent requirement-supported DOMAIN behavior.", prompt)
        self.assertIn("Method names use camelCase.", prompt)
        for relationship_type in ["association", "aggregation", "composition", "inheritance", "dependency"]:
            self.assertIn(f"- {relationship_type}", prompt)
        self.assertIn("Every generated class, attribute, method, and relationship must be supported by", prompt)
        self.assertIn("Generate the smallest complete domain model supported by the requirements", prompt)

    def test_class_prompt_removes_contradictory_and_domain_biased_rules(self):
        prompt = build_class_prompt(REQUIREMENTS, REQ_IDS)

        self.assertNotIn("Controller MUST handle all business logic", prompt)
        self.assertNotIn("payload validation, and calculations", prompt)
        self.assertNotIn("Any component acting in the system", prompt)
        self.assertNotIn("must be included as a Class", prompt)
        self.assertNotIn("pre-existing", prompt.lower())
        self.assertNotIn("Patient", prompt)
        self.assertNotIn("Doctor", prompt)
        self.assertNotIn("Appointment", prompt)
        self.assertNotIn("Prescription", prompt)
        self.assertNotIn("processPayment", prompt)
        self.assertNotIn("DESIGN RULES", prompt)

    def test_er_prompt_has_persistence_rules_and_inputs(self):
        prompt = build_er_prompt(REQUIREMENTS, CLASS_DIAGRAM)

        self.assertIn(REQUIREMENTS, prompt)
        self.assertIn('"class_diagram"', prompt)
        self.assertIn('"OrderService"', prompt)
        self.assertIn('"er_diagram"', prompt)
        self.assertIn('"entities"', prompt)
        self.assertIn('"primary_key"', prompt)
        self.assertIn("Normally include persistent domain/data concepts", prompt)
        self.assertIn("Controller", prompt)
        self.assertIn("When an explicit entity identifier is supplied, represent it as the primary key", prompt)
        self.assertIn('"name": "semantic relationship verb or verb phrase"', prompt)
        self.assertIn('"source_multiplicity"', prompt)
        self.assertIn('"target_multiplicity"', prompt)
        self.assertIn("relationship names are not cardinality labels", prompt)
        self.assertNotIn("pre-existing", prompt.lower())
        self.assertNotIn("modifications to a pre-existing table structure", prompt)

    def test_sequence_prompt_has_exact_participant_method_and_logic_rules(self):
        prompt = build_sequence_prompt(REQUIREMENTS, CLASS_DIAGRAM, ER_DIAGRAM)

        self.assertIn(REQUIREMENTS, prompt)
        self.assertIn('"class_diagram"', prompt)
        self.assertIn('"er_diagram"', prompt)
        self.assertIn('"sequence_diagrams"', prompt)
        self.assertIn('"participants"', prompt)
        self.assertIn('"messages"', prompt)
        self.assertIn('"OrderRepository"', prompt)
        self.assertIn("When invoking a domain object, use the exact canonical method", prompt)
        self.assertIn("method names must match exactly", prompt)
        self.assertIn("Do not invent a ValidationService unless supplied by the architecture", prompt)
        self.assertIn("Include a participant only when it sends or receives at least one meaningful message", prompt)
        self.assertIn("Repository operations should be initiated by the use-case coordinator", prompt)
        self.assertIn("Repeated collection processing MUST use a LOOP fragment", prompt)
        self.assertIn("success occurs only after all mandatory work finishes", prompt)
        self.assertNotIn('"FrontendUI": "boundary"', prompt)
        self.assertIn('"<participant_name>": "<participant_type>"', prompt)

    def test_stage_skill_activation_includes_common_class_er_and_sequence(self):
        registry = SkillRegistry()
        self.assertEqual(registry.get("class_generation").name, "class_generation")
        self.assertEqual(registry.get("er_generation").name, "er_generation")
        self.assertEqual(registry.get("sequence_generation").name, "sequence_generation")

        source = inspect.getsource(candidate_prompts)
        self.assertIn('get("common_uml")', source)
        self.assertIn('get("class_generation")', source)
        self.assertIn('get("er_generation")', source)
        self.assertIn('get("sequence_generation")', source)

    def test_class_prompt_does_not_duplicate_active_class_skill_rules(self):
        prompt = build_class_prompt(REQUIREMENTS, REQ_IDS)
        rules = [
            "Class names use PascalCase.",
            "Methods represent requirement-supported DOMAIN behavior.",
            "Method names use camelCase.",
            "Do not add Controllers, Services, Repositories, or UI components merely to show",
        ]

        for rule in rules:
            self.assertEqual(prompt.count(rule), 1, rule)


if __name__ == "__main__":
    unittest.main()
