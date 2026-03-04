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
from datetime import datetime

from Backend.database import get_db
from Backend.middleware import get_current_user
from Backend.models import Account, ServiceTransaction, Transaction
from Backend.schemas import (
    AirtimePurchaseRequest,
    DataPurchaseRequest,
    BillPayRequest,
    ServiceTransactionResponse,
    ProviderOut,
    BillCategoryOut,
    InternalTransferRequest,
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
        raise HTTPException(
            status_code=400, detail="The selected account was not found."
        )
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


# ═══════════════════════════════════════════════════════════════
#  INTERNAL TRANSFERS
# ═══════════════════════════════════════════════════════════════


@router.post("/internal-transfer")
async def internal_transfer(
    payload: InternalTransferRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Perform a transfer between two accounts within Sentinel Bank.
    """
    # 1. Verify source account
    stmt_src = select(Account).filter(
        Account.account_number == payload.from_account_number
    )
    res_src = await db.execute(stmt_src)
    src_acc = res_src.scalars().first()

    if not src_acc:
        raise HTTPException(status_code=400, detail="Source account not found.")

    if src_acc.customer_id != user.customer_id:
        raise HTTPException(
            status_code=403, detail="You do not have permission to debit this account."
        )

    # 2. Check balance
    if float(src_acc.current_balance) < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance.")

    # 3. Verify recipient account
    stmt_dest = select(Account).filter(
        Account.account_number == payload.to_account_number
    )
    res_dest = await db.execute(stmt_dest)
    dest_acc = res_dest.scalars().first()

    if not dest_acc:
        raise HTTPException(
            status_code=400, detail="The recipient account number does not exist."
        )

    if src_acc.account_id == dest_acc.account_id:
        raise HTTPException(
            status_code=400, detail="Source and destination accounts must be different."
        )

    # 4. Perform atomic transfer
    try:
        # Update Balances
        src_acc.current_balance = float(src_acc.current_balance) - payload.amount
        dest_acc.current_balance = float(dest_acc.current_balance) + payload.amount

        # Record Transaction for Sender
        sender_txn = Transaction(
            transaction_id=uuid.uuid4().hex,
            transaction_reference_number=f"TRF-OUT-{uuid.uuid4().hex[:10].upper()}",
            account_id=src_acc.account_id,
            channel="web",
            transaction_type="debit",
            amount=payload.amount,
            narration=payload.narration or f"Transfer to {dest_acc.account_number}",
            transaction_status="completed",
            transaction_timestamp=datetime.now(),
            transaction_balance=src_acc.current_balance,
        )

        # Record Transaction for Recipient
        receiver_txn = Transaction(
            transaction_id=uuid.uuid4().hex,
            transaction_reference_number=f"TRF-IN-{uuid.uuid4().hex[:10].upper()}",
            account_id=dest_acc.account_id,
            channel="web",
            transaction_type="credit",
            amount=payload.amount,
            narration=payload.narration or f"Transfer from {src_acc.account_number}",
            transaction_status="completed",
            transaction_timestamp=datetime.now(),
            transaction_balance=dest_acc.current_balance,
        )

        db.add(sender_txn)
        db.add(receiver_txn)

        await db.commit()

        return {
            "message": "Transfer successfully completed!",
            "reference": sender_txn.transaction_reference_number,
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred during transfer: {str(e)}"
        )
