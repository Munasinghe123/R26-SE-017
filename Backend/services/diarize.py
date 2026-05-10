from pyannote.audio import Pipeline
import os

pipeline = Pipeline.from_pretrained(
    
    "pyannote/speaker-diarization-3.1",
    use_auth_token="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" 
)

def diarize_audio(path):
    diarization = pipeline(path)

    results = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        results.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })

    return results