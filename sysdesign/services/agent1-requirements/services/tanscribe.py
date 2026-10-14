"""
Legacy alias for services/transcribe.py to maintain backward compatibility.
"""
from services.transcribe import transcribe_audio, get_local_whisper_model as get_whisper_model

__all__ = ["transcribe_audio", "get_whisper_model"]