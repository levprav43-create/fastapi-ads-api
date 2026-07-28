from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime

from app.database import engine, get_db
from app.models import Base, Advertisement
from app.schemas import AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse

app = FastAPI(title="FastAPI Ads API", version="1.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/advertisement", response_model=AdvertisementResponse, status_code=201)
async def create_advertisement(ad: AdvertisementCreate, db: AsyncSession = Depends(get_db)):
    db_ad = Advertisement(
        title=ad.title,
        description=ad.description,
        price=ad.price,
        author=ad.author,
        created_at=datetime.utcnow()
    )
    db.add(db_ad)
    await db.commit()
    await db.refresh(db_ad)
    return db_ad

@app.get("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
async def get_advertisement(advertisement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Advertisement).where(Advertisement.id == advertisement_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return ad

@app.patch("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
async def update_advertisement(
    advertisement_id: int,
    ad_update: AdvertisementUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Advertisement).where(Advertisement.id == advertisement_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    
    update_data = ad_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ad, field, value)
    
    await db.commit()
    await db.refresh(ad)
    return ad

@app.delete("/advertisement/{advertisement_id}")
async def delete_advertisement(advertisement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Advertisement).where(Advertisement.id == advertisement_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    
    await db.delete(ad)
    await db.commit()
    return {"message": f"Объявление {advertisement_id} удалено"}

@app.get("/advertisement", response_model=list[AdvertisementResponse])
async def search_advertisements(
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Advertisement)
    conditions = []
    
    if title:
        conditions.append(Advertisement.title.ilike(f"%{title}%"))
    if author:
        conditions.append(Advertisement.author.ilike(f"%{author}%"))
    if min_price is not None:
        conditions.append(Advertisement.price >= min_price)
    if max_price is not None:
        conditions.append(Advertisement.price <= max_price)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    return result.scalars().all()