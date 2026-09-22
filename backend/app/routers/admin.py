from fastapi import APIRouter,Depends,HTTPException,Request
from ..models import Reel,ReelCountry
from ..schemas import ReelIn
from ..services.validation import validate_category,validate_country_codes
from .dependencies import DB,require_admin
router=APIRouter(prefix="/api/admin",tags=["admin"])
@router.post("/reels",dependencies=[Depends(require_admin)])
async def create_reel(payload:ReelIn,request:Request,session:DB):
    category=validate_category(payload.category); countries=validate_country_codes(payload.countries)
    if category=="adult" and not payload.is_adult: raise HTTPException(422,"adult category requires is_adult=true")
    if category!="adult" and payload.is_adult: raise HTTPException(422,"is_adult=true requires adult category")
    if await session.get(Reel,payload.id): raise HTTPException(409,"reel id already exists")
    reel=Reel(id=payload.id,category=category,video_url=str(payload.video_url),thumbnail_url=str(payload.thumbnail_url) if payload.thumbnail_url else None,title=payload.title,is_adult=payload.is_adult,published=True)
    session.add(reel)
    for code in countries: session.add(ReelCountry(reel_id=payload.id,country_code=code))
    await session.commit(); request.app.state.feed_cache.clear()
    return {"ok":True,"id":reel.id,"countries":countries,"category":category}
@router.delete("/reels/{reel_id}",dependencies=[Depends(require_admin)])
async def delete_reel(reel_id:str,request:Request,session:DB):
    reel=await session.get(Reel,reel_id)
    if not reel: raise HTTPException(404,"reel not found")
    await session.delete(reel); await session.commit(); request.app.state.feed_cache.clear(); return {"ok":True}
