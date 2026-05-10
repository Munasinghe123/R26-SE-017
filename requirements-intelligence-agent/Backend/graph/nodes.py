from services.generate_srs import generate_srs
from graph.state import GraphState
from services.tanscribe import transcribe_audio
from services.extract import extract_requirements
from services.diarize import diarize_audio
from services.refine_requirements import refine_requirements
from services.meetings_service import get_latest_requirements
from services.generate_srs_pdf import create_pdf
from services.read_document import read_document


def transcribe_node(state: GraphState):
    transcript = transcribe_audio(state["audio_path"])
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
    return {"diarization": diarization}


def extraction_node(state: GraphState):
    requirements = extract_requirements(state["transcript"])
    return {"requirements": requirements}


def refine_node(state: GraphState):
    updated = refine_requirements(
        state["requirements"],
        state["feedback"]
    )

    return {
        "requirements": updated
    }
    
def generate_srs_node(state):

    latest = get_latest_requirements(
        state["meeting_id"]
    )

    srs_text = generate_srs(latest)

    return {
        "srs_text": srs_text
    }
    
def generate_srs_pdf_node(state: GraphState):

    pdf_path = create_pdf(
        state["srs_text"],
        state["meeting_id"]
    )

    return {
        "pdf_path": pdf_path
    }
    
