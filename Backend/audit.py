"""
Backend/audit.py — Audit & Logging
───────────────────────────────────
Read-only endpoints to query the audit_logs table.
All endpoints require admin role.

Register in app.py:
    from Backend.audit import router as audit_router
    app.include_router(audit_router)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from Backend.database import get_db
from Backend.middleware import get_current_user
from Backend.models import Customer, AuditLog
from Backend.schemas import AuditLogOut

router = APIRouter(prefix="/audit", tags=["Audit"])


# ─── Guard: reject non-admin users ──────────────────────────
def require_admin(user=Depends(get_current_user)):
    if getattr(user, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# ═══════════════════════════════════════════════════════════════
#  AUDIT LOG QUERIES
# ═══════════════════════════════════════════════════════════════


@router.get("/logs", response_model=list[AuditLogOut])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None, description="Filter by action name"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Paginated list of all audit log entries, newest first."""
    query = select(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/user/{customer_id}", response_model=list[AuditLogOut])
async def get_audit_logs_by_user(
    customer_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """All audit entries where the actor OR target is the given user."""
    result = await db.execute(
        select(AuditLog)
        .filter(
            (AuditLog.actor_id == customer_id)
            | ((AuditLog.target_type == "user") & (AuditLog.target_id == customer_id))
        )
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/transaction/{transaction_id}", response_model=list[AuditLogOut])
async def get_audit_logs_by_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """All audit entries related to a specific transaction."""
    result = await db.execute(
        select(AuditLog)
        .filter(
            (AuditLog.target_type == "transaction")
            & (AuditLog.target_id == transaction_id)
        )
        .order_by(AuditLog.created_at.desc())
    )
    return result.scalars().all()
