import os
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from services.live_kit import create_participant_token
from services.llm import llm
from services.meetings_service import save_meeting_requirements

try:
    import json_repair
except ImportError:
    json_repair = None

live_kit_routes = APIRouter()


class DetectRequirementRequest(BaseModel):
    text: str
    speaker: str = "Client"
    role: str = "client"
    project_id: Optional[str] = None
    room_name: Optional[str] = None


class LiveMeetingSaveRequest(BaseModel):
    meeting_id: str
    project_id: Optional[str] = None
    requirements: List[Dict[str, Any]]
    transcript_items: Optional[List[Dict[str, Any]]] = None


@live_kit_routes.get("/test/livekit-token")
async def test_livekit_token(
    room: str = Query("test-room", description="Meeting room identifier"),
    username: str = Query("Test User", description="Display name of participant"),
    role: str = Query("ba", description="Participant role: 'ba' or 'client'"),
    project_id: Optional[str] = Query(None, description="Optional project ID"),
):
    """
    Issues a secure LiveKit WebRTC access token for a meeting participant.
    Supports dual-persona role separation (Business Analyst vs. Client).
    """
    server_url = os.getenv("LIVEKIT_URL")
    if not server_url:
        raise HTTPException(status_code=500, detail="LIVEKIT_URL environment variable is not configured.")

    sanitized_role = "ba" if role.lower() in ["ba", "business analyst", "analyst"] else "client"
    unique_suffix = uuid.uuid4().hex[:6]
    identity = f"{sanitized_role}_{unique_suffix}"

    token = create_participant_token(
        identity=identity,
        name=username,
        room_name=room,
        metadata={"role": sanitized_role, "project_id": project_id, "username": username},
    )

    return {
        "token": token,
        "room_name": room,
        "server_url": server_url,
        "identity": identity,
        "role": sanitized_role,
        "username": username,
    }


@live_kit_routes.post("/live-meeting/detect-requirement")
async def detect_requirement(payload: DetectRequirementRequest):
    """
    Fast, real-time AI Elicitation filter:
    Analyzes a single live spoken utterance. Filters out casual chit-chat,
    and returns a structured requirement card if a system capability or constraint is stated.
    """
    raw_text = (payload.text or "").strip()
    words = raw_text.split()

    # Fast heuristic reject for greetings and very short filler phrases
    if len(words) < 3:
        return {"is_requirement": False, "reason": "too_short"}

    filler_phrases = ["hello", "good morning", "can you hear me", "yes i can", "thanks for joining", "bye bye", "okay yeah", "sounds good"]
    if raw_text.lower() in filler_phrases:
        return {"is_requirement": False, "reason": "chitchat"}

    prompt = f"""
You are an expert real-time Requirements Engineering AI assistant listening to a live software elicitation meeting.
Analyze this single spoken sentence from the client/analyst:
"{raw_text}"

Evaluate whether this sentence states a concrete software requirement, business rule, system behavior, role capability, or quality constraint.

Criteria:
1. Casual conversation, greetings, confirmation words, or general small talk -> is_requirement: false
2. Simple questions asking for clarification without specifying features -> is_requirement: false
3. Descriptions of a desired feature, data behavior, user workflow, admin action, or business rule -> is_requirement: true, category: "FR"
4. Constraints regarding security, access roles, performance, latency, compliance, or UI rules -> is_requirement: true, category: "NFR"

Return ONLY a valid JSON object matching this schema:
{{
  "is_requirement": true,
  "category": "FR" or "NFR",
  "type": "Functional" or "Non-Functional",
  "sub_type": "Security" | "Performance" | "Data Sync" | "User Workflow" | "Reporting" | "General",
  "title": "Concise 3-6 word title (e.g. Real-Time Stock Synchronization)",
  "description": "Standard requirement specification starting with 'The system shall...'",
  "confidence": 0.95
}}

If is_requirement is false:
{{
  "is_requirement": false
}}
""".strip()

    try:
        response = llm.invoke(prompt)
        content = (response.content or "").strip()
        content = content.replace("```json", "").replace("```", "").strip()

        if json_repair:
            data = json_repair.loads(content)
        else:
            data = json.loads(content)

        if isinstance(data, dict) and data.get("is_requirement") is True:
            category = data.get("category", "FR")
            prefix = "FR" if category == "FR" else "NFR"
            card_id = f"{prefix}-LIVE-{uuid.uuid4().hex[:4].upper()}"

            return {
                "is_requirement": True,
                "id": card_id,
                "category": category,
                "type": data.get("type", "Functional" if category == "FR" else "Non-Functional"),
                "sub_type": data.get("sub_type", "General"),
                "title": data.get("title", "Detected Requirement"),
                "description": data.get("description", raw_text),
                "source_text": raw_text,
                "speaker": payload.speaker,
                "role": payload.role,
                "confidence": float(data.get("confidence", 0.9)),
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            }
    except Exception as exc:
        print(f"[Live Meeting Detection Warning] {exc}")

    return {"is_requirement": False}


@live_kit_routes.post("/live-meeting/save-requirements")
async def save_live_requirements(payload: LiveMeetingSaveRequest):
    """
    Persists real-time captured requirements from the live meeting into
    the meeting cache and Neon database, seamlessly linking into the
    Requirements Review and SRS Assembly pipeline.
    """
    meeting_id = payload.meeting_id or str(uuid.uuid4())
    reqs_list = payload.requirements or []

    # Separate into functional and non-functional buckets
    functional = []
    non_functional = []
    client_view_items = []

    for idx, r in enumerate(reqs_list):
        category = r.get("category", "FR")
        req_id = r.get("id") or f"REQ-{idx+1:03d}"
        title = r.get("title") or f"Requirement {idx+1}"
        desc = r.get("description") or r.get("source_text") or ""
        sub_type = r.get("sub_type") or "General"

        item = {
            "id": req_id,
            "title": title,
            "description": desc,
            "type": sub_type,
            "category": category,
            "source": r.get("source_text") or "",
            "speaker": r.get("speaker") or "Client",
            "status": "approved",
        }

        if category == "NFR":
            non_functional.append(item)
        else:
            functional.append(item)

        # Build client-friendly statement
        client_view_items.append({
            "id": req_id,
            "client_statement": desc.replace("The system shall ", "The system will "),
            "original_title": title,
            "category": category,
        })

    canonical_requirements = {
        "functional": functional,
        "non_functional": non_functional,
        "all": functional + non_functional,
        "meeting_id": meeting_id,
        "project_id": payload.project_id,
        "total_count": len(reqs_list),
        "input_method": "meeting",
    }

    client_view = {
        "items": client_view_items,
        "meeting_id": meeting_id,
        "total_items": len(client_view_items),
        "input_method": "meeting",
    }

    try:
        await save_meeting_requirements(
            meeting_id=meeting_id,
            requirements=canonical_requirements,
            client_view=client_view,
            version=1,
            project_id=payload.project_id,
            status="completed",  # For meeting input: already discussed with client, ready for BA pipeline
        )
    except Exception as e:
        print(f"[Warning] Failed to persist meeting requirements: {e}")

    return {
        "ok": True,
        "meeting_id": meeting_id,
        "project_id": payload.project_id,
        "saved_count": len(reqs_list),
        "review_url": f"/requirements-review/{meeting_id}",
    }