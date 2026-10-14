import os
import json
from typing import List, Dict, Any
from services.llm import get_llm, llm


def diarize_audio(path: str, transcript_segments: list[dict] = None) -> list[dict]:
    """
    Lightweight, cloud-hostable Semantic Dialogue Diarization.
    Replaces heavy local Pyannote neural networks with fast LLM semantic speaker turn segmentation.
    Eliminates all PyTorch/Torchaudio version conflicts, memory bloat, and cloud server crashes.
    """
    print("[Agent 1 Diarization] Performing semantic dialogue diarization...")

    # If transcript segments are not provided directly, return a baseline turn
    if not transcript_segments:
        return [
            {"start": 0.0, "end": 100.0, "speaker": "SPEAKER_00"}
        ]

    # Combine segments into text for semantic turn detection
    raw_text = "\n".join([s.get("text", "") for s in transcript_segments if s.get("text")]).strip()
    if not raw_text:
        return [{"start": 0.0, "end": 100.0, "speaker": "SPEAKER_00"}]

    prompt = f"""
You are an expert NLP conversation diarization model.
Analyze the following raw transcription of a software requirements elicitation meeting.
The participants are:
1. The Business Analyst (asks questions, clarifies requirements, guides discussion)
2. The Client (describes business needs, features, constraints, answers questions)

Segment the raw text into distinct conversational turns. For each turn, indicate who is speaking.

Return ONLY a valid JSON list of objects matching this exact structure:
[
  {{
    "speaker": "Business Analyst",
    "text": "spoken statement or question"
  }},
  {{
    "speaker": "Client",
    "text": "spoken response or requirement"
  }}
]

Raw Transcript:
{raw_text}
""".strip()

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        turns = json.loads(content)

        if isinstance(turns, list) and turns:
            results = []
            for idx, turn in enumerate(turns):
                results.append({
                    "start": float(idx * 5.0),
                    "end": float((idx + 1) * 5.0),
                    "speaker": turn.get("speaker", "Business Analyst" if idx % 2 == 0 else "Client"),
                    "text": turn.get("text", ""),
                })
            print(f"[Agent 1 Diarization] Successfully identified {len(results)} conversational speaker turns.")
            return results
    except Exception as exc:
        print(f"[Agent 1 Diarization Warning] LLM turn segmentation notice: {exc}")

    # Fallback to single speaker turn if parsing fails
    return [{"start": 0.0, "end": 100.0, "speaker": "SPEAKER_00"}]