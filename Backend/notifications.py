from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import List
from Backend.database import get_db
from Backend.middleware import get_current_user
from Backend.models import Notification, User
from Backend.schemas import NotificationResponse, NotificationSend

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = select(Notification).filter(Notification.customer_id == user.customer_id).order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification_data: NotificationSend,
    db: AsyncSession = Depends(get_db),
    # This might be restricted to admin in a real app, but for now we follow the instruction
    user: User = Depends(get_current_user)
):
    notification_id = f"NOTIF-{uuid.uuid4().hex[:10].upper()}"
    new_notif = Notification(
        notification_id=notification_id,
        customer_id=notification_data.customer_id,
        title=notification_data.title,
        message=notification_data.message
    )
    db.add(new_notif)
    await db.commit()
    await db.refresh(new_notif)
    return new_notif

@router.patch("/{id}/read")
async def mark_as_read(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = select(Notification).filter(
        Notification.notification_id == id,
        Notification.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return {"message": "Notification marked as read", "is_read": notification.is_read}

@router.delete("/{id}")
async def delete_notification(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = select(Notification).filter(
        Notification.notification_id == id,
        Notification.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notification)
    await db.commit()
    return {"message": "Notification deleted successfully"}
