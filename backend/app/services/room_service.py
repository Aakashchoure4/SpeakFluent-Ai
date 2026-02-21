"""
Room management service.

Handles room creation, joining, lookup, and participant management.
"""

import logging
import secrets
import string
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Room, RoomParticipant, RoomStatus, LanguageMode, User

logger = logging.getLogger(__name__)


def _generate_room_code(length: int = 8) -> str:
    """Generate a unique room code like 'MX7K-A2QP'."""
    chars = string.ascii_uppercase + string.digits
    part1 = "".join(secrets.choice(chars) for _ in range(length // 2))
    part2 = "".join(secrets.choice(chars) for _ in range(length // 2))
    return f"{part1}-{part2}"


async def create_room(
    db: AsyncSession,
    owner: User,
    name: str,
    max_participants: int = 10,
) -> Room:
    """Create a new meeting room."""
    room_code = _generate_room_code()

    room = Room(
        room_code=room_code,
        name=name,
        owner_id=owner.id,
        status=RoomStatus.ACTIVE,
        max_participants=max_participants,
    )
    db.add(room)
    await db.flush()

    # Owner auto-joins the room
    participant = RoomParticipant(
        room_id=room.id,
        user_id=owner.id,
        language_mode=LanguageMode.HINDI_TO_ENGLISH,
        is_active=True,
    )
    db.add(participant)
    await db.flush()

    logger.info("Room created: %s by user %d", room_code, owner.id)
    return room


async def join_room(
    db: AsyncSession,
    user: User,
    room_code: str,
    language_mode: str = "hi_to_en",
) -> Optional[Room]:
    """Join an existing room by code."""
    result = await db.execute(
        select(Room)
        .options(selectinload(Room.participants))
        .where(Room.room_code == room_code, Room.status == RoomStatus.ACTIVE)
    )
    room = result.scalar_one_or_none()
    if room is None:
        return None

    # Check if user is already a participant
    existing = await db.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room.id,
            RoomParticipant.user_id == user.id,
        )
    )
    participant = existing.scalar_one_or_none()

    if participant:
        participant.is_active = True
        participant.language_mode = LanguageMode(language_mode)
    else:
        # Check max participants
        count_result = await db.execute(
            select(func.count(RoomParticipant.id)).where(
                RoomParticipant.room_id == room.id,
                RoomParticipant.is_active == True,  # noqa: E712
            )
        )
        active_count = count_result.scalar() or 0
        if active_count >= room.max_participants:
            return None  # Room is full

        participant = RoomParticipant(
            room_id=room.id,
            user_id=user.id,
            language_mode=LanguageMode(language_mode),
            is_active=True,
        )
        db.add(participant)

    await db.flush()
    logger.info("User %d joined room %s", user.id, room_code)
    return room


async def get_room_by_code(
    db: AsyncSession, room_code: str
) -> Optional[Room]:
    """Get a room by its code."""
    result = await db.execute(
        select(Room)
        .options(selectinload(Room.participants).selectinload(RoomParticipant.user))
        .where(Room.room_code == room_code)
    )
    return result.scalar_one_or_none()


async def get_user_rooms(db: AsyncSession, user_id: int) -> List[Room]:
    """Get all rooms a user participates in."""
    result = await db.execute(
        select(Room)
        .join(RoomParticipant)
        .where(RoomParticipant.user_id == user_id)
        .order_by(Room.created_at.desc())
    )
    return list(result.scalars().all())


async def leave_room(db: AsyncSession, user_id: int, room_code: str) -> bool:
    """Mark a participant as inactive in a room."""
    room = await get_room_by_code(db, room_code)
    if room is None:
        return False

    result = await db.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room.id,
            RoomParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()
    if participant:
        participant.is_active = False
        await db.flush()
        return True
    return False


async def end_room(db: AsyncSession, room: Room) -> Room:
    """End a meeting room."""
    from datetime import datetime, timezone

    room.status = RoomStatus.ENDED
    room.ended_at = datetime.now(timezone.utc)
    await db.flush()
    return room
