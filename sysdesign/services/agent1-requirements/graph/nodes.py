import json

from graph.state import GraphState
from langgraph.types import interrupt

from services.tanscribe import transcribe_audio
from services.extract.extract import extract_requirements
from services.diarize import diarize_audio
from services.srs.build_srs import build_srs
from services.srs.generate_srs_pdf import create_pdf
from services.read_document import read_document
from services.speech_enhancement import enhance_speech
from services.speaker_alignment import align_speakers
from services.identify_speakers import identify_speakers
from services.clean_transcript import clean_transcript
from services.extract.classify_specified_requirements import reclassify_requirements
from services.refine_requirements import refine_requirements

from services.HITL.client_view import build_client_view
from services.HITL.process_client_review import process_client_review
from services.HITL.analyze_client_changes import analyze_client_changes
from services.HITL.partition_client_changes import partition_client_changes
from services.HITL.generate_targeted_questions import generate_targeted_questions
from services.HITL.generate_requirements_from_answers import generate_requirements_from_answers
from services.HITL.collect_new_requirements import collect_new_requirements
from services.HITL.classify_new_requirements import classify_new_requirements
from services.HITL.validate_requirement_format import find_requirements_to_rewrite
from services.HITL.normalize_requirements import normalize_requirements
from services.HITL.reconcile_requirements import reconcile_requirements


# ============================================================
# Audio / document ingestion nodes
# ============================================================

def speech_enhancement_node(state: GraphState):
    enhanced_audio_path = enhance_speech(state["audio_path"])
    print("enhanced")
    return {"audio_path": enhanced_audio_path}


def transcribe_node(state: GraphState):
    transcript_segments = transcribe_audio(state["audio_path"])
    print("transcribed")
    return {"transcript_segments": transcript_segments}


def speaker_alignment_node(state: GraphState):
    transcript = align_speakers(
        state["transcript_segments"],
        state["speaker_segments"]
    )
    print("aligned")
    return {"transcript": transcript}


def diarization_node(state: GraphState):
    speaker_segments = diarize_audio(state["audio_path"])
    print("diarized")
    return {"speaker_segments": speaker_segments}


def role_identification_node(state: GraphState):
    speaker_roles = identify_speakers(state["transcript"])
    print("roles identified", speaker_roles)
    return {"speaker_roles": speaker_roles}


def transcript_cleaning_node(state: GraphState):
    print("========== RAW TRANSCRIPT ==========")
    print(state["transcript"])
    cleaned_transcript = clean_transcript(state["transcript"], state["speaker_roles"])
    print("========== CLEAN TRANSCRIPT ==========")
    print(cleaned_transcript)
    return {"transcript": cleaned_transcript}


def document_node(state: GraphState):
    text = read_document(state["document_path"])
    return {"transcript": text}


# ============================================================
# Extraction & reclassification
# ============================================================

def extraction_node(state: GraphState):
    requirements = extract_requirements(state["transcript"])
    print("\n========== EXTRACTION NODE RESULT ==========")
    print(json.dumps(requirements, indent=4, ensure_ascii=False))
    print("============================================")
    return {"requirements": requirements}


def reclassify_requirements_node(state: GraphState):
    requirements = state.get("requirements") or {}
    specified = requirements.get("specified_requirements")
    if not specified:
        return {"requirements": requirements}
    corrected_specified = reclassify_requirements(specified)
    updated_requirements = {**requirements, "specified_requirements": corrected_specified}
    print("updated requirements", updated_requirements)
    return {"requirements": updated_requirements}


# ============================================================
# Client view
# ============================================================

def client_view_node(state: GraphState):
    client_view = build_client_view(state.get("requirements") or {})
    return {"client_view": client_view}


# ============================================================
# HITL — client review interrupt
# ============================================================

