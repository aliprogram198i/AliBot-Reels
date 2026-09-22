from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import delete
from ..models import UserCountryPreference,UserPreference
from ..services.validation import validate_category,validate_country_codes
from ..schemas import OnboardingIn
from .dependencies import DB,require_authenticated
router=APIRouter(prefix="/api",tags=["onboarding"])
@router.post("/onboarding")
async def save_onboarding(payload:OnboardingIn,session:DB,user=Depends(require_authenticated)):
    countries=validate_country_codes(payload.countries); category=validate_category(payload.category)
    if category=="adult" and not user.age_eligible: raise HTTPException(403,"age eligibility required")
    await session.execute(delete(UserCountryPreference).where(UserCountryPreference.user_id==user.id))
    for code in countries: session.add(UserCountryPreference(user_id=user.id,country_code=code))
    pref=await session.get(UserPreference,user.id)
    if pref is None: session.add(UserPreference(user_id=user.id,category=category))
    else: pref.category=category
    user.onboarding_complete=True; await session.commit()
    request_cache=__import__("fastapi").Request
    return {"ok":True,"countries":countries,"category":category}
