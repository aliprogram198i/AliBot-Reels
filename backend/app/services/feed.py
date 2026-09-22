from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.cache import FeedCache
from ..core.config import FEED_LIMIT
from ..models import Reel,ReelCountry,User,UserCountryPreference,UserPreference
from .validation import validate_category
def serialize_reel(reel:Reel)->dict[str,object]: return {"id":reel.id,"category":reel.category,"video_url":reel.video_url,"thumbnail_url":reel.thumbnail_url,"title":reel.title}
class FeedService:
    def __init__(self,cache:FeedCache): self.cache=cache
    async def get_feed(self,session:AsyncSession,user:User,requested_category:str|None):
        if not user.onboarding_complete: raise HTTPException(401,"onboarding required")
        pref=await session.get(UserPreference,user.id)
        if pref is None: raise HTTPException(409,"content preferences are incomplete")
        category=validate_category(requested_category) if requested_category else pref.category
        if category=="adult" and not user.age_eligible: raise HTTPException(403,"age eligibility required")
        rows=await session.execute(select(UserCountryPreference.country_code).where(UserCountryPreference.user_id==user.id).order_by(UserCountryPreference.country_code)); countries=list(rows.scalars())
        if not countries: raise HTTPException(409,"country preferences are incomplete")
        key=f"{user.id}:{category}:{','.join(countries)}"; cached=self.cache.get(key)
        if cached is not None: return {"category":category,"countries":countries,"items":cached}
        stmt=select(Reel).join(ReelCountry,ReelCountry.reel_id==Reel.id).where(Reel.published.is_(True),ReelCountry.country_code.in_(countries),Reel.is_adult.is_(True) if category=="adult" else Reel.is_adult.is_(False)).distinct().order_by(Reel.id.asc()).limit(FEED_LIMIT)
        if category!="all": stmt=stmt.where(Reel.category==category)
        items=[serialize_reel(r) for r in (await session.execute(stmt)).scalars().all()]; self.cache.set(key,items)
        return {"category":category,"countries":countries,"items":items}
