"""
Connection manager for WebSocket meeting rooms.

Maintains a mapping of room_code → set of active WebSocket connections.
Handles broadcast, per-room messaging, and connection lifecycle.
"""

import logging
from typing import Dict, Set
from dataclasses import dataclass, field

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class Participant:
    """Represents a connected meeting participant."""
    websocket: WebSocket
    user_id: int
    username: str
    language_mode: str  # "hi_to_en" or "en_to_hi"


class ConnectionManager:
    """Manages WebSocket connections grouped by room."""

    def __init__(self):
        # room_code → set of Participant
        self._rooms: Dict[str, Set[Participant]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        room_code: str,
        user_id: int,
        username: str,
        language_mode: str = "hi_to_en",
    ) -> Participant:
        """Accept a WebSocket connection and add to a room."""
        await websocket.accept()

        participant = Participant(
            websocket=websocket,
            user_id=user_id,
            username=username,
            language_mode=language_mode,
        )

        if room_code not in self._rooms:
            self._rooms[room_code] = set()

        self._rooms[room_code].add(participant)

        logger.info(
            "WS connected: user=%s room=%s mode=%s (total=%d)",
            username,
            room_code,
            language_mode,
            len(self._rooms[room_code]),
        )

        # Notify others
        await self.broadcast_json(
            room_code,
            {
                "type": "user_joined",
                "user_id": user_id,
                "username": username,
                "language_mode": language_mode,
                "participants": self.get_participant_list(room_code),
            },
            exclude=participant,
        )

        return participant

    def disconnect(self, room_code: str, participant: Participant):
        """Remove a participant from a room."""
        if room_code in self._rooms:
            self._rooms[room_code].discard(participant)
            if not self._rooms[room_code]:
                del self._rooms[room_code]

        logger.info(
            "WS disconnected: user=%s room=%s",
            participant.username,
            room_code,
        )

    async def broadcast_json(
        self,
        room_code: str,
        data: dict,
        exclude: Participant = None,
    ):
        """Send JSON data to all participants in a room."""
        if room_code not in self._rooms:
            return

        disconnected = []
        for p in self._rooms[room_code]:
            if p is exclude:
                continue
            try:
                await p.websocket.send_json(data)
            except Exception:
                disconnected.append(p)

        for p in disconnected:
            self._rooms[room_code].discard(p)

    async def send_to_participant(self, participant: Participant, data: dict):
        """Send JSON data to a specific participant."""
        try:
            await participant.websocket.send_json(data)
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", participant.username, exc)

    def get_participant_list(self, room_code: str) -> list:
        """Return a JSON-serializable list of participants in a room."""
        if room_code not in self._rooms:
            return []

        return [
            {
                "user_id": p.user_id,
                "username": p.username,
                "language_mode": p.language_mode,
            }
            for p in self._rooms[room_code]
        ]

    def get_room_count(self) -> int:
        """Return the number of active rooms."""
        return len(self._rooms)

    def get_total_connections(self) -> int:
        """Return total active connections across all rooms."""
        return sum(len(participants) for participants in self._rooms.values())


# Singleton instance
manager = ConnectionManager()
