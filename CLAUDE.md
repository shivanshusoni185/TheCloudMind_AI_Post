# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TheCloudMind AI Post is a full-stack AI news platform with a FastAPI backend and React frontend, deployed on Fly.io. The backend auto-aggregates news from RSS feeds and exposes a REST API; the frontend consumes it via a Vite proxy.

## Commands

### Frontend (`/frontend`)
```bash
npm run dev       # Start Vite dev server (proxies /api → localhost:8000)
npm run build     # Production build
npm run lint      # ESLint
npm run preview   # Preview production build
```

### Backend (`/backend`)
```bash
# Create and activate virtualenv
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run slug migration (one-time)
python migrate_slugs.py
```

### Required Backend `.env`
```
DATABASE_URL=postgresql://user:password@host:5432/db
ADMIN_USERNAME=admin@example.com
ADMIN_PASSWORD=your_password
JWT_SECRET=your_jwt_secret
# Optional scheduler settings (defaults shown):
AUTO_PUBLISH_ENABLED=true
AUTO_PUBLISH_TIMEZONE=Asia/Kolkata
AUTO_PUBLISH_HOUR=9
AUTO_PUBLISH_MINUTE=0
AUTO_PUBLISH_MAX_PER_TOPIC=5
AUTO_PUBLISH_RUN_ON_STARTUP=false
```

## Architecture

### Backend (`/backend/app/`)

**Entry point**: `main.py` — creates the FastAPI app, registers routers, starts the APScheduler on startup.

**Routers** (`routers/`):
- `news.py` — public endpoints: list/search articles, get by slug, serve images
- `admin.py` — protected CRUD for articles (JWT-gated), admin login
- `contact.py` — contact form submissions

**Models** (`models.py`): Two SQLAlchemy models:
- `News` — articles with binary image storage (LargeBinary), auto-generated slugs, publish flag
- `Contact` — form submissions with read-status tracking

**Auth** (`auth.py`): Single admin user from env vars. Argon2 password hashing, JWT tokens (24h expiry), OAuth2PasswordBearer scheme.

**Auto-publish** (`services/auto_publish.py`): Fetches Google News RSS feeds for AI/Sports topics, downloads images, deduplicates, and inserts published articles. Triggered by APScheduler (`scheduler.py`) on a configurable cron.

**Images** are stored as binary blobs in PostgreSQL (not filesystem). The image endpoint serves them with proper MIME type headers; legacy file-based URLs are handled for backward compatibility.

### Frontend (`/frontend/src/`)

**Routing** (`App.jsx`): React Router v7 with pages for Home, LatestNews, Article (by slug), AdminLogin, AdminDashboard, ContactUs, AboutUs.

**API** (`lib/api.js`): Axios client pointing at `/api` (proxied by Vite to the backend in dev, handled by nginx in production).

**Admin flow**: `AdminLogin` stores JWT in state/localStorage → `AdminDashboard` sends `Authorization: Bearer <token>` for article CRUD.

### Deployment

Both services have their own `Dockerfile` and `fly.toml`. The frontend's nginx (`nginx.conf`) handles SPA routing and proxies `/api` to the backend service in production.
