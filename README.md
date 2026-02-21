# 🌐 Live AI Meeting Interpreter

Real-time AI-powered meeting interpreter with live translation between Hindi and English.  
Built with FastAPI, React, WebSockets, Whisper, and Edge-TTS.

---

## 🚀 Features

- **Real-Time Translation**: Hindi ↔ English live translation
- **Voice Output**: Edge-TTS powered voice synthesis
- **Meeting Rooms**: Multi-user room support with unique room IDs
- **WebSocket Streaming**: Low-latency audio streaming
- **JWT Authentication**: Secure user registration and login
- **Admin-Ready**: Base structure for admin panel
- **Docker Support**: Full Docker Compose deployment

---

## 📁 Project Structure

```
speakfluent-ai/
├── backend/
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Config, security, dependencies
│   │   ├── db/             # Database models & session
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic services
│   │   ├── websocket/      # WebSocket handlers
│   │   └── main.py         # FastAPI application entry
│   ├── alembic/            # Database migrations
│   ├── static/             # Generated audio files
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── pages/          # Page components
│   │   ├── services/       # API & WebSocket services
│   │   ├── context/        # React context providers
│   │   └── styles/         # CSS files
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
└── .env
```

---

## 🛠 Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- FFmpeg (for Whisper)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
cp .env.example .env         # Edit with your settings
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🐳 Docker Deployment

```bash
# Copy and edit environment
cp .env.example .env

# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f
```

Access at: `http://localhost`

---

## 🔊 Audio Flow

```
User Microphone
      ↓
WebSocket Stream (binary audio chunks)
      ↓
Whisper Transcription (speech-to-text)
      ↓
Language Detection (Hindi/English)
      ↓
Translation Engine (deep-translator)
      ↓
Edge-TTS Voice Synthesis
      ↓
Response to all room participants:
  • Original text
  • Translated text
  • Audio playback URL
```

---

## 📝 API Endpoints

| Method | Endpoint                  | Description           |
|--------|---------------------------|-----------------------|
| POST   | `/api/auth/register`      | Register new user     |
| POST   | `/api/auth/login`         | Login & get JWT token |
| GET    | `/api/auth/me`            | Get current user      |
| POST   | `/api/rooms/`             | Create meeting room   |
| GET    | `/api/rooms/`             | List your rooms       |
| GET    | `/api/rooms/{room_id}`    | Get room details      |
| WS     | `/ws/{room_id}?token=JWT` | WebSocket connection  |

---

## ⚙️ Environment Variables

| Variable              | Description                    | Default              |
|-----------------------|--------------------------------|----------------------|
| `DATABASE_URL`        | PostgreSQL connection string   | —                    |
| `SECRET_KEY`          | JWT signing key                | —                    |
| `WHISPER_MODEL`       | Whisper model size             | `base`               |
| `CORS_ORIGINS`        | Allowed CORS origins           | `http://localhost:*` |
| `STATIC_DIR`          | Audio file output directory    | `./static`           |

---

## 📄 License

MIT License — Build freely.
