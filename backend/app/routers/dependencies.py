from __future__ import annotations
from typing import Annotated
from fastapi import Depends,Header,HTTPException,Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.security import get_current_user
from ..models import User
async def db_session(request:Request):
    async with request.app.state.session_factory() as session: yield session
DB=Annotated[AsyncSession,Depends(db_session)]
async def current_user(request:Request,session:DB)->User|None: return await get_current_user(request,session)
def require_authenticated(user:User|None=Depends(current_user))->User:
    if user is None: raise HTTPException(401,"login required")
    return user
async def require_admin(request:Request,authorization:str|None=Header(default=None)):
    token=request.app.state.settings.admin_api_token
    if not token or authorization!=f"Bearer {token}": raise HTTPException(401,"admin authorization required")
