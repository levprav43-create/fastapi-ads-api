from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# === СХЕМЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=4)
    group: str = Field(default="user", max_length=20)

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    group: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    group: str
    model_config = {"from_attributes": True}

# === СХЕМЫ ДЛЯ ЛОГИНА ===
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# === СХЕМЫ ДЛЯ ОБЪЯВЛЕНИЙ ===
class AdvertisementCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    author: Optional[str] = None
    price: Decimal = Field(..., gt=0)

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    price: Optional[Decimal] = None

class AdvertisementResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    author: Optional[str]
    price: Decimal
    created_at: datetime
    user_id: int
    model_config = {"from_attributes": True}