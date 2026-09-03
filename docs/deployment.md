# RePackAI — Production Deployment Guide

This document provides setup instructions for deploying RePackAI in local development, production, and Dockerized environments.

## 1. Environment Setup

Copy `.env.example` to `.env` and configure key variables:
```bash
cp repackai/.env.example repackai/backend/.env
```

Key Settings:
*   `DATABASE_URL`: Set to `sqlite:///./repackai.db` (local development) or standard postgres URI.
*   `VITE_API_URL`: Mapped to backend host (default: `http://localhost:8000`).

---

## 2. Docker Containerized Deployment (Recommended)

RePackAI features a production-style container architecture. Ensure Docker and Docker Compose are installed, then run:

```bash
# Build and start services in detached background mode
docker-compose up --build -d
```

This single command:
1.  Downloads base images (python:3.11-slim and node:18-alpine).
2.  Spawns `backend` container running Uvicorn at `http://localhost:8000`.
3.  Spawns `frontend` container compiling assets and running Nginx static hosting at `http://localhost:3000`.
4.  Creates the persistent database volume.

To stop services:
```bash
docker-compose down
```

---

## 3. Manual Server Deployment

### Backend Deployment
Ensure Python 3.11+ is installed, then run:
```bash
cd repackai/backend
pip install -r requirements.txt

# Run migrations & seed Rules
python ../scripts/seed_database.py

# Run training
python ../scripts/train_model.py

# Launch production ASGI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment
Ensure Node.js 18+ is installed, then run:
```bash
cd repackai/frontend
npm install

# Build static production bundle
npm run build
```
The compiled HTML/JS/CSS assets will be written to `repackai/frontend/dist`. Deploy this directory to Nginx, AWS S3, or any static file host.
