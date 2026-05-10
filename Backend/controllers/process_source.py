
from controllers.audio_controller import handle_audio_upload
from controllers.document_controller import handle_document_upload

audio_extensions = (".mp3", ".wav", ".m4a")

document_extensions = (".pdf", ".txt")

async def process_source(file):

    filename = file.filename.lower()

    if filename.endswith(audio_extensions):
        return await handle_audio_upload(file)

    elif filename.endswith(document_extensions):
        return await handle_document_upload(file)

    else:
        raise Exception("Unsupported file type")