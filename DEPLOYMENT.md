# 🚀 VPS Deployment Guide — Live AI Meeting Interpreter

## Prerequisites

- Ubuntu 22.04+ VPS (4 GB RAM minimum, 8 GB recommended for Whisper)
- Domain name (optional but recommended)
- SSH access

---

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install Git
sudo apt install git -y

# Logout and login again for docker group
exit
```

---

## Step 2: Clone & Configure

```bash
# Clone the project
git clone <your-repo-url> ~/speakfluent-ai
cd ~/speakfluent-ai

# Create production environment file
cp .env.example .env
nano .env
```

### Production `.env` Settings

```env
# IMPORTANT: Change these for production!
SECRET_KEY=<generate-a-random-64-char-string>
POSTGRES_PASSWORD=<strong-random-password>

DATABASE_URL=postgresql+asyncpg://speakfluent:<your-pg-password>@db:5432/speakfluent_db
DATABASE_URL_SYNC=postgresql://speakfluent:<your-pg-password>@db:5432/speakfluent_db

CORS_ORIGINS=https://yourdomain.com,http://yourdomain.com
WHISPER_MODEL=base
```

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Step 3: Build & Launch

```bash
# Build all services
docker compose build

# Start in detached mode
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

---

## Step 4: SSL with Let's Encrypt (Optional but Recommended)

```bash
# Install certbot
sudo apt install certbot -y

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx.conf to use SSL
# Add SSL section and redirect HTTP → HTTPS
```

### SSL Nginx Config Addition

Add to `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # ... (same location blocks as port 80 config)
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

Mount the cert volume in `docker-compose.yml`:
```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

---

## Step 5: Firewall Configuration

```bash
# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## Step 6: Monitoring & Maintenance

### View logs
```bash
docker compose logs -f backend
docker compose logs -f nginx
```

### Restart services
```bash
docker compose restart backend
```

### Update deployment
```bash
git pull
docker compose build
docker compose up -d
```

### Database backup
```bash
docker compose exec db pg_dump -U speakfluent speakfluent_db > backup_$(date +%Y%m%d).sql
```

### Database restore
```bash
cat backup_20260221.sql | docker compose exec -T db psql -U speakfluent speakfluent_db
```

---

## Step 7: Performance Tuning

### Whisper Model Selection

| Model    | RAM   | Speed   | Accuracy |
|----------|-------|---------|----------|
| `tiny`   | ~1 GB | Fastest | Lower    |
| `base`   | ~1 GB | Fast    | Good     |
| `small`  | ~2 GB | Medium  | Better   |
| `medium` | ~5 GB | Slow    | High     |
| `large`  | ~10 GB| Slowest | Highest  |

Update `WHISPER_MODEL` in `.env` based on your server's RAM.

### Scaling

For high-traffic, consider:
1. Running multiple backend workers (update Dockerfile CMD)
2. Using Redis for WebSocket pub/sub across workers
3. Separating Whisper into a dedicated GPU server
4. Adding a CDN for static audio files

---

## Troubleshooting

### Common Issues

1. **Container won't start**: Check `docker compose logs <service>`
2. **Database connection error**: Ensure DB container is healthy first
3. **WebSocket disconnects**: Check nginx timeout settings
4. **Whisper OOM**: Lower `WHISPER_MODEL` to `tiny` or `base`
5. **Audio not playing**: Verify `/static/` nginx path and volume mount

### Health Check

```bash
curl http://localhost/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Live AI Meeting Interpreter",
  "active_rooms": 0,
  "active_connections": 0
}
```
