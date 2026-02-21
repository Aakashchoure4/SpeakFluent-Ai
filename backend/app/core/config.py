"""
Application configuration loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings sourced from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://speakfluent:speakfluent_pass@localhost:5432/speakfluent_db",
    )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://speakfluent:speakfluent_pass@localhost:5432/speakfluent_db",
    )

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )

    # Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")

    # CORS
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
        ).split(",")
    ]

    # Static files directory for generated audio
    STATIC_DIR: str = os.getenv(
        "STATIC_DIR",
        str(Path(__file__).resolve().parents[1] / "static"),
    )

    # Audio subdirectory
    AUDIO_DIR: str = os.path.join(STATIC_DIR, "audio")

    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        os.makedirs(cls.STATIC_DIR, exist_ok=True)
        os.makedirs(cls.AUDIO_DIR, exist_ok=True)


settings = Settings()
settings.ensure_directories()
