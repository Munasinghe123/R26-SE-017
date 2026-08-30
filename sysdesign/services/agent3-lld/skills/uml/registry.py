from __future__ import annotations

from collections.abc import Iterable

from skills.uml.class_diagram import CLASS_GENERATION_SKILL
from skills.uml.common import COMMON_UML_SKILL
from skills.uml.er_diagram import ER_GENERATION_SKILL
from skills.uml.sequence_diagram import SEQUENCE_GENERATION_SKILL
from skills.uml.skill import Skill


class SkillRegistry:
    def __init__(self, skills: Iterable[Skill] | None = None) -> None:
        skill_list = list(skills or _DEFAULT_SKILLS)
        self._skills = {skill.name: skill for skill in skill_list}
        if len(self._skills) != len(skill_list):
            raise ValueError("UML skill names must be unique.")

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            available = ", ".join(sorted(self._skills))
            raise KeyError(f"Unknown UML skill '{name}'. Available skills: {available}") from exc

    def all(self) -> tuple[Skill, ...]:
        return tuple(self._skills.values())


_DEFAULT_SKILLS = (
    COMMON_UML_SKILL,
    CLASS_GENERATION_SKILL,
    ER_GENERATION_SKILL,
    SEQUENCE_GENERATION_SKILL,
)
