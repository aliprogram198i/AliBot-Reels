from __future__ import annotations
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException,Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.security import telegram_user_from_init_data,validate_telegram_init_data
from ..models import User
class AuthService:
    def __init__(self,oauth:OAuth,telegram_bot_token:str,google_redirect_uri:str,frontend_url:str): self.oauth=oauth; self.telegram_bot_token=telegram_bot_token; self.google_redirect_uri=google_redirect_uri; self.frontend_url=frontend_url
    async def google_login(self,request:Request):
        if not self.oauth.google: raise HTTPException(503,"Google OAuth is not configured")
        return await self.oauth.google.authorize_redirect(request,self.google_redirect_uri or str(request.url_for("google_callback")))
    async def google_callback(self,request:Request,session:AsyncSession):
        if not self.oauth.google: raise HTTPException(503,"Google OAuth is not configured")
        token=await self.oauth.google.authorize_access_token(request); info=token.get("userinfo")
        if not info or not info.get("sub") or not info.get("email"): raise HTTPException(400,"Google identity is incomplete")
        result=await session.execute(select(User).where(User.google_sub==info["sub"])); user=result.scalar_one_or_none()
        if user is None: user=User(google_sub=info["sub"],email=info["email"],name=info.get("name"),picture=info.get("picture")); session.add(user)
        else: user.email=info["email"]; user.name=info.get("name"); user.picture=info.get("picture")
        await session.commit(); await session.refresh(user); request.session["user_id"]=user.id; return RedirectResponse(url=self.frontend_url,status_code=303)
    async def telegram_login(self,init_data:str,request:Request,session:AsyncSession):
        data=validate_telegram_init_data(init_data,self.telegram_bot_token); tid,tuser=telegram_user_from_init_data(data); result=await session.execute(select(User).where(User.telegram_id==tid)); user=result.scalar_one_or_none()
        if user is None: user=User(telegram_id=tid,email=f"telegram-{tid}@users.invalid",name=tuser.get("first_name")); session.add(user)
        else: user.name=tuser.get("first_name") or user.name
        await session.commit(); await session.refresh(user); request.session["user_id"]=user.id; return {"authenticated":True,"telegram_id":tid}
