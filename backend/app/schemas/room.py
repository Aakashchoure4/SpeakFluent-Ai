"""
Pydantic request / response schemas for meeting rooms.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ---------------------------------------------------------------------------
# Room Create
# ---------------------------------------------------------------------------
class RoomCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    max_participants: int = Field(default=10, ge=2, le=100)


# ---------------------------------------------------------------------------
# Room Response
# ---------------------------------------------------------------------------
class ParticipantInfo(BaseModel):
    user_id: int
    username: str
    language_mode: str
    is_active: bool

    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    id: int
    room_code: str
    name: str
    owner_id: int
    status: str
    max_participants: int
    created_at: datetime
    ended_at: Optional[datetime] = None
    participant_count: int = 0

    class Config:
        from_attributes = True


class RoomDetailResponse(RoomResponse):
    participants: List[ParticipantInfo] = []


# ---------------------------------------------------------------------------
# Room Join
# ---------------------------------------------------------------------------
class RoomJoin(BaseModel):
    room_code: str = Field(..., min_length=4, max_length=20)
    language_mode: str = Field(default="hi_to_en", pattern="^(hi_to_en|en_to_hi)$")


# ---------------------------------------------------------------------------
# Message Response
# ---------------------------------------------------------------------------
class MessageResponse(BaseModel):
    id: int
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    audio_url: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
