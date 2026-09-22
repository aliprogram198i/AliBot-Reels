from fastapi import APIRouter,Depends,Header,HTTPException
from ..models import Reel,ReelCountry
from ..schemas import ReelIn
from ..services.validation import validate_category,validate_country_codes
from .dependencies import DB
router=APIRouter(prefix="/api/admin",tags=["admin"])
async def admin_guard(authorization:str|None=Header(default=None)):
    raise RuntimeError("admin_guard must be bound by application startup")
@router.post("/reels")
async def create_reel(payload:ReelIn,session:DB):
    raise RuntimeError("admin route not initialized")
@router.delete("/reels/{reel_id}")
async def delete_reel(reel_id:str,session:DB):
    raise RuntimeError("admin route not initialized")
