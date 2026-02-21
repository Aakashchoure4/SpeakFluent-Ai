"""
WebSocket route handler for real-time meeting audio processing.

Flow:
  1. Client connects with JWT token via query parameter
  2. Client sends binary audio chunks
  3. Server transcribes (Whisper) → translates → synthesizes (Edge-TTS)
  4. Server broadcasts results to all room participants
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token
from app.db.session import async_session_factory
from app.db.models import User, Room, RoomParticipant, MessageLog, RoomStatus
from app.services.transcription import transcribe_audio
from app.services.translation import translate_text, detect_language
from app.services.tts import synthesize_speech
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


async def _authenticate_ws(token: str):
    """Validate JWT token and return the user, or None."""
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        return user


async def _get_participant_mode(user_id: int, room_code: str) -> str:
    """Look up the participant's language mode from the database."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(RoomParticipant)
            .join(Room)
            .where(
                Room.room_code == room_code,
                RoomParticipant.user_id == user_id,
            )
        )
        rp = result.scalar_one_or_none()
        if rp and hasattr(rp.language_mode, "value"):
            return rp.language_mode.value
        return "hi_to_en"


async def _save_message(
    room_code: str,
    user_id: int,
    original_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    audio_url: str,
    confidence: float,
):
    """Persist a message log entry."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Room).where(Room.room_code == room_code)
        )
        room = result.scalar_one_or_none()
        if room is None:
            return

        msg = MessageLog(
            room_id=room.id,
            user_id=user_id,
            original_text=original_text,
            translated_text=translated_text,
            source_language=source_lang,
            target_language=target_lang,
            audio_url=audio_url,
            confidence=confidence,
        )
        db.add(msg)
        await db.commit()


@router.websocket("/ws/{room_code}")
async def websocket_meeting(
    websocket: WebSocket,
    room_code: str,
    token: str = Query(...),
):
    """
    Main WebSocket endpoint for a meeting room.

    Query params:
        token: JWT access token

    Binary messages: audio chunks (WebM/WAV)
    Text messages:   JSON control messages
    """
    # --- Authenticate ---
    user = await _authenticate_ws(token)
    if user is None:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # --- Validate room ---
    async with async_session_factory() as db:
        result = await db.execute(
            select(Room).where(
                Room.room_code == room_code,
                Room.status == RoomStatus.ACTIVE,
            )
        )
        room = result.scalar_one_or_none()
        if room is None:
            await websocket.close(code=4002, reason="Room not found or ended")
            return

    # --- Get language mode ---
    language_mode = await _get_participant_mode(user.id, room_code)

    # --- Connect ---
    participant = await manager.connect(
        websocket=websocket,
        room_code=room_code,
        user_id=user.id,
        username=user.username,
        language_mode=language_mode,
    )

    # Send initial state to the connecting client
    await manager.send_to_participant(
        participant,
        {
            "type": "connection_established",
            "user_id": user.id,
            "username": user.username,
            "room_code": room_code,
            "language_mode": language_mode,
            "participants": manager.get_participant_list(room_code),
        },
    )

    try:
        while True:
            # Wait for audio or text messages
            message = await websocket.receive()

            if "bytes" in message:
                # --- Binary audio chunk ---
                audio_bytes = message["bytes"]
                if len(audio_bytes) < 100:
                    continue  # Skip tiny/empty frames

                # 1. Transcribe
                transcription = await transcribe_audio(audio_bytes)
                original_text = transcription["text"]
                detected_lang = transcription["language"]
                confidence = transcription["confidence"]

                if not original_text.strip():
                    continue  # Skip empty transcriptions

                # 2. Determine target language from participant mode
                if language_mode == "hi_to_en":
                    source_lang = "hi"
                    target_lang = "en"
                else:
                    source_lang = "en"
                    target_lang = "hi"

                # Override source with detected if confident
                if confidence > 0.5:
                    source_lang = detected_lang

                # 3. Translate
                translated_text, src, tgt = await translate_text(
                    original_text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                )

                # 4. Text-to-Speech
                audio_url = await synthesize_speech(translated_text, tgt)

                # 5. Broadcast results to all participants
                result_data = {
                    "type": "translation_result",
                    "user_id": user.id,
                    "username": user.username,
                    "original_text": original_text,
                    "translated_text": translated_text,
                    "source_language": src,
                    "target_language": tgt,
                    "audio_url": audio_url,
                    "confidence": confidence,
                }

                await manager.broadcast_json(room_code, result_data)

                # Also send to the speaker themselves
                await manager.send_to_participant(participant, result_data)

                # 6. Save to database asynchronously
                await _save_message(
                    room_code=room_code,
                    user_id=user.id,
                    original_text=original_text,
                    translated_text=translated_text,
                    source_lang=src,
                    target_lang=tgt,
                    audio_url=audio_url,
                    confidence=confidence,
                )

            elif "text" in message:
                # --- JSON control message ---
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type", "")

                if msg_type == "change_mode":
                    new_mode = data.get("mode", language_mode)
                    if new_mode in ("hi_to_en", "en_to_hi"):
                        participant.language_mode = new_mode
                        language_mode = new_mode
                        await manager.send_to_participant(
                            participant,
                            {
                                "type": "mode_changed",
                                "mode": new_mode,
                            },
                        )

                elif msg_type == "ping":
                    await manager.send_to_participant(
                        participant,
                        {"type": "pong"},
                    )

    except WebSocketDisconnect:
        logger.info("WS disconnected: user=%s room=%s", user.username, room_code)
    except Exception as exc:
        logger.exception("WS error for user=%s room=%s: %s", user.username, room_code, exc)
    finally:
        manager.disconnect(room_code, participant)

        # Notify others that user left
        await manager.broadcast_json(
            room_code,
            {
                "type": "user_left",
                "user_id": user.id,
                "username": user.username,
                "participants": manager.get_participant_list(room_code),
            },
        )
