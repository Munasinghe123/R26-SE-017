import os

pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        try:
            from pyannote.audio import Pipeline
            auth_token = os.getenv("DIARIZE_AUTH_TOKEN")
            if auth_token:
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=auth_token
                )
        except Exception as e:
            print(f"[WARNING] Pyannote diarization unavailable: {e}")
            pipeline = None
    return pipeline

def diarize_audio(path):
    p = get_pipeline()
    if not p:
        print("[INFO] Diarization bypassed (pyannote pipeline not initialized).")
        return [{"start": 0.0, "end": 100.0, "speaker": "SPEAKER_00"}]

    diarization = p(path)

    results = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        results.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })
    
    print("Diarization Results:", results)
    
    for result in results:
        print(
            f"[{result['start']:.2f} - {result['end']:.2f}] {result['speaker']}"
        )

    return results