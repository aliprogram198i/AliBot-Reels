from __future__ import annotations

from contextlib import asynccontextmanager

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .core.cache import FeedCache
from .core.config import FEED_CACHE_TTL, load_settings
from .db import create_session_factory
from .services.auth import AuthService
from .services.feed import FeedService
from .routers import admin, auth, feed, health, me, onboarding

settings = load_settings()
engine, session_factory = create_session_factory(settings.database_url)

oauth = OAuth()
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

feed_cache = FeedCache(FEED_CACHE_TTL)
feed_service = FeedService(feed_cache)
auth_service = AuthService(
    oauth=oauth,
    telegram_bot_token=settings.telegram_bot_token,
    google_redirect_uri=settings.google_redirect_uri,
    frontend_url=settings.frontend_url,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.feed_cache = feed_cache
    app.state.feed_service = feed_service
    app.state.auth_service = auth_service
    yield
    await engine.dispose()


app = FastAPI(title="AliBot Reels API", version="1.2.0", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret or "dev-only-change-me",
    https_only=settings.is_production,
    same_site="lax",
)
if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(onboarding.router)
app.include_router(feed.router)
app.include_router(admin.router)
