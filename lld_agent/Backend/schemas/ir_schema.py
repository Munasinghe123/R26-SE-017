from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Visibility(str, Enum):
	PUBLIC = "public"
	PRIVATE = "private"
	PROTECTED = "protected"
	PACKAGE = "package"


class MessageType(str, Enum):
	CALL = "call"
	RETURN = "return"


@dataclass
class MethodParameter:
	name: str
	data_type: str = ""


@dataclass
class Method:
	name: str
	parameters: list[MethodParameter] = field(default_factory=list)
	visibility: Visibility = Visibility.PUBLIC


@dataclass
class ClassRelationship:
	target: str
	rel_type: str = "association"
	cardinality: str = ""


@dataclass
class ClassIR:
	name: str
	attributes: list[str] = field(default_factory=list)
	methods: list[Method] = field(default_factory=list)
	relationships: list[ClassRelationship] = field(default_factory=list)
	stereotype: str = ""
	requirement_ids: list[str] = field(default_factory=list)


@dataclass
class SequenceMessage:
	from_participant: str
	to_participant: str
	method: str
	arguments: list[str] = field(default_factory=list)
	type: MessageType = MessageType.CALL


@dataclass
class SequenceIR:
	name: str
	description: str = ""
	participants: list[str] = field(default_factory=list)
	actors: list[str] = field(default_factory=list)
	messages: list[SequenceMessage] = field(default_factory=list)
	requirement_ids: list[str] = field(default_factory=list)


@dataclass
class EntityAttribute:
	name: str
	data_type: str = ""
	constraint: str = ""


@dataclass
class EntityRelationship:
	target: str
	rel_type: str = "one-to-many"


@dataclass
class EntityIR:
	name: str
	attributes: list[EntityAttribute] = field(default_factory=list)
	relationships: list[EntityRelationship] = field(default_factory=list)
	requirement_ids: list[str] = field(default_factory=list)


@dataclass
class IntermediateRepresentation:
	classes: list[ClassIR] = field(default_factory=list)
	sequences: list[SequenceIR] = field(default_factory=list)
	entities: list[EntityIR] = field(default_factory=list)
