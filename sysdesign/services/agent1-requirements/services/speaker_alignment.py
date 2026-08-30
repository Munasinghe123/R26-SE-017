def align_speakers(
    transcript_segments: list[dict],
    speaker_segments: list[dict]
) -> str:

    transcript = ""
    current_speaker = None

    for segment in transcript_segments:

        midpoint = (segment["start"] + segment["end"]) / 2

        speaker = "UNKNOWN"

        for diarization in speaker_segments:
            if (
                diarization["start"]
                <= midpoint
                <= diarization["end"]
            ):
                speaker = diarization["speaker"]
                break

        if speaker != current_speaker:
            if transcript:
                transcript += "\n\n"

            transcript += f"{speaker}:\n"
            current_speaker = speaker

        transcript += segment["text"] + "\n"
        
    print("\n===== FINAL TRANSCRIPT =====\n")
    print(transcript.strip())
    print("\n============================\n")

    return transcript.strip()