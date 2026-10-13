def align_speakers(
    transcript_segments: list[dict],
    speaker_segments: list[dict]
) -> str:
    """
    Aligns speaker turns with transcript text to create a clean, dialogue-formatted transcript.
    Supports both semantic speaker turns and timestamp-aligned segments.
    """
    # 1. If speaker_segments already contains segmented dialogue turns with text
    has_turn_text = any(s.get("text") for s in (speaker_segments or []))
    if has_turn_text:
        formatted_turns = []
        for s in speaker_segments:
            spk = s.get("speaker", "Speaker")
            txt = s.get("text", "").strip()
            if txt:
                formatted_turns.append(f"{spk}:\n{txt}")
        if formatted_turns:
            aligned = "\n\n".join(formatted_turns)
            print("\n===== FINAL TRANSCRIPT =====\n")
            print(aligned)
            print("\n============================\n")
            return aligned

    # 2. Timestamp alignment (fallback / standard flow)
    transcript = ""
    current_speaker = None

    for segment in (transcript_segments or []):
        midpoint = (segment.get("start", 0) + segment.get("end", 0)) / 2
        speaker = "UNKNOWN"

        for diarization in (speaker_segments or []):
            if diarization.get("start", 0) <= midpoint <= diarization.get("end", float("inf")):
                speaker = diarization.get("speaker", "UNKNOWN")
                break

        if speaker != current_speaker:
            if transcript:
                transcript += "\n\n"
            transcript += f"{speaker}:\n"
            current_speaker = speaker

        transcript += segment.get("text", "") + "\n"

    final_str = transcript.strip()
    if not final_str and transcript_segments:
        final_str = "\n".join([s.get("text", "") for s in transcript_segments])

    print("\n===== FINAL TRANSCRIPT =====\n")
    print(final_str)
    print("\n============================\n")
    return final_str