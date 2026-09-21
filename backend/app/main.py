from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AliBot Reels API", version="0.1.0")

class Reel(BaseModel):
    id: str
    category: str
    video_url: str
    thumbnail_url: str | None = None
    title: str | None = None

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/feed")
def feed(category: str = "all") -> dict[str, object]:
    # Playback path remains a thin read API. Real media ingestion/storage comes later.
    return {"category": category, "items": []}
