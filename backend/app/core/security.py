from __future__ import annotations
import hashlib,hmac,json,time
from urllib.parse import parse_qsl
from fastapi import Header,HTTPException,Request
from sqlalchemy.ext.asyncio import AsyncSession
from .config import Settings
from ..models import User

def validate_telegram_init_data(init_data:str,bot_token:str)->dict[str,str]:
    if not bot_token: raise HTTPException(503,"Telegram auth is not configured")
    pairs=dict(parse_qsl(init_data,keep_blank_values=True)); received=pairs.pop("hash",None)
    if not received: raise HTTPException(401,"invalid Telegram init data")
    try: auth_date=int(pairs.get("auth_date","0"))
    except ValueError as exc: raise HTTPException(401,"invalid Telegram auth date") from exc
    if abs(time.time()-auth_date)>86400: raise HTTPException(401,"expired Telegram init data")
    check="\n".join(f"{k}={v}" for k,v in sorted(pairs.items())); secret=hmac.new(b"WebAppData",bot_token.encode(),hashlib.sha256).digest(); calculated=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated,received): raise HTTPException(401,"invalid Telegram signature")
    return pairs
async def get_current_user(request:Request,session:AsyncSession)->User|None:
    user_id=request.session.get("user_id")
    return await session.get(User,int(user_id)) if user_id else None
async def require_admin(authorization:str|None=Header(default=None),settings:Settings=None)->None:
    if not settings or not settings.admin_api_token or authorization!=f"Bearer {settings.admin_api_token}": raise HTTPException(401,"admin authorization required")
def telegram_user_from_init_data(data:dict[str,str])->tuple[int,dict]:
    raw=data.get("user")
    if not raw: raise HTTPException(400,"Telegram user is missing")
    try: obj=json.loads(raw); return int(obj["id"]),obj
    except (TypeError,ValueError,KeyError,json.JSONDecodeError) as exc: raise HTTPException(400,"invalid Telegram user") from exc
