# app/main.py
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_session, init_db
from app.models import Advertisement, User
from app.schemas import (
    AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse,
    UserCreate, UserUpdate, UserResponse, LoginRequest, TokenResponse,
)
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_auth,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Ads API Part 2", lifespan=lifespan)


# ==================== LOGIN ====================
@app.post("/login", response_model=TokenResponse, tags=["Auth"])
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    """Логин. Возвращает JWT токен на 48 часов. 401 при неверных данных."""
    result = await session.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer",
    }


# ==================== USERS ====================
@app.post("/user", response_model=UserResponse, status_code=201, tags=["Users"])
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Создать пользователя. Доступно всем (без токена)."""
    existing = await session.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Пользователь уже существует")
    if data.group not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Группа должна быть user или admin")

    new_user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        group=data.group,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@app.get("/user", response_model=List[UserResponse], tags=["Users"])
async def list_users(session: AsyncSession = Depends(get_session)):
    """Получить СПИСОК всех пользователей. Доступно всем (без токена)."""
    result = await session.execute(select(User))
    return result.scalars().all()


@app.get("/user/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    """Получить пользователя по ID. Доступно всем (без токена)."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.patch("/user/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """Обновить пользователя. Только себя или админ."""
    if current_user.id != user_id and current_user.group != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    update_data = data.model_dump(exclude_unset=True)
    if "username" in update_data:
        user.username = update_data["username"]
    if "password" in update_data:
        user.hashed_password = get_password_hash(update_data["password"])
    if "group" in update_data:
        if current_user.group != "admin":
            raise HTTPException(status_code=403, detail="Только админ может менять группу")
        user.group = update_data["group"]

    await session.commit()
    await session.refresh(user)
    return user


@app.delete("/user/{user_id}", status_code=204, tags=["Users"])
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """Удалить пользователя. Только себя или админ."""
    if current_user.id != user_id and current_user.group != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await session.delete(user)
    await session.commit()
    return JSONResponse(status_code=204, content=None)


# ==================== ОБЪЯВЛЕНИЯ ====================
@app.post("/advertisement", response_model=AdvertisementResponse, status_code=201, tags=["Ads"])
async def create_ad(
    data: AdvertisementCreate,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """Создать объявление. Нужна авторизация."""
    new_ad = Advertisement(
        title=data.title,
        description=data.description,
        author=data.author,
        price=data.price,
        user_id=current_user.id,
    )
    session.add(new_ad)
    await session.commit()
    await session.refresh(new_ad)
    return new_ad


@app.get("/advertisement/{ad_id}", response_model=AdvertisementResponse, tags=["Ads"])
async def get_ad(ad_id: int, session: AsyncSession = Depends(get_session)):
    """Получить объявление по ID. Доступно всем."""
    result = await session.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return ad


@app.get("/advertisement", response_model=List[AdvertisementResponse], tags=["Ads"])
async def search_ads(
    title: Optional[str] = None,
    description: Optional[str] = None,
    author: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
):
    """Поиск объявлений по полям. Доступно всем."""
    query = select(Advertisement)
    conditions = []
    if title:
        conditions.append(Advertisement.title.ilike(f"%{title}%"))
    if description:
        conditions.append(Advertisement.description.ilike(f"%{description}%"))
    if author:
        conditions.append(Advertisement.author.ilike(f"%{author}%"))
    if min_price is not None:
        conditions.append(Advertisement.price >= min_price)
    if max_price is not None:
        conditions.append(Advertisement.price <= max_price)
    if min_date is not None:
        conditions.append(Advertisement.created_at >= min_date)
    if max_date is not None:
        conditions.append(Advertisement.created_at <= max_date)
    if conditions:
        query = query.where(and_(*conditions))

    result = await session.execute(query)
    return result.scalars().all()


@app.patch("/advertisement/{ad_id}", response_model=AdvertisementResponse, tags=["Ads"])
async def update_ad(
    ad_id: int,
    data: AdvertisementUpdate,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """Обновить объявление. Только своё или админ."""
    result = await session.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if current_user.group != "admin" and ad.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ad, key, value)
    await session.commit()
    await session.refresh(ad)
    return ad


@app.delete("/advertisement/{ad_id}", status_code=204, tags=["Ads"])
async def delete_ad(
    ad_id: int,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """Удалить объявление. Только своё или админ."""
    result = await session.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if current_user.group != "admin" and ad.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    await session.delete(ad)
    await session.commit()
    return JSONResponse(status_code=204, content=None)