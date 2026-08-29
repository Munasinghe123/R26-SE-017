from pyannote.audio import Pipeline
import os


AUDIO_PATH = r"D:\sliit\Y4S1\4th Year Research\business_audio.mp3"


pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.getenv("DIARIZE_AUTH_TOKEN")
)


print("PIPELINE LOADED SUCCESSFULLY")

diarization = pipeline(AUDIO_PATH)

print("\nDIARIZATION RESULTS:\n")

for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(
        f"[{turn.start:.2f} - {turn.end:.2f}] {speaker}"
    )

print("\nDIARIZATION COMPLETED SUCCESSFULLY")