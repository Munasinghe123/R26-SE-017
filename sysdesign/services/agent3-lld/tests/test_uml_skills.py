import os
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from skills.uml import Skill, SkillRegistry  # noqa: E402
from graph.candidate_prompts import (  # noqa: E402
    build_class_prompt,
    build_er_prompt,
    build_sequence_prompt,
)


class UMLSkillTests(unittest.TestCase):
    def test_skill_is_immutable(self):
        skill = Skill(name="example", instructions="Use clear instructions.")

        with self.assertRaises(FrozenInstanceError):
            skill.instructions = "mutated"

    def test_registry_returns_common_uml(self):
        skill = SkillRegistry().get("common_uml")

        self.assertEqual(skill.name, "common_uml")
        self.assertIn("Return ONLY valid JSON", skill.instructions)

    def test_registry_returns_class_generation(self):
        skill = SkillRegistry().get("class_generation")

        self.assertEqual(skill.name, "class_generation")
        self.assertIn("Class Diagram", skill.instructions)

    def test_registry_returns_er_generation(self):
        skill = SkillRegistry().get("er_generation")

        self.assertEqual(skill.name, "er_generation")
        self.assertIn("persistent domain/data concepts", skill.instructions)
        self.assertIn("relationship names are not cardinality labels", skill.instructions)
        self.assertIn("1..*", skill.instructions)

    def test_registry_returns_sequence_generation(self):
        skill = SkillRegistry().get("sequence_generation")

        self.assertEqual(skill.name, "sequence_generation")
        self.assertIn("When invoking a domain object, use the exact canonical method", skill.instructions)
        self.assertIn("Repeated collection processing MUST use a LOOP fragment", skill.instructions)
        self.assertIn("success occurs only after all mandatory work finishes", skill.instructions)

    def test_unknown_skill_raises_clear_error(self):
        with self.assertRaisesRegex(KeyError, "Unknown UML skill 'missing'"):
            SkillRegistry().get("missing")

    def test_each_skill_has_non_empty_instructions(self):
        for skill in SkillRegistry().all():
            self.assertTrue(skill.instructions.strip(), skill.name)

    def test_skill_names_are_unique(self):
        registry = SkillRegistry()
        names = [skill.name for skill in registry.all()]

        self.assertEqual(len(names), len(set(names)))

    def test_registry_rejects_duplicate_skill_names(self):
        duplicate_a = Skill("duplicate", "first")
        duplicate_b = Skill("duplicate", "second")

        with self.assertRaisesRegex(ValueError, "unique"):
            SkillRegistry([duplicate_a, duplicate_b])

    def test_registry_does_not_mutate_shared_skill_definitions(self):
        registry_a = SkillRegistry()
        registry_b = SkillRegistry()

        self.assertIs(registry_a.get("common_uml"), registry_b.get("common_uml"))
        self.assertEqual(
            registry_a.get("common_uml").instructions,
            registry_b.get("common_uml").instructions,
        )

    def test_importing_skill_system_has_no_provider_or_environment_side_effects(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("llm.factory.get_llm_provider") as provider_factory:
            import skills.uml as uml_skills

        self.assertTrue(hasattr(uml_skills, "SkillRegistry"))
        provider_factory.assert_not_called()

    def test_skill_import_does_not_change_active_candidate_prompts(self):
        requirements = "REQ-001: Customers can place orders."
        requirement_ids = ["REQ-001"]
        class_diagram = {
            "classes": [{"name": "Order", "attributes": ["id"], "methods": ["placeOrder()"]}],
            "relationships": [],
        }
        er_diagram = {
            "entities": [{"name": "Order", "attributes": ["id"], "primary_key": "id"}],
            "relationships": [],
        }
        before = (
            build_class_prompt(requirements, requirement_ids),
            build_er_prompt(requirements, class_diagram),
            build_sequence_prompt(requirements, class_diagram, er_diagram),
        )

        SkillRegistry().get("common_uml")

        after = (
            build_class_prompt(requirements, requirement_ids),
            build_er_prompt(requirements, class_diagram),
            build_sequence_prompt(requirements, class_diagram, er_diagram),
        )
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
