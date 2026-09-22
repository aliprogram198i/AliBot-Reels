from __future__ import annotations
from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    google_sub: Mapped[str|None]=mapped_column(String(255),unique=True,index=True,nullable=True)
    telegram_id: Mapped[int|None]=mapped_column(unique=True,index=True,nullable=True)
    email: Mapped[str]=mapped_column(String(320),index=True)
    name: Mapped[str|None]=mapped_column(String(255),nullable=True)
    picture: Mapped[str|None]=mapped_column(String(1000),nullable=True)
    age_eligible: Mapped[bool]=mapped_column(Boolean,default=False)
    onboarding_complete: Mapped[bool]=mapped_column(Boolean,default=False)
class UserPreference(Base):
    __tablename__="user_preferences"
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),primary_key=True)
    category: Mapped[str]=mapped_column(String(50),nullable=False,index=True)
class UserCountryPreference(Base):
    __tablename__="user_country_preferences"
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),primary_key=True)
    country_code: Mapped[str]=mapped_column(String(2),primary_key=True)
    __table_args__=(Index("ix_user_country_preferences_country_code","country_code"),)
class Reel(Base):
    __tablename__="reels"
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    category: Mapped[str]=mapped_column(String(50),index=True)
    video_url: Mapped[str]=mapped_column(String(2000))
    thumbnail_url: Mapped[str|None]=mapped_column(String(2000),nullable=True)
    title: Mapped[str|None]=mapped_column(String(500),nullable=True)
    is_adult: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    published: Mapped[bool]=mapped_column(Boolean,default=True,index=True)
class ReelCountry(Base):
    __tablename__="reel_countries"
    reel_id: Mapped[str]=mapped_column(ForeignKey("reels.id",ondelete="CASCADE"),primary_key=True)
    country_code: Mapped[str]=mapped_column(String(2),primary_key=True)
    __table_args__=(Index("ix_reel_countries_country_code","country_code"),)
