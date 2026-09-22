from fastapi import APIRouter,Depends,Query
from ..services.feed import FeedService
from .dependencies import DB,require_authenticated
router=APIRouter(prefix="/api",tags=["feed"])
@router.get("/feed")
async def feed(session:DB,user=Depends(require_authenticated),category:str|None=Query(None,max_length=50)):
    return await FeedService.current().get_feed(session,user,category)
