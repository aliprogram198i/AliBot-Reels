from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl
from .core.config import MAX_COUNTRIES_PER_USER
class OnboardingIn(BaseModel):
    countries:list[str]=Field(min_length=1,max_length=MAX_COUNTRIES_PER_USER)
    category:str=Field(min_length=1,max_length=50)
class TelegramAuthIn(BaseModel): init_data:str=Field(min_length=1,max_length=8192)
class ReelIn(BaseModel):
    id:str=Field(min_length=1,max_length=100); category:str=Field(min_length=1,max_length=50); countries:list[str]=Field(min_length=1,max_length=MAX_COUNTRIES_PER_USER); video_url:HttpUrl; thumbnail_url:HttpUrl|None=None; title:str|None=Field(default=None,max_length=500); is_adult:bool=False
