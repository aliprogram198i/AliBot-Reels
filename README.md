# AliBot Reels

Telegram Mini App for fast vertical video playback with category-based feeds and Google authentication.

## MVP principles
- Playback-first: no AI or heavy processing in the playback path.
- Vertical swipe feed.
- One-item prefetch by default.
- Category filtering.
- Google OAuth prepared, credentials supplied through environment variables.
- Adult category is isolated behind age eligibility checks.

## Structure
- `frontend/` — React + TypeScript + Vite Mini App UI.
- `backend/` — FastAPI API, feed and auth boundaries.

This repository intentionally contains no production secrets.
