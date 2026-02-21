"""
Live AI Meeting Interpreter — FastAPI Application Entry Point.

Bootstraps the application with:
  - CORS middleware
  - Static file serving
  - API route registration
  - WebSocket route registration
  - Database initialization on startup
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.session import init_db
from app.api.auth import router as auth_router
from app.api.rooms import router as rooms_router
from app.websocket.handler import router as ws_router

# ---------------------------------------------------------------------------
# Logging — UTF-8 safe
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(
            stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
        )
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("🚀 Starting Live AI Meeting Interpreter …")
    await init_db()
    logger.info("✅ Database tables ensured.")
    settings.ensure_directories()
    logger.info("✅ Static directories ready.")
    yield
    logger.info("🛑 Shutting down …")


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Live AI Meeting Interpreter",
    description="Real-time Hindi ↔ English meeting interpreter with voice output",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static Files (generated audio)
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(ws_router)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and Docker."""
    from app.websocket.manager import manager

    return {
        "status": "healthy",
        "service": "Live AI Meeting Interpreter",
        "active_rooms": manager.get_room_count(),
        "active_connections": manager.get_total_connections(),
    }
