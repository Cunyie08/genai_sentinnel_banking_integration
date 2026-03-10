import uuid
import random
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from Backend.database import get_db
from Backend.models import Account, Card, Customer
from Backend.middleware import get_current_user
from Backend.schemas import CardRequest, CardResponse, CardLimitUpdate

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.post(
    "/request", response_model=CardResponse, status_code=status.HTTP_201_CREATED
)
async def request_card(
    request: CardRequest,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    # Verify account belongs to user
    stmt = select(Account).filter(
        Account.account_id == request.account_id,
        Account.customer_id == user.customer_id,
    )
    result = await db.execute(stmt)
    account = result.scalars().first()

    if not account:
        raise HTTPException(status_code=403, detail="Unauthorized account access")

    card_id = f"CARD-{uuid.uuid4().hex[:10].upper()}"
    card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])
    expiry_date = "12/29"  # Static expiry for demo
    cvv = "".join([str(random.randint(0, 9)) for _ in range(3)])

    new_card = Card(
        card_id=card_id,
        account_id=request.account_id,
        card_type=request.card_type,
        card_number=card_number,
        expiry_date=expiry_date,
        cvv=cvv,
        status="active",
        daily_limit=100000.00,
    )
    db.add(new_card)
    await db.commit()
    await db.refresh(new_card)
    return new_card


@router.get("/", response_model=List[CardResponse])
async def list_cards(
    db: AsyncSession = Depends(get_db), user: Customer = Depends(get_current_user)
):
    # Find all accounts linked to the user's customer record
    acc_stmt = select(Account.account_id).filter(
        Account.customer_id == user.customer_id
    )
    acc_result = await db.execute(acc_stmt)
    account_ids = [row for row in acc_result.scalars().all()]

    if not account_ids:
        return []

    # Find all cards linked to these accounts
    stmt = select(Card).filter(Card.account_id.in_(account_ids))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{cardId}/freeze")
async def freeze_card(
    cardId: str,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    # Join with Account to verify ownership
    stmt = (
        select(Card)
        .join(Account)
        .filter(Card.card_id == cardId, Account.customer_id == user.customer_id)
    )
    result = await db.execute(stmt)
    card = result.scalars().first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.status = "frozen"
    await db.commit()
    await db.refresh(card)
    return {"message": "Card frozen successfully", "status": card.status}


@router.patch("/{cardId}/activate")
async def activate_card(
    cardId: str,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    stmt = (
        select(Card)
        .join(Account)
        .filter(Card.card_id == cardId, Account.customer_id == user.customer_id)
    )
    result = await db.execute(stmt)
    card = result.scalars().first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.status = "active"
    await db.commit()
    await db.refresh(card)
    return {"message": "Card activated successfully", "status": card.status}


@router.get("/{cardId}/details", response_model=CardResponse)
async def get_card_details(
    cardId: str,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    stmt = (
        select(Card)
        .join(Account)
        .filter(Card.card_id == cardId, Account.customer_id == user.customer_id)
    )
    result = await db.execute(stmt)
    card = result.scalars().first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return card


@router.post("/{cardId}/set-limit")
async def set_card_limit(
    cardId: str,
    limit_data: CardLimitUpdate,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
):
    stmt = (
        select(Card)
        .join(Account)
        .filter(Card.card_id == cardId, Account.customer_id == user.customer_id)
    )
    result = await db.execute(stmt)
    card = result.scalars().first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.daily_limit = limit_data.daily_limit
    await db.commit()
    await db.refresh(card)
    return {
        "message": "Card limit updated successfully",
        "daily_limit": float(card.daily_limit),
    }
