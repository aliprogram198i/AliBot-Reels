# AliBot Reels

Telegram Mini App for a fast, vertical Reels-style video feed.

## Architecture

- **Frontend:** React + TypeScript + Vite, packaged as a static Nginx service.
- **Backend:** FastAPI + SQLAlchemy async.
- **Application services:** authentication and feed logic are separated from HTTP transport.
- **Persistence:** SQLAlchemy models + async session factory; PostgreSQL is the production source of truth.
- **Schema evolution:** Alembic migrations are required; startup no longer calls create_all().
- **Adult category:** server-side age eligibility is required before the adult feed is returned.
- **Media:** the API stores URLs to already-hosted media. It does not extract or transcode Instagram media during playback.

## Repository layout

- `frontend/` — Mini App UI and Nginx container.
- `backend/` — API, auth, database models and admin media catalog endpoints.
- `.github/workflows/ci.yml` — backend compile/migration/tests plus frontend and Docker image builds.

## Required deployment variables

Backend:
- `DATABASE_URL`
- `SESSION_SECRET`
- `ALLOWED_ORIGINS`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `ADMIN_API_TOKEN`
- `TELEGRAM_BOT_TOKEN` when Telegram authentication is enabled

Frontend:
- `VITE_API_BASE_URL`

Never put secrets in GitHub source files or the frontend bundle.

## Render staging deployment

The repository is structured as two independently deployable services from the same GitHub repository:

1. **Backend Web Service**
   - Runtime: Docker
   - Root Directory: `backend`
   - Dockerfile: `backend/Dockerfile`
   - Health check: `/health`
2. **Frontend Static Site or Web Service**
   - Root Directory: `frontend`
   - Build output: `dist`
   - `VITE_API_BASE_URL` points to the backend public URL

For the backend, set `DATABASE_URL` to a managed PostgreSQL connection string. The container runs `alembic upgrade head` before starting Uvicorn, so the schema is migrated before the API accepts traffic.

For Google OAuth, `GOOGLE_REDIRECT_URI` must exactly match the public backend callback URL:
`<BACKEND_URL>/api/auth/google/callback`.

For browser credentials, `ALLOWED_ORIGINS` must contain the exact frontend origin and `FRONTEND_URL` must contain the public frontend URL.

For staging, validate in this order:
1. backend deploy succeeds;
2. `GET /health` returns HTTP 200;
3. database migration completes;
4. Google/Telegram authentication works;
5. country + category onboarding persists;
6. feed filtering returns only matching published content;
7. adult feed remains server-side gated;
8. reel playback uses already-hosted HTTPS media;
9. frontend-to-backend CORS/session flow works end to end.

## Architecture evolution rules

1. Keep playback free of extraction, transcoding, AI and blocking analytics.
2. Add business behavior in services before expanding route handlers.
3. Keep cache and media storage behind replaceable boundaries.
4. Add content lifecycle, media assets, cursor pagination and ranking strategies as separate evolutions.
5. Do not introduce Redis, Kafka or microservices until measured workload justifies them.

## Media ingestion

The current backend intentionally accepts **already-hosted HTTPS video URLs**. This is the correct playback-first boundary: downloading/extracting/transcoding Instagram content must happen before publication, never when a user swipes.

To publish a reel, call:

`POST /api/admin/reels`

with:

`Authorization: Bearer <ADMIN_API_TOKEN>`

and JSON containing `id`, `category`, `countries`, `video_url`, optional `thumbnail_url`, `title`, and `is_adult`. `countries` contains supported two-letter country codes.

The actual video source/CDN is deliberately not invented in this repository. It must be selected and configured before production content is added.
