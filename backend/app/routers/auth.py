from fastapi import APIRouter,Request
from ..schemas import TelegramAuthIn
from .dependencies import DB
router=APIRouter(prefix="/api/auth",tags=["auth"])
@router.get("/google/login")
async def google_login(request:Request):
    return await request.app.state.auth_service.google_login(request)
@router.get("/google/callback",name="google_callback")
async def google_callback(request:Request,session:DB):
    return await request.app.state.auth_service.google_callback(request,session)
@router.post("/telegram")
async def telegram_login(payload:TelegramAuthIn,request:Request,session:DB):
    return await request.app.state.auth_service.telegram_login(payload.init_data,request,session)
@router.post("/logout")
async def logout(request:Request):
    request.session.clear(); return {"ok":True}