def await_client_node(state: GraphState):
    print("interrupt reached — waiting for client review")

    decision = interrupt({
        "client_view": state.get("client_view"),
        "project_id": state.get("project_id"),
        "thread_id": state.get("thread_id") or state.get("meeting_id"),
    })

    print("Client review received:", decision)

    return {
        "review_status": decision.get("status"),
        "client_review": decision.get("items"),
    }


def process_client_review_node(state: GraphState):
    changes = process_client_review(
        state["client_view"],
        state["client_review"]
    )
    print("\n========== CLIENT CHANGE SET ==========")
    print(json.dumps(changes, indent=4, ensure_ascii=False))
    print("=======================================")
    return {"change_set": changes}


# ============================================================
# HITL — change analysis
# ============================================================

def analyze_client_changes_node(state: GraphState):
    analysis = analyze_client_changes(
        state["requirements"],
        state["change_set"]
    )
    print("\n========== CHANGE ANALYSIS ==========")
    print(json.dumps(analysis, indent=4, ensure_ascii=False))
    print("=====================================")
    return {"change_analysis": analysis}


def partition_client_changes_node(state: GraphState):
    result = partition_client_changes(
        state["change_set"],
        state["change_analysis"]
    )
    print("\n========== ACCEPTED CHANGES ==========")
    print(json.dumps(result["accepted_changes"], indent=4, ensure_ascii=False))
    print("\n========== CLARIFICATION CHANGES ==========")
    print(json.dumps(result["clarification_changes"], indent=4, ensure_ascii=False))
    return {
        "accepted_changes": result["accepted_changes"],
        "clarification_changes": result["clarification_changes"]
    }


# ============================================================
# HITL — targeted Q&A interrupt
# ============================================================

def generate_targeted_questions_node(state: GraphState):
    questions = generate_targeted_questions(state["clarification_changes"])
    print("\n========== TARGETED QUESTIONS ==========")
    print(json.dumps(questions, indent=4, ensure_ascii=False))
    print("========================================")
    return {"clarification_questions": questions}


def await_client_questions_node(state: GraphState):
    questions_data = state.get("clarification_questions") or {}
    questions = questions_data.get("questions", []) if isinstance(questions_data, dict) else (questions_data or [])

    if not questions:
        print("\n[HITL] No clarification questions generated — skipping interrupt.")
        return {"client_answers": []}

    print("\n========== WAITING FOR CLIENT ANSWERS ==========")
    response = interrupt({
        "thread_id": state.get("thread_id") or state.get("meeting_id"),
        "questions": state["clarification_questions"]
    })
    print("\n========== CLIENT ANSWERS RECEIVED ==========")
    print(json.dumps(response, indent=4, ensure_ascii=False))
    return {"client_answers": response.get("answers", [])}


def apply_client_answers_node(state: GraphState):
    print("\n========== CONVERTING CLIENT ANSWERS INTO REQUIREMENTS ==========")
    answer_requirements = generate_requirements_from_answers(
        state["clarification_questions"],
        state["client_answers"],
        state["clarification_changes"]
    )
    print("\n========== ANSWER-GENERATED REQUIREMENTS ==========")
    print(json.dumps(answer_requirements, indent=4, ensure_ascii=False))
    return {"answer_requirements": answer_requirements}


# ============================================================
# HITL — new requirements pipeline
# ============================================================

def collect_new_requirements_node(state: GraphState):
    print("\n========== COLLECTING NEW REQUIREMENTS ==========")
    new_requirements = collect_new_requirements(
        state.get("accepted_changes") or {},
        state.get("answer_requirements") or []
    )
    print(json.dumps(new_requirements, indent=4, ensure_ascii=False))
    return {"new_requirements": new_requirements}


def classify_new_requirements_node(state: GraphState):
    print("\n========== CLASSIFYING NEW REQUIREMENTS ==========")
    new_reqs = state.get("new_requirements") or []
    if not new_reqs:
        print("[classify_new_requirements_node] No new requirements to classify.")
        return {"classified_new_requirements": []}
    classified = classify_new_requirements(new_reqs)
    print(json.dumps(classified, indent=4, ensure_ascii=False))
    return {"classified_new_requirements": classified}


