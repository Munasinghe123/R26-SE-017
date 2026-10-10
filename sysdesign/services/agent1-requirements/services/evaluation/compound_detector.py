import re
from typing import Dict, Any, List

# Common action verbs in software requirement statements
ACTION_VERBS = {
    "accept", "activate", "add", "alert", "allow", "analyze", "apply", "archive",
    "assign", "attach", "authenticate", "authorize", "block", "browse", "calculate",
    "cancel", "capture", "change", "check", "choose", "clear", "close", "collect",
    "compute", "configure", "confirm", "connect", "convert", "create", "deactivate",
    "delete", "deny", "deploy", "detect", "disable", "disconnect", "dispatch",
    "display", "download", "edit", "email", "enable", "encrypt", "enforce",
    "enter", "execute", "export", "extract", "fetch", "filter", "find", "format",
    "forward", "generate", "handle", "hide", "identify", "import", "initialize",
    "input", "insert", "inspect", "integrate", "isolate", "issue", "launch",
    "link", "list", "load", "locate", "lock", "log", "login", "manage",
    "modify", "monitor", "navigate", "notify", "obtain", "open", "output",
    "parse", "perform", "permit", "populate", "prevent", "print", "process",
    "prompt", "provide", "publish", "purge", "query", "receive", "record",
    "redirect", "refresh", "register", "reject", "release", "remove", "render",
    "renew", "replace", "replicate", "request", "require", "resend", "reset",
    "resolve", "respond", "restart", "restore", "restrict", "retrieve", "retry",
    "review", "route", "save", "scan", "schedule", "search", "select", "send",
    "set", "share", "show", "sign", "sort", "specify", "start", "stop", "store",
    "submit", "subscribe", "synchronize", "sync", "terminate", "toggle", "track",
    "transfer", "transform", "transmit", "trigger", "truncate", "unlock", "update",
    "upgrade", "upload", "validate", "verify", "view", "warn"
}

# Multi-word compound connectors
COMPOUND_PHRASES = [
    r"\bas\s+well\s+as\b",
    r"\bin\s+addition\s+to\b",
    r"\balong\s+with\b",
    r"\badditionally\b",
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"\band\s+also\b"
]


def detect_compound_requirement(requirement_text: str) -> Dict[str, Any]:
    """
    Python rule-based linguistic detector for possible compound / non-atomic requirements.

    Detects:
    1. Coordinating conjunctions linking multiple action verbs (e.g. 'register and reset')
    2. Semicolons separating multiple clauses
    3. Additive connector phrases ('as well as', 'in addition to', 'along with')
    4. Repeated modal verbs ('shall ... and shall ...')

    NO LLM CALLS.
    """
    text = (requirement_text or "").strip()
    if not text:
        return {
            "rule": "POSSIBLE_COMPOUND_REQUIREMENT",
            "status": "passed",
            "is_compound": False,
            "evidence": [],
            "message": "Requirement is empty."
        }

    evidence = []
    detected_actions = []

    # 1. Check for semicolon clause separators
    if ";" in text:
        evidence.append(";")
        clauses = [c.strip() for c in text.split(";") if c.strip()]
        if len(clauses) > 1:
            detected_actions.extend(clauses)

    # 2. Check for repeated modal verbs (e.g. "shall ... and shall ...")
    shall_matches = re.findall(r"\bshall\b", text, re.IGNORECASE)
    if len(shall_matches) > 1:
        evidence.append("multiple 'shall' predicates")

    # 3. Check for compound phrases (e.g. "as well as", "in addition to")
    for phrase_pat in COMPOUND_PHRASES:
        found_phrases = re.findall(phrase_pat, text, re.IGNORECASE)
        for fp in found_phrases:
            normalized_fp = re.sub(r"\s+", " ", fp).lower()
            if normalized_fp not in evidence:
                evidence.append(normalized_fp)

    # 4. Check for coordinating conjunctions linking action verbs ('and', 'or')
    # Match patterns like: [verb1] ... and [verb2] ... OR allow/enable users to [verb1] and [verb2]
    # Tokenize words cleanly
    words = re.findall(r"[a-zA-Z]+(?:-[a-zA-Z]+)?", text.lower())

    for i, word in enumerate(words):
        if word in ["and", "or"] and 0 < i < len(words) - 1:
            # Check context around the conjunction
            prev_window = words[max(0, i - 6):i]
            next_window = words[i + 1:min(len(words), i + 6)]

            # Look for action verbs preceding and following the conjunction
            prev_verbs = [w for w in prev_window if w in ACTION_VERBS]
            next_verbs = [w for w in next_window if w in ACTION_VERBS]

            # Special case: immediately following verb (e.g., "register and reset")
            if next_window and next_window[0] in ACTION_VERBS:
                if "and" not in evidence and word == "and":
                    evidence.append("and")
                elif "or" not in evidence and word == "or":
                    evidence.append("or")
                detected_actions.append(f"{prev_verbs[-1] if prev_verbs else 'action'} {word} {next_window[0]}")

            # Case: clause-level coordination (verb in prev and verb in next)
            elif prev_verbs and next_verbs:
                # Exclude compound nouns (e.g. "username and password", "email and phone")
                # If the immediate next word is a noun and no verb follows, it's a compound noun.
                first_next = next_window[0] if next_window else ""
                if first_next not in ["password", "username", "email", "address", "number", "date", "time", "id", "name", "role", "type"]:
                    if word not in evidence:
                        evidence.append(word)
                    detected_actions.append(f"{prev_verbs[-1]} ... {word} ... {next_verbs[0]}")

    is_compound = len(evidence) > 0

    if is_compound:
        return {
            "rule": "POSSIBLE_COMPOUND_REQUIREMENT",
            "status": "warning",
            "is_compound": True,
            "evidence": list(dict.fromkeys(evidence)),
            "detected_actions": list(dict.fromkeys(detected_actions)),
            "message": "The requirement may contain multiple independent capabilities."
        }

    return {
        "rule": "POSSIBLE_COMPOUND_REQUIREMENT",
        "status": "passed",
        "is_compound": False,
        "evidence": [],
        "detected_actions": [],
        "message": "No compound actions or non-atomic predicates detected."
    }
