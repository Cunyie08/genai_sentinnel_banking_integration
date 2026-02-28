"""
Backend/services.py — Quick Services
─────────────────────────────────────
Endpoints for airtime top-up, data bundles, and bill payments.
Register in app.py:
    from Backend.services import router as services_router
    app.include_router(services_router)
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from Backend.database import get_db
from Backend.middleware import get_current_user
from Backend.models import Account, ServiceTransaction
from Backend.schemas import (
    AirtimePurchaseRequest,
    DataPurchaseRequest,
    BillPayRequest,
    ServiceTransactionResponse,
    ProviderOut,
    BillCategoryOut,
)

router = APIRouter(prefix="/services", tags=["Quick Services"])


# ─── Static provider / category catalogues ──────────────────
AIRTIME_PROVIDERS = [
    {"name": "MTN", "code": "mtn"},
    {"name": "Airtel", "code": "airtel"},
    {"name": "Glo", "code": "glo"},
    {"name": "9mobile", "code": "9mobile"},
]

DATA_PROVIDERS = [
    {"name": "MTN", "code": "mtn"},
    {"name": "Airtel", "code": "airtel"},
    {"name": "Glo", "code": "glo"},
    {"name": "9mobile", "code": "9mobile"},
]

BILL_CATEGORIES = [
    {"name": "Electricity", "code": "electricity"},
    {"name": "Water", "code": "water"},
    {"name": "Internet", "code": "internet"},
    {"name": "Cable TV", "code": "cable_tv"},
    {"name": "Waste", "code": "waste"},
]

BILL_PROVIDERS = [
    {"name": "IKEDC", "code": "ikedc"},
    {"name": "EKEDC", "code": "ekedc"},
    {"name": "AEDC", "code": "aedc"},
    {"name": "DSTV", "code": "dstv"},
    {"name": "GOtv", "code": "gotv"},
    {"name": "Startimes", "code": "startimes"},
    {"name": "Lagos Water", "code": "lagos_water"},
    {"name": "Spectranet", "code": "spectranet"},
    {"name": "Smile", "code": "smile"},
]


# ─── Helpers ─────────────────────────────────────────────────
async def _verify_account_ownership(
    db: AsyncSession, account_id: str, user
) -> "Account":
    """Return the account if it belongs to the current user, else 403/404."""
    result = await db.execute(select(Account).filter(Account.account_id == account_id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.customer_id != user.customer_id:
        raise HTTPException(status_code=403, detail="Account does not belong to you")
    return account


async def _debit_account(db: AsyncSession, account: "Account", amount: float):
    """Deduct amount from account current_balance; raises 400 if insufficient."""
    if float(account.current_balance) < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    await db.execute(
        update(Account)
        .where(Account.account_id == account.account_id)
        .values(current_balance=Account.current_balance - amount)
    )


# ═══════════════════════════════════════════════════════════════
#  AIRTIME
# ═══════════════════════════════════════════════════════════════


@router.get("/airtime/providers", response_model=list[ProviderOut])
async def get_airtime_providers(user=Depends(get_current_user)):
    """List available airtime providers."""
    return AIRTIME_PROVIDERS


@router.post("/airtime/purchase", response_model=ServiceTransactionResponse)
async def purchase_airtime(
    payload: AirtimePurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Purchase airtime for a phone number."""
    account = await _verify_account_ownership(db, payload.account_id, user)
    await _debit_account(db, account, payload.amount)

    txn = ServiceTransaction(
        service_tx_id=f"STX-{uuid.uuid4().hex[:12].upper()}",
        user_id=user.user_id,
        account_id=payload.account_id,
        service_type="airtime",
        provider=payload.provider,
        phone_number=payload.phone_number,
        amount=payload.amount,
        reference=f"AIR-{uuid.uuid4().hex[:10].upper()}",
        status="completed",
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn


# ═══════════════════════════════════════════════════════════════
#  DATA BUNDLES
# ═══════════════════════════════════════════════════════════════


@router.get("/data/providers", response_model=list[ProviderOut])
async def get_data_providers(user=Depends(get_current_user)):
    """List available data-bundle providers."""
    return DATA_PROVIDERS


@router.post("/data/purchase", response_model=ServiceTransactionResponse)
async def purchase_data(
    payload: DataPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Purchase a data bundle."""
    account = await _verify_account_ownership(db, payload.account_id, user)
    await _debit_account(db, account, payload.amount)

    txn = ServiceTransaction(
        service_tx_id=f"STX-{uuid.uuid4().hex[:12].upper()}",
        user_id=user.user_id,
        account_id=payload.account_id,
        service_type="data",
        provider=payload.provider,
        phone_number=payload.phone_number,
        data_plan=payload.data_plan,
        amount=payload.amount,
        reference=f"DAT-{uuid.uuid4().hex[:10].upper()}",
        status="completed",
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn


# ═══════════════════════════════════════════════════════════════
#  BILLS
# ═══════════════════════════════════════════════════════════════


@router.get("/bills/categories", response_model=list[BillCategoryOut])
async def get_bill_categories(user=Depends(get_current_user)):
    """List available bill categories."""
    return BILL_CATEGORIES


@router.get("/bills/providers", response_model=list[ProviderOut])
async def get_bill_providers(user=Depends(get_current_user)):
    """List available bill-payment providers."""
    return BILL_PROVIDERS


@router.post("/bills/pay", response_model=ServiceTransactionResponse)
async def pay_bill(
    payload: BillPayRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Pay a bill (electricity, water, cable TV, etc.)."""
    account = await _verify_account_ownership(db, payload.account_id, user)
    await _debit_account(db, account, payload.amount)

    txn = ServiceTransaction(
        service_tx_id=f"STX-{uuid.uuid4().hex[:12].upper()}",
        user_id=user.user_id,
        account_id=payload.account_id,
        service_type="bills",
        provider=payload.provider,
        category=payload.category,
        bill_account_number=payload.bill_account_number,
        amount=payload.amount,
        reference=f"BIL-{uuid.uuid4().hex[:10].upper()}",
        status="completed",
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn
