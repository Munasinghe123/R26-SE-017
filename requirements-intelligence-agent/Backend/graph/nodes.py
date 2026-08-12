import json

from services.srs.build_srs import build_srs
from graph.state import GraphState
from services.tanscribe import transcribe_audio
from services.extract.extract import extract_requirements
from services.diarize import diarize_audio
from services.refine_requirements import refine_requirements
from services.meetings_service import get_latest_requirements
from services.srs.generate_srs_pdf import create_pdf
from services.read_document import read_document
from services.speech_enhancement import enhance_speech
from services.speaker_alignment import align_speakers
from services.identify_speakers import identify_speakers
from services.clean_transcript import clean_transcript
from langgraph.types import interrupt


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

def document_node(state: GraphState):
    text = read_document(
        state["document_path"]
    )

    return {
        "transcript": text
    }

def diarization_node(state: GraphState):
    speaker_segments = diarize_audio(state["audio_path"])
    print("diarizeded")
    return {"speaker_segments": speaker_segments}

def role_identification_node(state: GraphState):
    speaker_roles = identify_speakers(
        state["transcript"]
    )
    print("roles identified", speaker_roles)
    return {"speaker_roles": speaker_roles}

def transcript_cleaning_node(state: GraphState):
    print("========== RAW TRANSCRIPT ==========")
    print(state["transcript"])
    
    print("========== CLEAN TRANSCRIPT ==========")
    cleaned_transcript = clean_transcript(
        state["transcript"] , state["speaker_roles"]
    )
    print(cleaned_transcript)
    
    return {"transcript": cleaned_transcript}


def extraction_node(state: GraphState):
    requirements = extract_requirements(state["transcript"])

    print("\n========== EXTRACTION NODE RESULT ==========")
    print(json.dumps(requirements, indent=4, ensure_ascii=False))
    print("============================================")

    return {"requirements": requirements}

def refine_node(state: GraphState):
    
    print("Feedback:", state["feedback"])
    
    updated = refine_requirements(
        state["requirements"],
        state["feedback"]
    )
    print("refined")
    print(updated)
    return {
        "requirements": updated
    }
    
def build_srs_node(state):

    latest = get_latest_requirements(
        state["meeting_id"]
    )

    srs_text = build_srs(latest)
    print("srs built")

    return {
        "srs_text": srs_text
    }
    
def generate_srs_pdf_node(state: GraphState):

    pdf_path = create_pdf(
        state["srs_text"],
        state["meeting_id"]
    )

    print("srs pdf built");
    return {
        "pdf_path": pdf_path
    }
    
def await_client_node(state: GraphState):
    print("intrupt reached")
    decision = interrupt({
        "requirements": state["requirements"],
        "meeting_id": state["meeting_id"],
        "iteration_count": state["iteration_count"] or 0
    })
    print("back to resume")
    
    print("Decision:", decision)
    return {
        "approval_status": decision.get("status"),
        "feedback": decision.get("feedback"),
    }



