import whisper

model = whisper.load_model("base")


def transcribe_audio(file_path: str) -> list[dict]:
    result = model.transcribe(file_path)

    segments = []

    for segment in result["segments"]:
        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })

    print("Transcription Results:")

    for segment in segments:
        print(
            f"[{segment['start']:.2f} - {segment['end']:.2f}] {segment['text']}"
        )

    return segments