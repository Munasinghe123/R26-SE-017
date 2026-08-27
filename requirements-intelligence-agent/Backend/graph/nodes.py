import json

from services.srs.build_srs import build_srs
from graph.state import GraphState
from services.tanscribe import transcribe_audio
from services.extract.extract import extract_requirements
from services.diarize import diarize_audio
from services.refine_requirements import refine_requirements
# from services.meetings_service import get_latest_requirements
from services.srs.generate_srs_pdf import create_pdf
from services.read_document import read_document
from services.speech_enhancement import enhance_speech
from services.speaker_alignment import align_speakers
from services.identify_speakers import identify_speakers
from services.clean_transcript import clean_transcript
from langgraph.types import interrupt
from services.HITL.client_view import build_client_view
from services.HITL.process_client_review import process_client_review
from services.HITL.analyze_client_changes import analyze_client_changes
from services.HITL.generate_targeted_questions import generate_targeted_questions
from services.HITL.partition_client_changes import (partition_client_changes)
from services.HITL.generate_requirements_from_answers import generate_requirements_from_answers


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

    # print("\n========== EXTRACTION NODE RESULT ==========")
    # print(json.dumps(requirements, indent=4, ensure_ascii=False))
    # print("============================================")

    return {"requirements": requirements}

def client_view_node(state: GraphState):

    client_view = build_client_view(
        state["requirements"]
    )

    # print("\n========== CLIENT VIEW ==========")
    # print(json.dumps(
    #     client_view,
    #     indent=4,
    #     ensure_ascii=False
    # ))
    # print("=================================")

    return {
        "client_view": client_view
    }

def await_client_node(state: GraphState):

    print("interrupt reached")

    decision = interrupt({
        "client_view": state["client_view"],
        "project_id": state["project_id"],
        "thread_id": state["thread_id"]
    })

    print("Client review received:")
    print(decision)

    return {
        "review_status": decision.get("status"),
        "client_review": decision.get("items")
    }
       
def process_client_review_node(state: GraphState):

    changes = process_client_review(
        state["client_view"],
        state["client_review"]
    )

    print("\n========== CLIENT CHANGE SET ==========")
    print(json.dumps(
        changes,
        indent=4,
        ensure_ascii=False
    ))
    print("=======================================")

    return {
        "change_set": changes
    }  
    
def analyze_client_changes_node(state: GraphState):

    analysis = analyze_client_changes(
        state["requirements"],
        state["change_set"]
    )

    print("\n========== CHANGE ANALYSIS ==========")

    print(
        json.dumps(
            analysis,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "====================================="
    )

    return {
        "change_analysis": analysis
    }

def partition_client_changes_node(
    state: GraphState
):

    result = partition_client_changes(
        state["change_set"],
        state["change_analysis"]
    )

    print(
        "\n========== ACCEPTED CHANGES =========="
    )

    print(
        json.dumps(
            result["accepted_changes"],
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\n========== CLARIFICATION CHANGES =========="
    )

    print(
        json.dumps(
            result["clarification_changes"],
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "==========================================="
    )

    return {
        "accepted_changes": result[
            "accepted_changes"
        ],
        "clarification_changes": result[
            "clarification_changes"
        ]
    }
    
def generate_targeted_questions_node(state: GraphState):

    questions = generate_targeted_questions(
        state["clarification_changes"]
    )

    print("\n========== TARGETED QUESTIONS ==========")

    print(
        json.dumps(
            questions,
            indent=4,
            ensure_ascii=False
        )
    )

    print("========================================")

    return {
        "clarification_questions": questions
    }
    
def await_client_questions_node(state: GraphState):

    print(
        "\n========== WAITING FOR CLIENT ANSWERS =========="
    )

    response = interrupt({
        "thread_id": state["thread_id"],
        "questions": state["clarification_questions"]
    })

    print(
        "\n========== CLIENT ANSWERS RECEIVED =========="
    )

    print(
        json.dumps(
            response,
            indent=4,
            ensure_ascii=False
        )
    )

    answers = response.get("answers", [])

    return {
        "client_answers": answers
    }

def apply_client_answers_node(state: GraphState):

    print(
        "\n========== CONVERTING CLIENT ANSWERS INTO REQUIREMENTS =========="
    )

    answer_requirements = generate_requirements_from_answers(
        state["clarification_questions"],
        state["client_answers"],
        state["clarification_changes"]
    )

    print(
        "\n========== ANSWER-GENERATED REQUIREMENTS =========="
    )

    print(
        json.dumps(
            answer_requirements,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "===================================================="
    )

    return {
        "answer_requirements": answer_requirements
    }


    
def generate_srs_pdf_node(state: GraphState):

    pdf_path = create_pdf(
        state["srs_text"],
        state["thread_id"]
    )

    print("srs pdf built");
    return {
        "pdf_path": pdf_path
    }
    



