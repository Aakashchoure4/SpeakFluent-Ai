"""
Meeting room API routes — create, list, join, detail, leave, end.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, RoomStatus
from app.schemas.room import (
    RoomCreate,
    RoomJoin,
    RoomResponse,
    RoomDetailResponse,
    ParticipantInfo,
)
from app.core.dependencies import get_current_user
from app.services.room_service import (
    create_room,
    join_room,
    get_room_by_code,
    get_user_rooms,
    leave_room,
    end_room,
)

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


# --------------------------------------------------------------------------
# Create Room
# --------------------------------------------------------------------------
@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_new_room(
    payload: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new meeting room."""
    room = await create_room(
        db=db,
        owner=current_user,
        name=payload.name,
        max_participants=payload.max_participants,
    )
    return RoomResponse(
        id=room.id,
        room_code=room.room_code,
        name=room.name,
        owner_id=room.owner_id,
        status=room.status.value,
        max_participants=room.max_participants,
        created_at=room.created_at,
        participant_count=1,
    )


# --------------------------------------------------------------------------
# List Rooms
# --------------------------------------------------------------------------
@router.get("/", response_model=list[RoomResponse])
async def list_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all rooms the current user is part of."""
    rooms = await get_user_rooms(db, current_user.id)
    return [
        RoomResponse(
            id=r.id,
            room_code=r.room_code,
            name=r.name,
            owner_id=r.owner_id,
            status=r.status.value if isinstance(r.status, RoomStatus) else r.status,
            max_participants=r.max_participants,
            created_at=r.created_at,
            ended_at=r.ended_at,
            participant_count=0,
        )
        for r in rooms
    ]


# --------------------------------------------------------------------------
# Join Room
# --------------------------------------------------------------------------
@router.post("/join", response_model=RoomResponse)
async def join_existing_room(
    payload: RoomJoin,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join an existing meeting room by room code."""
    room = await join_room(
        db=db,
        user=current_user,
        room_code=payload.room_code,
        language_mode=payload.language_mode,
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found, is full, or has ended",
        )
    return RoomResponse(
        id=room.id,
        room_code=room.room_code,
        name=room.name,
        owner_id=room.owner_id,
        status=room.status.value if isinstance(room.status, RoomStatus) else room.status,
        max_participants=room.max_participants,
        created_at=room.created_at,
        participant_count=0,
    )


# --------------------------------------------------------------------------
# Room Detail
# --------------------------------------------------------------------------
@router.get("/{room_code}", response_model=RoomDetailResponse)
async def get_room_detail(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get room detail with participants."""
    room = await get_room_by_code(db, room_code)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    participants = [
        ParticipantInfo(
            user_id=p.user_id,
            username=p.user.username if p.user else "Unknown",
            language_mode=p.language_mode.value if hasattr(p.language_mode, 'value') else p.language_mode,
            is_active=p.is_active,
        )
        for p in room.participants
    ]

    return RoomDetailResponse(
        id=room.id,
        room_code=room.room_code,
        name=room.name,
        owner_id=room.owner_id,
        status=room.status.value if isinstance(room.status, RoomStatus) else room.status,
        max_participants=room.max_participants,
        created_at=room.created_at,
        ended_at=room.ended_at,
        participant_count=len([p for p in participants if p.is_active]),
        participants=participants,
    )


# --------------------------------------------------------------------------
# Leave Room
# --------------------------------------------------------------------------
@router.post("/{room_code}/leave", status_code=status.HTTP_200_OK)
async def leave_existing_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a meeting room."""
    success = await leave_room(db, current_user.id, room_code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found or not a participant",
        )
    return {"detail": "Left room successfully"}


# --------------------------------------------------------------------------
# End Room (owner only)
# --------------------------------------------------------------------------
@router.post("/{room_code}/end", status_code=status.HTTP_200_OK)
async def end_existing_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """End a meeting room (owner only)."""
    room = await get_room_by_code(db, room_code)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    if room.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the room owner can end the meeting",
        )
    await end_room(db, room)
    return {"detail": "Room ended successfully"}
