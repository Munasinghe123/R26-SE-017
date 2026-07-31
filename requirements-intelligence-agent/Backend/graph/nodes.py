from services.generate_srs import generate_srs
from graph.state import GraphState
from services.tanscribe import transcribe_audio
from services.extract import extract_requirements
from services.diarize import diarize_audio
from services.refine_requirements import refine_requirements
from services.meetings_service import get_latest_requirements
from services.generate_srs_pdf import create_pdf
from services.read_document import read_document
from langgraph.types import interrupt


def transcribe_node(state: GraphState):
    transcript = transcribe_audio(state["audio_path"])
    print("transcribed")
    return {"transcript": transcript}

def document_node(state: GraphState):
    text = read_document(
        state["document_path"]
    )

    return {
        "transcript": text
    }


def diarization_node(state: GraphState):
    diarization = diarize_audio(state["audio_path"])
    print("diarizeded")
    return {"diarization": diarization}


def extraction_node(state: GraphState):
    requirements = extract_requirements(state["transcript"])
    print("extracteded")
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
    
def generate_srs_node(state):

    latest = get_latest_requirements(
        state["meeting_id"]
    )

    srs_text = generate_srs(latest)
    print("srs generated")

    return {
        "srs_text": srs_text
    }
    
def generate_srs_pdf_node(state: GraphState):

    pdf_path = create_pdf(
        state["srs_text"],
        state["meeting_id"]
    )

    print("srs pdf");
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

