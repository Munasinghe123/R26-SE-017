from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
	CRITICAL = "critical"
	HIGH = "high"
	MEDIUM = "medium"
	LOW = "low"
	INFO = "info"


@dataclass
class ValidationError:
	rule_id: str
	severity: Severity
	message: str
	suggestion: str = ""
	educational_feedback: str = ""

	def to_dict(self) -> dict:
		return {
			"rule_id": self.rule_id,
			"severity": self.severity.value,
			"message": self.message,
			"suggestion": self.suggestion,
			"educational_feedback": self.educational_feedback,
		}


@dataclass
class NamingViolation:
	location: str
	current_name: str
	expected_name: str
	convention: str
	auto_fixed: bool = False

	def to_dict(self) -> dict:
		return {
			"location": self.location,
			"current_name": self.current_name,
			"expected_name": self.expected_name,
			"convention": self.convention,
			"auto_fixed": self.auto_fixed,
		}


@dataclass
class OverDesignFlag:
	element_type: str
	element_name: str
	reason: str
	educational_feedback: str = ""

	def to_dict(self) -> dict:
		return {
			"element_type": self.element_type,
			"element_name": self.element_name,
			"reason": self.reason,
			"educational_feedback": self.educational_feedback,
		}


@dataclass
class TraceabilityEntry:
	requirement_id: str
	mapped_classes: list[str] = field(default_factory=list)
	mapped_sequences: list[str] = field(default_factory=list)
	mapped_entities: list[str] = field(default_factory=list)
	is_covered: bool = False

	def to_dict(self) -> dict:
		return {
			"requirement_id": self.requirement_id,
			"mapped_classes": list(self.mapped_classes),
			"mapped_sequences": list(self.mapped_sequences),
			"mapped_entities": list(self.mapped_entities),
			"is_covered": self.is_covered,
		}


@dataclass
class ValidationReport:
	passed: bool
	consistency_score: float
	total_checks: int
	passed_checks: int
	errors: list[ValidationError] = field(default_factory=list)
	traceability_matrix: list[TraceabilityEntry] = field(default_factory=list)
	overdesign_flags: list[OverDesignFlag] = field(default_factory=list)
	naming_violations: list[NamingViolation] = field(default_factory=list)
	naming_violations_fixed: int = 0

	def to_dict(self) -> dict:
		return {
			"passed": self.passed,
			"consistency_score": self.consistency_score,
			"total_checks": self.total_checks,
			"passed_checks": self.passed_checks,
			"errors": [err.to_dict() for err in self.errors],
			"traceability_matrix": [entry.to_dict() for entry in self.traceability_matrix],
			"overdesign_flags": [flag.to_dict() for flag in self.overdesign_flags],
			"naming_violations": [violation.to_dict() for violation in self.naming_violations],
			"naming_violations_fixed": self.naming_violations_fixed,
		}
