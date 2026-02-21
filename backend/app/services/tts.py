"""
Edge-TTS voice synthesis service.

Generates an MP3 file from translated text using Microsoft Edge TTS voices.
Returns the file path relative to the static directory so it can be served
via FastAPI's StaticFiles mount.
"""

import os
import uuid
import logging

import edge_tts

from app.core.config import settings

logger = logging.getLogger(__name__)

# Voice mapping per language
VOICES = {
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
}


async def synthesize_speech(text: str, language: str = "en") -> str:
    """
    Convert text to speech and save as an MP3 file.

    Args:
        text:     The text to speak.
        language: Target language code ("en" or "hi").

    Returns:
        Relative URL path to the generated audio file, e.g.
        "/static/audio/abc123.mp3"
    """
    if not text or not text.strip():
        return ""

    voice = VOICES.get(language, VOICES["en"])
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(settings.AUDIO_DIR, filename)

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)

        relative_url = f"/static/audio/{filename}"
        logger.info("TTS generated: %s (%s, %s)", relative_url, language, voice)
        return relative_url

    except Exception as exc:
        logger.exception("TTS synthesis failed: %s", exc)
        return ""
