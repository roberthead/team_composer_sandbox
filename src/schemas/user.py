from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    name_first: str
    name_middle: Optional[str] = None
    name_last: str
    email: EmailStr
    job_title: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name_first: Optional[str] = None
    name_middle: Optional[str] = None
    name_last: Optional[str] = None
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True