def validate_new_requirement_format_node(state: GraphState):
    print("\n========== CHECKING REQUIREMENT FORMAT ==========")
    classified = state.get("classified_new_requirements") or []
    if not classified:
        print("[validate_new_requirement_format_node] No classified requirements to validate.")
        return {"requirements_to_rewrite": []}
    requirements_to_rewrite = find_requirements_to_rewrite(classified)
    print(json.dumps(requirements_to_rewrite, indent=4, ensure_ascii=False))
    return {"requirements_to_rewrite": requirements_to_rewrite}


def normalize_new_requirements_node(state: GraphState):
    print("\n========== NORMALIZING REQUIREMENTS ==========")
    to_rewrite = state.get("requirements_to_rewrite") or []
    classified = state.get("classified_new_requirements") or []

    if not to_rewrite:
        print("[normalize_new_requirements_node] Nothing to rewrite.")
        return {"normalized_new_requirements": classified}

    rewritten = normalize_requirements(to_rewrite)

    rewritten_ids = {r["id"] for r in rewritten}
    final_requirements = []
    for req in classified:
        if req["id"] in rewritten_ids:
            final_requirements.append(
                next(r for r in rewritten if r["id"] == req["id"])
            )
        else:
            final_requirements.append(req)

    print(json.dumps(final_requirements, indent=4, ensure_ascii=False))
    return {"normalized_new_requirements": final_requirements}


# ============================================================
# Reconcile
# ============================================================

def reconcile_requirements_node(state: GraphState):
    print("\n========== RECONCILIATION NODE ==========")
    final_requirements = reconcile_requirements(
        original_requirements=state.get("requirements") or {},
        accepted_changes=state.get("accepted_changes") or {},
        answer_requirements=state.get("answer_requirements") or [],
        normalized_new_requirements=state.get("normalized_new_requirements") or []
    )

    orig = dict(state.get("requirements") or {})
    func_items = []
    nfunc_items = []

    for section in final_requirements.get("sections", []):
        stitle = section.get("title", "").lower()
        for item in section.get("items", []):
            mapped = {
                "id": item.get("id"),
                "description": item.get("text") or item.get("description", "")
            }
            if "non" in stitle or item.get("type") == "non_functional":
                nfunc_items.append(mapped)
            else:
                func_items.append(mapped)

    orig["specified_requirements"] = {
        "functional": func_items,
        "non_functional": nfunc_items
    }
    orig["functional"] = func_items
    orig["non_functional"] = nfunc_items

    # Persist reconciled requirements for PO UI
    meeting_id = state.get("meeting_id") or state.get("thread_id")
    project_id = state.get("project_id")
    if meeting_id:
        try:
            import os
            from services.meetings_service import CACHE_DIR
            cache_file = os.path.join(CACHE_DIR, f"{meeting_id}.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "id": meeting_id,
                    "requirements": orig,
                    "final_requirements": final_requirements,
                    "client_view": state.get("client_view"),
                    "version": 2,
                    "project_id": project_id
                }, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: could not write local cache: {e}")

    return {
        "final_requirements": final_requirements,
        "requirements": orig
    }


# ============================================================
# SRS (legacy / optional)
# ============================================================

def refine_node(state: GraphState):
    print("Feedback:", state.get("feedback"))
    updated = refine_requirements(state.get("requirements"), state.get("feedback"))
    print("refined", updated)
    return {"requirements": updated}


def generate_srs_pdf_node(state: GraphState):
    pdf_path = create_pdf(
        state.get("srs_text"),
        state.get("meeting_id") or state.get("thread_id")
    )
    print("srs pdf built")
    return {"pdf_path": pdf_path}
