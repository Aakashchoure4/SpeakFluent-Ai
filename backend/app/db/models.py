"""
SQLAlchemy ORM models for the application.

Models:
  - User:             Registered users
  - Room:             Meeting rooms
  - RoomParticipant:  Users in a room
  - MessageLog:       Transcription / translation log
  - SubscriptionPlan: Billing plans (admin-ready)
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class LanguageMode(str, enum.Enum):
    HINDI_TO_ENGLISH = "hi_to_en"
    ENGLISH_TO_HINDI = "en_to_hi"


class RoomStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"


class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owned_rooms = relationship("Room", back_populates="owner", lazy="selectin")
    participations = relationship(
        "RoomParticipant", back_populates="user", lazy="selectin"
    )
    plan = relationship("SubscriptionPlan", back_populates="users", lazy="selectin")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(
        SAEnum(RoomStatus), default=RoomStatus.ACTIVE, nullable=False
    )
    max_participants = Column(Integer, default=10, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_rooms", lazy="selectin")
    participants = relationship(
        "RoomParticipant", back_populates="room", lazy="selectin"
    )
    messages = relationship("MessageLog", back_populates="room", lazy="selectin")

    def __repr__(self):
        return f"<Room id={self.id} code={self.room_code}>"


# ---------------------------------------------------------------------------
# Room Participant (join table with metadata)
# ---------------------------------------------------------------------------
class RoomParticipant(Base):
    __tablename__ = "room_participants"
    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_mode = Column(
        SAEnum(LanguageMode),
        default=LanguageMode.HINDI_TO_ENGLISH,
        nullable=False,
    )
    joined_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    room = relationship("Room", back_populates="participants")
    user = relationship("User", back_populates="participations")


# ---------------------------------------------------------------------------
# Message Log
# ---------------------------------------------------------------------------
class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    audio_url = Column(String(500), nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    room = relationship("Room", back_populates="messages")


# ---------------------------------------------------------------------------
# Subscription Plan
# ---------------------------------------------------------------------------
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    tier = Column(SAEnum(PlanTier), default=PlanTier.FREE, nullable=False)
    max_rooms = Column(Integer, default=3, nullable=False)
    max_minutes_per_month = Column(Integer, default=60, nullable=False)
    price_monthly = Column(Float, default=0.0, nullable=False)
    features = Column(Text, nullable=True)  # JSON string for flexibility
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    users = relationship("User", back_populates="plan", lazy="selectin")

    def __repr__(self):
        return f"<SubscriptionPlan id={self.id} name={self.name}>"
