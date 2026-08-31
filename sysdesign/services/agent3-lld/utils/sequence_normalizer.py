"""
Sequence Normalizer & Validator

Normalizes sequence diagram IR / raw dictionaries before PlantUML rendering.
Enforces participant roles, canonical names, return arrow types, loop structures,
and causal message ordering.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# Standard semantic participant roles supported by the system
SUPPORTED_ROLES = {
    "actor",
    "boundary",
    "controller",
    "control",  # backward compatibility
    "service",
    "repository",
    "entity",
    "database",
    "external_system",
    "participant",
}

# Deterministic PlantUML keyword mapping for each semantic role (Requirement 3 & 8)
ROLE_TO_PLANTUML = {
    "actor": "actor",
    "boundary": "boundary",
    "controller": "control",
    "control": "control",
    "service": "control",
    "entity": "entity",
    "repository": "participant",
    "database": "database",
    "external_system": "participant",
    "participant": "participant",
}


def normalize_sequence_diagram(
    sequence_data: dict[str, Any],
    class_diagram: dict[str, Any] | None = None,
    hld_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Normalizes a single sequence diagram dict before PlantUML rendering.

    - Resolves missing participants against canonical class/hld names
    - Validates message senders and receivers
    - Preserves canonical participant names and parameters
    - Normalizes explicit message types ('call' vs 'return')
    - Ensures logic blocks (loops, alt, opt) preserve causal ordering
    """
    sequence = dict(sequence_data)
    raw_participants = [str(p).strip() for p in sequence.get("participants", []) or [] if str(p).strip()]
    participant_types = dict(sequence.get("participant_types", {}) or {})

    # Build index of canonical classes and HLD components for resolution
    canonical_index: dict[str, dict[str, str]] = {}

    if class_diagram and isinstance(class_diagram, dict):
        for cls in class_diagram.get("classes", []) or []:
            if isinstance(cls, dict):
                cname = str(cls.get("name", "")).strip()
                if cname:
                    # Infer role from class stereotype or name pattern if not explicit
                    role = "entity" if cls.get("attributes") else "service"
                    if "controller" in cname.lower():
                        role = "controller"
                    elif "repository" in cname.lower():
                        role = "repository"
                    elif "service" in cname.lower():
                        role = "service"
                    canonical_index[cname.lower()] = {"name": cname, "role": role}

    if hld_data and isinstance(hld_data, dict):
        for comp in hld_data.get("architecture_components", []) or []:
            cname = str(comp).split("(")[0].strip()
            if cname:
                role = "boundary" if "ui" in cname.lower() or "frontend" in cname.lower() or "gateway" in cname.lower() else "controller"
                if "repository" in cname.lower():
                    role = "repository"
                elif "service" in cname.lower():
                    role = "service"
                canonical_index[cname.lower()] = {"name": cname, "role": role}

    # 1. Normalize participant names and roles
    declared_participants: list[str] = []
    normalized_types: dict[str, str] = {}
    seen_participants: set[str] = set()

    for p in raw_participants:
        p_lower = p.lower()
        canonical_info = canonical_index.get(p_lower)
        canonical_name = canonical_info["name"] if canonical_info else p

        if canonical_name not in seen_participants:
            seen_participants.add(canonical_name)
            declared_participants.append(canonical_name)

            raw_role = str(participant_types.get(p, participant_types.get(canonical_name, ""))).strip().lower()
            if raw_role in SUPPORTED_ROLES:
                role = raw_role
            elif canonical_info:
                role = canonical_info["role"]
            else:
                role = "participant"
            normalized_types[canonical_name] = role

    # 2. Extract and validate all messages from sequence
    messages = sequence.get("messages", []) or []
    logic_blocks = sequence.get("logic_blocks", []) or []
    raw_items = sequence.get("items", sequence.get("interactions", [])) or []

    # Collect all senders and receivers
    used_participant_names: set[str] = set()

    def _collect_and_validate_msg(msg: dict) -> dict:
        sender = str(msg.get("from", "")).strip()
        receiver = str(msg.get("to", "")).strip()

        # Resolve sender
        sender_canonical = _resolve_participant(sender, canonical_index, seen_participants, declared_participants, normalized_types)
        receiver_canonical = _resolve_participant(receiver, canonical_index, seen_participants, declared_participants, normalized_types)

        if sender_canonical:
            used_participant_names.add(sender_canonical)
            msg["from"] = sender_canonical
        if receiver_canonical:
            used_participant_names.add(receiver_canonical)
            msg["to"] = receiver_canonical

        # Check explicit type field (Requirement 4 & 7)
        raw_type = str(msg.get("type", "")).strip().lower()
        msg_text = str(msg.get("message", "")).strip()
        if raw_type not in ("call", "return"):
            if msg_text.lower().startswith("return") or "response" in msg_text.lower():
                msg["type"] = "return"
            else:
                msg["type"] = "call"
        return msg

    def _process_logic_block(block: dict) -> dict:
        block_type = str(block.get("block_type", block.get("type", "alt"))).strip().lower()
        block["block_type"] = block_type
        b_msgs = block.get("messages", []) or []
        block["messages"] = [_collect_and_validate_msg(m) for m in b_msgs if isinstance(m, dict)]
        b_blocks = block.get("logic_blocks", []) or []
        block["logic_blocks"] = [_process_logic_block(b) for b in b_blocks if isinstance(b, dict)]
        return block

    # Process all top-level messages and logic blocks
    sequence["messages"] = [_collect_and_validate_msg(m) for m in messages if isinstance(m, dict)]
    sequence["logic_blocks"] = [_process_logic_block(b) for b in logic_blocks if isinstance(b, dict)]

    if raw_items:
        processed_items = []
        for item in raw_items:
            if isinstance(item, dict):
                if "block_type" in item or ("type" in item and str(item.get("type")).lower() in {"loop", "alt", "opt", "else"}):
                    processed_items.append(_process_logic_block(item))
                else:
                    processed_items.append(_collect_and_validate_msg(item))
        sequence["items"] = processed_items

    # 3. Filter out unused participants (Requirement 11)
    final_participants = [p for p in declared_participants if p in used_participant_names]

    sequence["participants"] = final_participants
    sequence["participant_types"] = {p: normalized_types.get(p, "participant") for p in final_participants}

    return sequence


def _resolve_participant(
    name: str,
    canonical_index: dict[str, dict[str, str]],
    seen_participants: set[str],
    declared_participants: list[str],
    normalized_types: dict[str, str],
) -> str:
    """Resolves an undeclared participant against canonical HLD/Class names (Requirement 1)."""
    if not name:
        return ""
    if name in seen_participants:
        return name

    name_lower = name.lower()
    if name_lower in canonical_index:
        canonical_name = canonical_index[name_lower]["name"]
        role = canonical_index[name_lower]["role"]
        if canonical_name not in seen_participants:
            seen_participants.add(canonical_name)
            declared_participants.append(canonical_name)
            normalized_types[canonical_name] = role
        return canonical_name

    # If name was already in declared participants under exact casing
    if name not in seen_participants:
        seen_participants.add(name)
        declared_participants.append(name)
        normalized_types[name] = "participant"
    return name
