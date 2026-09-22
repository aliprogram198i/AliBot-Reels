from __future__ import annotations

import os
from dataclasses import dataclass

COUNTRY_CODES = frozenset({"NL", "DE", "FR", "GB", "US", "CA", "TR", "SA", "AE", "EG", "IQ", "JO", "MA", "DZ", "TN", "ES", "IT", "SE", "NO", "AU"})
CATEGORIES = frozenset({"all", "sports", "gaming", "music", "entertainment", "kids", "food", "animals", "travel", "fitness", "adult"})
MAX_COUNTRIES_PER_USER = 20
FEED_LIMIT = 50
FEED_CACHE_TTL = 15.0

@dataclass(frozen=True)
class Settings:
    database_url: str
    app_env: str
    session_secret: str
    admin_api_token: str
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    allowed_origins: tuple[str, ...]
    frontend_url: str
    telegram_bot_token: str
    @property
    def is_production(self) -> bool: return self.app_env == "production"

def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./reels.db").replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")

def load_settings() -> Settings:
    allowed = tuple(x.strip() for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip())
    settings = Settings(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./reels.db").replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://"), os.getenv("APP_ENV", "development"), os.getenv("SESSION_SECRET", ""), os.getenv("ADMIN_API_TOKEN", ""), os.getenv("GOOGLE_CLIENT_ID", ""), os.getenv("GOOGLE_CLIENT_SECRET", ""), os.getenv("GOOGLE_REDIRECT_URI", ""), allowed, os.getenv("FRONTEND_URL", "http://localhost:5173"), os.getenv("TELEGRAM_BOT_TOKEN", ""))
    if settings.is_production and not settings.session_secret: raise RuntimeError("SESSION_SECRET is required in production")
    return settings
