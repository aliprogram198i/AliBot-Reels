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
- `.github/workflows/ci.yml` — backend compile check and frontend production build.

## Required production variables

Backend:
- `DATABASE_URL`
- `SESSION_SECRET`
- `ALLOWED_ORIGINS`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `ADMIN_API_TOKEN`

Frontend:
- `VITE_API_BASE_URL`

Do not put secrets in GitHub or the frontend bundle.

## Architecture evolution rules\n\n1. Keep playback free of extraction, transcoding, AI and blocking analytics.\n2. Add business behavior in services before expanding route handlers.\n3. Keep cache and media storage behind replaceable boundaries.\n4. Add content lifecycle, media assets, cursor pagination and ranking strategies as separate evolutions.\n5. Do not introduce Redis, Kafka or microservices until measured workload justifies them.\n\n## Media ingestion

The current backend intentionally accepts **already-hosted HTTPS video URLs**. This is the correct playback-first boundary: downloading/extracting/transcoding Instagram content must happen before publication, never when a user swipes.

To publish a reel, call:

`POST /api/admin/reels`

with:

`Authorization: Bearer <ADMIN_API_TOKEN>`

and JSON containing `id`, `category`, `countries`, `video_url`, optional `thumbnail_url`, `title`, and `is_adult`. `countries` contains supported two-letter country codes.

The actual video source/CDN is deliberately not invented in this repository. It must be selected and configured before production content is added.

## Railway

This is an isolated monorepo. Create two services from the same GitHub repository:
1. Backend — root directory `/backend`
2. Frontend — root directory `/frontend`

Set the backend URL in the frontend as `VITE_API_BASE_URL`. Set the frontend public URL in backend `ALLOWED_ORIGINS`.

Railway can deploy each isolated directory as a separate service.
