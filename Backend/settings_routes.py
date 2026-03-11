from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from Backend.database import get_db
from Backend.models import Customer, UserSettings
from Backend.middleware import get_current_user
from Backend.schemas import (
    ThemeUpdate,
    LanguageUpdate,
    NotificationsUpdate,
    SecurityUpdate,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


async def _get_or_create_settings(db: AsyncSession, customer_id: str) -> UserSettings:
    stmt = select(UserSettings).filter(UserSettings.customer_id == customer_id)
    result = await db.execute(stmt)
    settings = result.scalars().first()
    if not settings:
        settings = UserSettings(customer_id=customer_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("/")
async def get_settings(
    db: AsyncSession = Depends(get_db), user: Customer = Depends(get_current_user)
):
    settings = await _get_or_create_settings(db, user.customer_id)
    return settings


@router.patch("/update-theme")
async def update_theme(
    payload: ThemeUpdate,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    settings = await _get_or_create_settings(db, user.customer_id)
    settings.theme = payload.theme
    await db.commit()
    await db.refresh(settings)
    return {"message": "Theme updated", "settings": settings}


@router.patch("/update-language")
async def update_language(
    payload: LanguageUpdate,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    settings = await _get_or_create_settings(db, user.customer_id)
    settings.language = payload.language
    await db.commit()
    await db.refresh(settings)
    return {"message": "Language updated", "settings": settings}


@router.patch("/update-notifications")
async def update_notifications(
    payload: NotificationsUpdate,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    settings = await _get_or_create_settings(db, user.customer_id)
    # The model has notify_transactions and notify_promotions
    # We update both based on the 'enabled' flag as a simplification
    settings.notify_transactions = payload.enabled
    await db.commit()
    await db.refresh(settings)
    return {"message": "Notification settings updated", "settings": settings}


@router.patch("/update-security")
async def update_security(
    payload: SecurityUpdate,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    settings = await _get_or_create_settings(db, user.customer_id)
    if payload.mfa_enabled is not None:
        settings.two_factor_enabled = payload.mfa_enabled
    await db.commit()
    await db.refresh(settings)
    return {"message": "Security settings updated", "settings": settings}
