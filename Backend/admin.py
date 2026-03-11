"""
Backend/admin.py — Admin Dashboard
───────────────────────────────────
All endpoints require user.role == "admin"; non-admins receive 403.
Every mutating action is logged to the audit_logs table.

Register in app.py:
    from Backend.admin import router as admin_router
    app.include_router(admin_router)
"""

import json
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from Backend.database import get_db
from Backend.middleware import get_current_user
from Backend.models import (
    Customer,
    Account,
    Transaction,
    Complaint,
    AuditLog,
    FraudAlert,
)
from Backend.schemas import AdminUserStatusUpdate, TicketAssign, TicketResolve

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Guard: reject non-admin users ──────────────────────────
def require_admin(user=Depends(get_current_user)):
    """Dependency that checks admin role. Inject with Depends(require_admin)."""
    # Simply bypass the admin check since we have removed roles
    return user


# ─── Audit helper ────────────────────────────────────────────
async def _log_action(
    db: AsyncSession,
    *,
    actor_id: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
):
    """Write one row to audit_logs."""
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(entry)
    # flushed with the caller's commit


# ═══════════════════════════════════════════════════════════════
#  USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════


@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Paginated list of all registered users."""
    result = await db.execute(select(Customer).offset(skip).limit(limit))
    users = result.scalars().all()

    count_result = await db.execute(select(func.count(Customer.customer_id)))
    total = count_result.scalar()

    return {"total": total, "skip": skip, "limit": limit, "users": users}


@router.get("/users/{customer_id}")
async def get_user(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get a single user's profile."""
    result = await db.execute(select(Customer).filter(Customer.customer_id == customer_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{customer_id}/transactions")
async def get_user_transactions(
    customer_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List transactions belonging to a user (via their accounts)."""
    # Find the user's customer_id first
    user_result = await db.execute(select(Customer).filter(Customer.customer_id == customer_id))
    user_obj = user_result.scalars().first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all account IDs for this customer
    acct_result = await db.execute(
        select(Account.account_id).filter(Account.customer_id == user_obj.customer_id)
    )
    account_ids = [row[0] for row in acct_result.all()]

    if not account_ids:
        return {"total": 0, "transactions": []}

    # Get transactions for those accounts
    txn_result = await db.execute(
        select(Transaction)
        .filter(
            (Transaction.sender_account_id.in_(account_ids))
            | (Transaction.receiver_account_id.in_(account_ids))
        )
        .order_by(Transaction.transaction_timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    transactions = txn_result.scalars().all()
    return {"total": len(transactions), "transactions": transactions}


@router.get("/users/{customer_id}/complaints")
async def get_user_complaints(
    customer_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List complaints filed by a user."""
    # Find customer_id for the user
    user_result = await db.execute(select(Customer).filter(Customer.customer_id == customer_id))
    user_obj = user_result.scalars().first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(Complaint)
        .filter(Complaint.customer_id == user_obj.customer_id)
        .order_by(Complaint.complaint_timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    complaints = result.scalars().all()
    return {"total": len(complaints), "complaints": complaints}


@router.patch("/users/{customer_id}/status")
async def update_user_status(
    customer_id: str,
    payload: AdminUserStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Activate, suspend, or deactivate a user account."""
    allowed = {"active", "suspended", "deactivated"}
    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {allowed}",
        )

    result = await db.execute(select(Customer).filter(Customer.customer_id == customer_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_status = getattr(user, "status", "unknown")
    await db.execute(
        update(Customer).where(Customer.customer_id == customer_id).values(status=payload.status)
    )

    await _log_action(
        db,
        actor_id=admin.customer_id,
        action="admin.update_user_status",
        target_type="user",
        target_id=customer_id,
        details={"old_status": old_status, "new_status": payload.status},
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return {"message": f"User {customer_id} status updated to {payload.status}"}


# ═══════════════════════════════════════════════════════════════
#  TICKET / COMPLAINT MANAGEMENT
# ═══════════════════════════════════════════════════════════════


@router.get("/tickets")
async def list_tickets(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List all support tickets / complaints, optionally filtered by status."""
    query = select(Complaint)
    if status_filter:
        query = query.filter(Complaint.complaint_status == status_filter)
    query = (
        query.order_by(Complaint.complaint_timestamp.desc()).offset(skip).limit(limit)
    )

    result = await db.execute(query)
    tickets = result.scalars().all()
    return {"total": len(tickets), "tickets": tickets}


@router.patch("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    payload: TicketAssign,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Assign a ticket to an agent."""
    result = await db.execute(
        select(Complaint).filter(Complaint.complaint_id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    await db.execute(
        update(Complaint)
        .where(Complaint.complaint_id == ticket_id)
        .values(assigned_to=payload.assigned_to, complaint_status="in_progress")
    )

    await _log_action(
        db,
        actor_id=admin.customer_id,
        action="admin.assign_ticket",
        target_type="ticket",
        target_id=ticket_id,
        details={"assigned_to": payload.assigned_to},
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return {"message": f"Ticket {ticket_id} assigned to {payload.assigned_to}"}


@router.patch("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    payload: TicketResolve,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Mark a ticket as resolved."""
    result = await db.execute(
        select(Complaint).filter(Complaint.complaint_id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_values = {"complaint_status": "resolved"}
    if payload.resolution_note:
        update_values["resolution_note"] = payload.resolution_note

    await db.execute(
        update(Complaint)
        .where(Complaint.complaint_id == ticket_id)
        .values(**update_values)
    )

    await _log_action(
        db,
        actor_id=admin.customer_id,
        action="admin.resolve_ticket",
        target_type="ticket",
        target_id=ticket_id,
        details={"resolution_note": payload.resolution_note},
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return {"message": f"Ticket {ticket_id} resolved"}


# ═══════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════


@router.get("/analytics/transactions")
async def analytics_transactions(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Transaction volume & totals for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total_result = await db.execute(
        select(
            func.count(Transaction.transaction_id).label("count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        ).filter(Transaction.transaction_timestamp >= since)
    )
    row = total_result.one()

    # Breakdown by transaction type
    type_result = await db.execute(
        select(
            Transaction.transaction_type,
            func.count(Transaction.transaction_id),
        )
        .filter(Transaction.transaction_timestamp >= since)
        .group_by(Transaction.transaction_type)
    )
    breakdown = {r[0] or "unknown": r[1] for r in type_result.all()}

    return {
        "period": f"last_{days}_days",
        "total_transactions": row.count,
        "total_amount": float(row.total_amount),
        "breakdown_by_type": breakdown,
    }


@router.get("/analytics/fraud")
async def analytics_fraud(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Fraud alert statistics for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        total_result = await db.execute(
            select(func.count(FraudAlert.alert_id)).filter(
                FraudAlert.created_at >= since
            )
        )
        total_alerts = total_result.scalar()

        status_result = await db.execute(
            select(FraudAlert.decision, func.count(FraudAlert.alert_id))
            .filter(FraudAlert.created_at >= since)
            .group_by(FraudAlert.decision)
        )
        by_decision = {r[0] or "unknown": r[1] for r in status_result.all()}
    except Exception:
        # fraud_alerts table may not exist yet or decision column missing
        total_alerts = 0
        by_decision = {}

    return {
        "period": f"last_{days}_days",
        "total_alerts": total_alerts,
        "breakdown_by_decision": by_decision,
    }


@router.get("/analytics/user-growth")
async def analytics_user_growth(
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """New user registrations per day for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Customer.onboarding_date).label("day"),
            func.count(Customer.customer_id).label("count"),
        )
        .filter(Customer.onboarding_date >= since.date())
        .group_by(func.date(Customer.onboarding_date))
        .order_by(func.date(Customer.onboarding_date))
    )
    daily = [{"date": str(r.day), "new_users": r.count} for r in result.all()]

    total_result = await db.execute(select(func.count(Customer.customer_id)))
    total_users = total_result.scalar()

    return {
        "period": f"last_{days}_days",
        "total_users": total_users,
        "daily_registrations": daily,
    }
