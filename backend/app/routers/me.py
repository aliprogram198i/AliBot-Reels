from fastapi import APIRouter,HTTPException,Request
from sqlalchemy import select
from ..models import UserCountryPreference,UserPreference
from .dependencies import DB,require_authenticated
router=APIRouter(prefix="/api",tags=["users"])
@router.get("/me")
async def me(request:Request,session:DB):
    user=await request.app.state.current_user(request,session)
    if not user: return {"authenticated":False,"user":None}
    pref=await session.get(UserPreference,user.id); rows=await session.execute(select(UserCountryPreference.country_code).where(UserCountryPreference.user_id==user.id).order_by(UserCountryPreference.country_code))
    return {"authenticated":True,"user":{"id":user.id,"email":user.email,"name":user.name,"picture":user.picture,"age_eligible":user.age_eligible,"onboarding_complete":user.onboarding_complete,"countries":list(rows.scalars()),"category":pref.category if pref else None}}
@router.post("/me/age-eligibility")
async def set_age_eligibility(session:DB,user=__import__("fastapi").Depends(require_authenticated)):
    user.age_eligible=True; await session.commit(); return {"age_eligible":True}
