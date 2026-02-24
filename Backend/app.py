# Libraries
import uvicorn
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, APIRouter, HTTPException, status, Body, Request
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os
import uuid
import logging
import random
from decimal import Decimal
import json
from svix.webhooks import Webhook
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, date

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Backend.database import engine, Base, SessionLocal, get_db
from Backend.models import Complaint, Account, Transaction, Customer, User, UserSettings
from Backend.middleware import get_current_user
from app.agents.dispatcher_agent import DispatcherAgent
from app.agents.sentinel_agent import SentinelAgent
from Backend.api import router as auth_router
from Backend.email import send_complaint_confirmation_email
from app.settings import RESEND_WEBHOOK_SECRET
from app.utils.schemas import DispatcherQuery, SentinelQuery, ComplaintQuery
from Backend.schemas import (
    TransactionRequest,
    CustomerCreate,
    ProfileUpdate,
    PreferencesUpdate,
    SettingsResponse,
    UserResponse,
    FullUserResponse,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # print("Starting up: Creating database tables...")
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield

    print("Shutting down: Disposing database engine...")
    await engine.dispose()


app = FastAPI(title="Sentinel Bank API", version="1.0.0", lifespan=lifespan)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/")
def home():
    return {"Message": "Welcome to the Bank System AI Assistant"}


# --- User Profile Endpoints ---

profile_router = APIRouter(tags=["User Profile"])


@profile_router.get("/users/me", response_model=FullUserResponse)
async def get_me(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    # Fetch customer and account details
    stmt = select(Customer).filter(Customer.customer_id == current_user.customer_id)
    result = await db.execute(stmt)
    customer = result.scalars().first()

    stmt_accounts = select(Account).filter(
        Account.customer_id == current_user.customer_id
    )
    result_accounts = await db.execute(stmt_accounts)
    accounts = result_accounts.scalars().all()

    account_list = []
    for acc in accounts:
        account_list.append(
            {
                "account_id": acc.account_id,
                "account_number": acc.account_number,
                "account_type": acc.account_type,
                "balance": float(acc.current_balance),
                "status": acc.status,
            }
        )

    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "customer_details": (
            {
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "full_name": customer.full_name,
                "phone_number": customer.phone_number,
                "kyc_status": "Verified",  # Mocked for now
            }
            if customer
            else None
        ),
        "account_details": account_list,
    }


@profile_router.patch("/users/update-profile")
async def update_profile(
    update_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.customer_id:
        raise HTTPException(status_code=400, detail="No linked customer profile found")

    stmt = select(Customer).filter(Customer.customer_id == current_user.customer_id)
    result = await db.execute(stmt)
    customer = result.scalars().first()

    if update_data.first_name:
        customer.first_name = update_data.first_name
    if update_data.last_name:
        customer.last_name = update_data.last_name
    if update_data.phone_number:
        customer.phone_number = update_data.phone_number
    if update_data.telco_provider:
        customer.telco_provider = update_data.telco_provider

    # Update full name if names changed
    customer.full_name = f"{customer.first_name} {customer.last_name}"

    await db.commit()
    return {"message": "Profile updated successfully"}


@profile_router.get("/users/settings", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = select(UserSettings).filter(UserSettings.user_id == current_user.user_id)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        # Create default if missing
        settings = UserSettings(user_id=current_user.user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@profile_router.patch("/users/update-preferences")
async def update_preferences(
    prefs: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserSettings).filter(UserSettings.user_id == current_user.user_id)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        settings = UserSettings(user_id=current_user.user_id)
        db.add(settings)

    if prefs.theme:
        settings.theme = prefs.theme
    if prefs.language:
        settings.language = prefs.language
    if prefs.notify_transactions is not None:
        settings.notify_transactions = prefs.notify_transactions
    if prefs.notify_promotions is not None:
        settings.notify_promotions = prefs.notify_promotions

    await db.commit()
    return {"message": "Preferences updated successfully"}


# Admin Endpoints
@profile_router.get("/users/{userId}", dependencies=[Depends(get_current_user)])
async def admin_get_user(
    userId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(User).filter(User.user_id == userId)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@profile_router.delete("/users/{userId}")
async def admin_delete_user(
    userId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(User).filter(User.user_id == userId)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False  # Deactivate instead of hard delete
    await db.commit()
    return {"message": f"User {userId} deactivated successfully"}


app.include_router(profile_router)


# --- Webhooks ---

webhook_router = APIRouter(tags=["Webhooks"])


@webhook_router.post("/webhooks/inbound-email")
async def inbound_email_webhook(
    request: Request,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives an inbound email from Resend with signature verification.
    """
    # 1. Get raw body and headers
    payload = await request.body()
    headers = request.headers

    # 2. Verify Signature (Only if Secret is set in .env)
    if RESEND_WEBHOOK_SECRET:
        try:
            wh = Webhook(RESEND_WEBHOOK_SECRET)
            # This validates the 'svix-id', 'svix-timestamp', and 'svix-signature'
            wh.verify(payload, headers)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    # 3. Parse data manually from raw payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON body")

    from_email = data.get("from")
    to_email = data.get("to")
    subject = data.get("subject", "No Subject")
    text = data.get("text", "")

    if not from_email:
        raise HTTPException(status_code=422, detail="Missing 'from' field")

    # 4. Find the user by from_email
    stmt = select(User).filter(User.email == from_email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        # In a real scenario, we might create a guest ticket or ignore
        return {"status": "ignored", "reason": "User not found"}

    # 2. Create a new complaint
    new_complaint_id = f"CMP-MAIL-{uuid.uuid4().hex[:8].upper()}"
    new_complaint = Complaint(
        complaint_id=new_complaint_id,
        customer_id=user.customer_id,
        complaint_timestamp=datetime.now(),
        complaint_status="open",
        complaint_channel="email",
        complaint_text=f"Subject: {subject}\n\n{text}",
        department_name="Pending AI Routing",
    )

    db.add(new_complaint)
    await db.commit()

    # 3. Trigger AI Routing in background
    background_tasks.add_task(
        process_complaint_routing,
        complaint_id=new_complaint_id,
        complaint_text=text,
    )

    return {
        "status": "received",
        "complaint_id": new_complaint_id,
        "message": "Email complaint received and is being routed by AI.",
    }


app.include_router(webhook_router)


# --- Existing Agent Endpoints ---


async def process_complaint_routing(complaint_id: str, complaint_text: str):
    """Background task to route complaints using the AI Agent."""
    async with SessionLocal() as db:
        try:
            agent = DispatcherAgent()
            routing_result = await agent.run(
                input_data={"complaint_text": complaint_text}
            )

            stmt = select(Complaint).filter(Complaint.complaint_id == complaint_id)
            result = await db.execute(stmt)
            complaint = result.scalars().first()

            if complaint:
                complaint.department_code = routing_result.get("department_code")
                complaint.department_name = routing_result.get("department")
                complaint.priority_level = routing_result.get("priority")
                complaint.sentiment = routing_result.get("sentiment")

                await db.commit()
                print(
                    f"Successfully routed complaint {complaint_id} to {complaint.department_name}"
                )

                # 4. Get the user email for confirmation
                user_stmt = select(User).filter(
                    User.customer_id == complaint.customer_id
                )
                user_result = await db.execute(user_stmt)
                user = user_result.scalars().first()

                if user:
                    print(f"📧 Sending auto-reply to {user.email}...")
                    await send_complaint_confirmation_email(
                        to_email=user.email,
                        complaint_id=complaint_id,
                        department=complaint.department_name,
                        priority=complaint.priority_level,
                    )

        except Exception as e:
            print(f"CRITICAL AI ROUTING FAILURE for {complaint_id}: {e}")


@app.post("/make_complaint", tags=["DB_Operations"])
async def make_complaint(
    query: ComplaintQuery,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        stmt = select(Account).filter(
            Account.account_number == query.account_number,
            Account.customer_id == user.customer_id,
        )
        result = await db.execute(stmt)
        account = result.scalars().first()

        if not account:
            raise HTTPException(status_code=403, detail="Unauthorized account access")

        new_complaint_id = f"CMP-{uuid.uuid4().hex[:10].upper()}"
        new_complaint = Complaint(
            complaint_id=new_complaint_id,
            customer_id=user.customer_id,
            linked_transaction_id=query.linked_transaction_id,
            linked_reference=query.linked_reference,
            complaint_timestamp=datetime.now(),
            complaint_status="open",
            complaint_channel=query.complaint_channel,
            complaint_text=query.complaint_text,
            department_name="Pending AI Routing",
        )

        db.add(new_complaint)
        await db.commit()

        background_tasks.add_task(
            process_complaint_routing,
            complaint_id=new_complaint_id,
            complaint_text=query.complaint_text,
        )

        return {
            "message": "Complaint submitted successfully and is being routed.",
            "complaint_id": new_complaint_id,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customers", tags=["DB_Operations"], status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate, db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Customer).filter(
            or_(
                Customer.bvn == customer_data.bvn, Customer.email == customer_data.email
            )
        )
        result = await db.execute(stmt)
        existing_customer = result.scalars().first()

        if existing_customer:
            raise HTTPException(
                status_code=409,
                detail="A customer with this BVN or Email already exists.",
            )

        new_customer_id = f"CUST-{uuid.uuid4().hex[:10].upper()}"
        calculated_full_name = f"{customer_data.first_name} {customer_data.last_name}"
        calculated_age = date.today().year - customer_data.date_of_birth.year

        new_customer = Customer(
            customer_id=new_customer_id,
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            full_name=calculated_full_name,
            gender=customer_data.gender,
            age=calculated_age,
            date_of_birth=customer_data.date_of_birth,
            bvn=customer_data.bvn,
            nin=customer_data.nin,
            phone_number=customer_data.phone_number,
            telco_provider=customer_data.telco_provider,
            email=customer_data.email,
            state_of_origin=customer_data.state_of_origin,
            residential_state=customer_data.residential_state,
            banking_branch=customer_data.banking_branch,
            onboarding_date=date.today(),
        )

        db.add(new_customer)
        new_account = Account(
            account_id=f"ACCT-{uuid.uuid4().hex[:10].upper()}",
            customer_id=new_customer_id,
            account_number=str(random.randint(1000000000, 9999999999)),
            account_type="Savings",
            currency="NGN",
            current_balance=float(random.randint(5, 100) * 1000),
            status="active",
            opened_date=date.today(),
        )
        db.add(new_account)

        await db.commit()
        await db.refresh(new_customer)
        await db.refresh(new_account)

        return {
            "message": "Customer and Bank Account created successfully",
            "customer_id": new_customer.customer_id,
            "account_number": new_account.account_number,
            "starting_balance": new_account.current_balance,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/make_transaction", tags=["Agents"])
async def make_transaction(
    request: TransactionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        stmt = (
            select(Account)
            .filter(
                Account.account_number == request.account_number,
                Account.customer_id == user.customer_id,
            )
            .with_for_update()
        )

        result = await db.execute(stmt)
        account = result.scalars().first()

        if not account:
            raise HTTPException(status_code=403, detail="Unauthorized account access")

        agent = SentinelAgent()
        fraud_result = await agent.run(request.model_dump())
        risk_score = fraud_result.get("risk_score", 0)

        if risk_score > 0.8:
            return {
                "status": "blocked",
                "message": "Transaction flagged as risk",
                "fraud_analysis": fraud_result,
            }

        safe_amount = Decimal(str(request.amount))
        if request.transaction_type == "debit":
            if account.current_balance < safe_amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            new_balance = account.current_balance - safe_amount
        else:
            new_balance = account.current_balance + safe_amount

        transaction = Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            transaction_reference_number=f"REF-{uuid.uuid4().hex[:10].upper()}",
            account_id=account.account_id,
            channel=request.channel,
            amount=safe_amount,
            transaction_type=request.transaction_type,
            transaction_balance=new_balance,
            transaction_status="completed",
            is_fraud_score=int(risk_score * 100),
            transaction_timestamp=datetime.now(),
        )

        account.current_balance = new_balance
        db.add(transaction)
        await db.commit()

        return {
            "status": "approved",
            "transaction_reference": transaction.transaction_reference_number,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
