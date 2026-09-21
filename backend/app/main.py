from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl
from contextlib import asynccontextmanager
from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import Boolean, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.middleware.sessions import SessionMiddleware

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./reels.db").replace(
    "postgres://", "postgresql+asyncpg://"
).replace("postgresql://", "postgresql+asyncpg://"
)
APP_ENV = os.getenv("APP_ENV", "development")
SESSION_SECRET = os.getenv("SESSION_SECRET", "")
ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip()]
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

if not SESSION_SECRET and APP_ENV == "production":
    raise RuntimeError("SESSION_SECRET is required in production")

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    telegram_id: Mapped[int | None] = mapped_column(unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    age_eligible: Mapped[bool] = mapped_column(Boolean, default=False)

class Reel(Base):
    __tablename__ = "reels"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    video_url: Mapped[str] = mapped_column(String(2000))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_adult: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

class TelegramAuthIn(BaseModel):
    init_data: str = Field(min_length=1, max_length=8192)

class ReelIn(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    video_url: HttpUrl
    thumbnail_url: HttpUrl | None = None
    title: str | None = Field(default=None, max_length=500)
    is_adult: bool = False

engine_kwargs = {"pool_pre_ping": True} if DATABASE_URL.startswith("postgresql") else {}
engine = create_async_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

oauth = OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

_feed_cache: dict[str, tuple[float, list[dict[str, object]]]] = {}
FEED_CACHE_TTL = 15.0

@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="AliBot Reels API", version="1.0.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET or "dev-only-change-me", https_only=APP_ENV == "production", same_site="lax")
if ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

async def db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

DB = Annotated[AsyncSession, Depends(db)]

async def current_user(request: Request, session: DB) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return await session.get(User, int(user_id))

def validate_telegram_init_data(init_data: str) -> dict[str, str]:
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        raise HTTPException(status_code=503, detail="Telegram auth is not configured")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="invalid Telegram init data")
    auth_date = int(pairs.get("auth_date", "0"))
    if abs(time.time() - auth_date) > 86400:
        raise HTTPException(status_code=401, detail="expired Telegram init data")
    check_string = "
".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", os.environ["TELEGRAM_BOT_TOKEN"].encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(status_code=401, detail="invalid Telegram signature")
    return pairs

async def require_admin(authorization: Annotated[str | None, Header()] = None) -> None:
    if not ADMIN_API_TOKEN or authorization != f"Bearer {ADMIN_API_TOKEN}":
        raise HTTPException(status_code=401, detail="admin authorization required")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/me")
async def me(request: Request, session: DB) -> dict[str, object | None]:
    user = await current_user(request, session)
    if not user:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture, "age_eligible": user.age_eligible},
    }

@app.get("/api/auth/google/login")
async def google_login(request: Request):
    if not oauth.google:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    redirect_uri = GOOGLE_REDIRECT_URI or str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/api/auth/google/callback", name="google_callback")
async def google_callback(request: Request, session: DB):
    if not oauth.google:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("sub") or not userinfo.get("email"):
        raise HTTPException(status_code=400, detail="Google identity is incomplete")
    result = await session.execute(select(User).where(User.google_sub == userinfo["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(google_sub=userinfo["sub"], email=userinfo["email"], name=userinfo.get("name"), picture=userinfo.get("picture"))
        session.add(user)
    else:
        user.email = userinfo["email"]
        user.name = userinfo.get("name")
        user.picture = userinfo.get("picture")
    await session.commit()
    await session.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse(url=FRONTEND_URL, status_code=303)

@app.post("/api/auth/telegram")
async def telegram_login(payload: TelegramAuthIn, request: Request, session: DB):
    data = validate_telegram_init_data(payload.init_data)
    raw_user = data.get("user")
    if not raw_user:
        raise HTTPException(status_code=400, detail="Telegram user is missing")
    telegram_user = json.loads(raw_user)
    telegram_id = int(telegram_user["id"])
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, email=f"telegram-{telegram_id}@users.invalid", name=telegram_user.get("first_name"))
        session.add(user)
    else:
        user.name = telegram_user.get("first_name") or user.name
    await session.commit()
    await session.refresh(user)
    request.session["user_id"] = user.id
    return {"authenticated": True, "telegram_id": telegram_id}

@app.post("/api/auth/logout")
async def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"ok": True}

@app.post("/api/me/age-eligibility")
async def set_age_eligibility(request: Request, session: DB):
    user = await current_user(request, session)
    if not user:
        raise HTTPException(status_code=401, detail="login required")
    user.age_eligible = True
    await session.commit()
    return {"age_eligible": True}

@app.get("/api/feed")
async def feed(request: Request, session: DB, category: str = Query("all", max_length=50)):
    is_adult = category == "adult"
    if is_adult:
        user = await current_user(request, session)
        if not user or not user.age_eligible:
            raise HTTPException(status_code=403, detail="age eligibility required")

    cache_key = category
    cached = _feed_cache.get(cache_key)
    now = time.monotonic()
    if cached and now - cached[0] < FEED_CACHE_TTL:
        return {"category": category, "items": cached[1]}

    stmt = select(Reel).where(Reel.published.is_(True))
    stmt = stmt.where(Reel.is_adult.is_(True) if is_adult else Reel.is_adult.is_(False))
    if category != "all":
        stmt = stmt.where(Reel.category == category)
    stmt = stmt.limit(50)
    rows = (await session.execute(stmt)).scalars().all()
    items = [
        {"id": r.id, "category": r.category, "video_url": r.video_url, "thumbnail_url": r.thumbnail_url, "title": r.title}
        for r in rows
    ]
    _feed_cache[cache_key] = (now, items)
    return {"category": category, "items": items}

@app.post("/api/admin/reels", dependencies=[Depends(require_admin)])
async def create_reel(payload: ReelIn, session: DB):
    existing = await session.get(Reel, payload.id)
    if existing:
        raise HTTPException(status_code=409, detail="reel id already exists")
    reel = Reel(
        id=payload.id, category=payload.category, video_url=str(payload.video_url),
        thumbnail_url=str(payload.thumbnail_url) if payload.thumbnail_url else None,
        title=payload.title, is_adult=payload.is_adult, published=True,
    )
    session.add(reel)
    await session.commit()
    _feed_cache.clear()
    return {"ok": True, "id": reel.id}

@app.delete("/api/admin/reels/{reel_id}", dependencies=[Depends(require_admin)])
async def delete_reel(reel_id: str, session: DB):
    reel = await session.get(Reel, reel_id)
    if not reel:
        raise HTTPException(status_code=404, detail="reel not found")
    await session.delete(reel)
    await session.commit()
    _feed_cache.clear()
    return {"ok": True}
