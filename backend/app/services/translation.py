"""
Translation service using deep-translator (Google Translate backend).

Supports Hindi ↔ English translation with language auto-detection fallback.
"""

import logging
from typing import Tuple

from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Pre-initialised translators
_hi_to_en = GoogleTranslator(source="hi", target="en")
_en_to_hi = GoogleTranslator(source="en", target="hi")


def detect_language(text: str) -> str:
    """
    Detect language of text.
    Returns 'hi' for Hindi, 'en' for English (default).
    """
    try:
        lang = detect(text)
        if lang in ("hi", "mr", "ne", "sa"):  # Devanagari-family fallback
            return "hi"
        return "en"
    except LangDetectException:
        return "en"


async def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
) -> Tuple[str, str, str]:
    """
    Translate text between Hindi and English.

    Args:
        text:        The text to translate.
        source_lang: The source language ("hi", "en", or "auto").
        target_lang: The target language ("hi" or "en").

    Returns:
        (translated_text, resolved_source_lang, resolved_target_lang)
    """
    if not text or not text.strip():
        return "", source_lang, target_lang

    # Auto-detect source language if needed
    if source_lang == "auto":
        source_lang = detect_language(text)

    # Determine target if both are the same
    if source_lang == target_lang:
        target_lang = "en" if source_lang == "hi" else "hi"

    try:
        if source_lang == "hi" and target_lang == "en":
            translated = _hi_to_en.translate(text)
        elif source_lang == "en" and target_lang == "hi":
            translated = _en_to_hi.translate(text)
        else:
            # Fallback — create a dynamic translator
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(text)

        if translated is None:
            translated = text

        logger.info(
            "Translation %s→%s  |  '%s' → '%s'",
            source_lang,
            target_lang,
            text[:60],
            translated[:60],
        )
        return translated, source_lang, target_lang

    except Exception as exc:
        logger.exception("Translation error: %s", exc)
        return text, source_lang, target_lang
