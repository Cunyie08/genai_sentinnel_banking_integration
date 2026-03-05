import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from Backend.database import get_db
from Backend.models import User, Notification
from Backend.middleware import get_current_user
from Backend.schemas import NotificationResponse, NotificationSend

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    stmt = (
        select(Notification)
        .filter(Notification.user_id == user.user_id)
        .order_by(Notification.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/send", status_code=status.HTTP_201_CREATED)
async def send_notification_endpoint(
    payload: NotificationSend,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    # Only admins should be able to send manual notifications (simplified for now)
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Find user_id from customer_id (since payload has customer_id)
    from Backend.models import User as UserTable

    user_stmt = select(UserTable).filter(UserTable.customer_id == payload.customer_id)
    user_result = await db.execute(user_stmt)
    target_user = user_result.scalars().first()

    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    notif_id = f"NOTIF-{uuid.uuid4().hex[:10].upper()}"
    new_notif = Notification(
        notification_id=notif_id,
        user_id=target_user.user_id,
        title=payload.title,
        message=payload.message,
        notification_type="in-app",
        is_read=False,
    )
    db.add(new_notif)
    await db.commit()
    return {"message": "Notification sent successfully", "id": notif_id}


@router.patch("/{id}/read")
async def mark_as_read(
    id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    stmt = select(Notification).filter(
        Notification.notification_id == id, Notification.user_id == user.user_id
    )
    result = await db.execute(stmt)
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.commit()
    return {"message": "Notification marked as read"}


@router.delete("/{id}")
async def delete_notification(
    id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    stmt = select(Notification).filter(
        Notification.notification_id == id, Notification.user_id == user.user_id
    )
    result = await db.execute(stmt)
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notification)
    await db.commit()
    return {"message": "Notification deleted successfully"}
