"""
Whisper-based speech-to-text transcription service.

Uses OpenAI Whisper locally. Audio bytes are saved to a temp file,
transcribed, and then the temp file is removed.
"""

import os
import tempfile
import logging
from typing import Optional

import whisper
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global model reference — loaded once per process
_model = None


def _get_model():
    """Lazy-load the Whisper model."""
    global _model
    if _model is None:
        logger.info("Loading Whisper model: %s …", settings.WHISPER_MODEL)
        _model = whisper.load_model(settings.WHISPER_MODEL)
        logger.info("Whisper model loaded successfully.")
    return _model


async def transcribe_audio(audio_bytes: bytes) -> dict:
    """
    Transcribe raw audio bytes (WebM / WAV / MP3).

    Returns:
        {
            "text": str,
            "language": str,   # detected language code ("hi", "en", etc.)
            "confidence": float
        }
    """
    tmp_path: Optional[str] = None
    try:
        # Write audio bytes to a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".webm", delete=False, dir=tempfile.gettempdir()
        ) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = _get_model()

        # Transcribe — Whisper handles format detection internally
        result = model.transcribe(
            tmp_path,
            fp16=False,  # Safe for CPU; GPU users can enable
            language=None,  # Auto-detect
            task="transcribe",
        )

        text = (result.get("text") or "").strip()
        detected_lang = result.get("language", "en")

        # Whisper doesn't give a single confidence score; approximate from
        # the average log-probability of the first segment.
        segments = result.get("segments", [])
        if segments:
            avg_logprob = float(
                np.mean([s.get("avg_logprob", -1.0) for s in segments])
            )
            # Convert log-prob to a 0-1 confidence heuristic
            confidence = round(max(0.0, min(1.0, 1.0 + avg_logprob)), 3)
        else:
            confidence = 0.0

        logger.info(
            "Transcription complete — lang=%s, conf=%.3f, text_len=%d",
            detected_lang,
            confidence,
            len(text),
        )

        return {
            "text": text,
            "language": detected_lang,
            "confidence": confidence,
        }

    except Exception as exc:
        logger.exception("Transcription failed: %s", exc)
        return {"text": "", "language": "en", "confidence": 0.0}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
