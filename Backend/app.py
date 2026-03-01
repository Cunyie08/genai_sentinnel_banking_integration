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
from app.agents.trajectory_agent import TrajectoryAgent
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository
from app.rag.rag_system.rag_querys import create_engine
from app.utils.llm_client import LLMClient
from openai import AsyncOpenAI
from google import genai
from Backend.api import router as auth_router
from Backend.services import router as services_router
from Backend.admin import router as admin_router
from Backend.audit import router as audit_router
from Backend.cards import router as cards_router
from Backend.notifications import router as notifications_router
from Backend.settings_routes import router as settings_router
from Backend.email import send_complaint_confirmation_email
from app.settings import RESEND_WEBHOOK_SECRET, OPENAI_API_KEY, GEMINI_API_KEY
from Backend.schemas import (
    TransactionRequest,
    CustomerCreate,
    ProfileUpdate,
    PreferencesUpdate,
    SettingsResponse,
    UserResponse,
    FullUserResponse,
    AccountResponse,
    ReportFailedRequest,
    InternalTransferRequest,
    RoutingResponse,
    FraudResponse
)

class ComplaintQuery(BaseModel):
    account_number: str
    complaint_channel: str
    complaint_text: str
    linked_transaction_id: Optional[str] = None
    linked_reference: Optional[str] = None

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
app.include_router(services_router)
app.include_router(admin_router)
app.include_router(audit_router)
app.include_router(cards_router)
app.include_router(notifications_router)
app.include_router(settings_router)


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


async def process_complaint_routing(complaint_id: str, complaint_text: str):
    """Background task to route complaints using the AI Agent."""
    async with SessionLocal() as db:
        try:
            # Initialize required components
            dataset_loader = DatasetLoader()
            await dataset_loader.load()
            repo = BankRepository(dataset_loader)
            rag_engine = await create_engine()
            openai_llm = LLMClient(
                client=AsyncOpenAI(api_key=OPENAI_API_KEY),
                model_name="gpt-4o",
                response_schema=RoutingResponse
            )
            gemini_llm = LLMClient(
                client=genai.Client(api_key=GEMINI_API_KEY),
                model_name="gemini-2.5-flash",
                response_schema=RoutingResponse
            )

            agent = DispatcherAgent(
                repo=repo,
                rag_engine=rag_engine,
                openai_llm=openai_llm,
                gemini_llm=gemini_llm
            )
            routing_result = await agent.run(
                payload={"complaint_id": complaint_id}
            )

            stmt = select(Complaint).filter(Complaint.complaint_id == complaint_id)
            result = await db.execute(stmt)
            complaint = result.scalars().first()

            if complaint:
                complaint.department_code = routing_result.get("department_code")
                complaint.department_name = routing_result.get("department_name")
                complaint.priority_level = routing_result.get("priority_level")
                complaint.sentiment = routing_result.get("sentiment")

                await db.commit()
                print(
                    f"Successfully routed complaint {complaint_id} to {complaint.department_name}"
                )

                user_stmt = select(User).filter(
                    User.customer_id == complaint.customer_id
                )
                user_result = await db.execute(user_stmt)
                user = user_result.scalars().first()

                if user:
                    print(f"Sending auto-reply to {user.email}...")
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
            linked_transaction_id=query.linked_transaction_id if query.linked_transaction_id and query.linked_transaction_id != "string" else None,
            linked_reference=query.linked_reference if query.linked_reference and query.linked_reference != "string" else None,
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

        # Initialize required components
        dataset_loader = DatasetLoader()
        await dataset_loader.load()
        repo = BankRepository(dataset_loader)
        rag_engine = await create_engine()
        openai_llm = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=FraudResponse
        )
        gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=FraudResponse
        )

        agent = SentinelAgent(
            repo=repo,
            rag_engine=rag_engine,
            openai_llm=openai_llm,
            gemini_llm=gemini_llm
        )
        
        # Build payload with mock transaction_id for initial scoring
        payload = request.model_dump()
        payload["transaction_id"] = f"TXN-{uuid.uuid4().hex[:10].upper()}"

        fraud_result = await agent.run(payload=payload)
        risk_score = fraud_result.get("total_risk_score", 0)

        if risk_score > 80:
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
            counterparty_bank=request.counterparty_bank,
            amount=safe_amount,
            transaction_type=request.transaction_type,
            transaction_balance=new_balance,
            transaction_status="completed",
            is_fraud_score=int(risk_score),
            transaction_timestamp=datetime.now(),
        )

        account.current_balance = new_balance
        db.add(transaction)
        await db.commit()

        return {
            "status": "approved",
            "transaction_reference": transaction.transaction_reference_number,
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/trajectory/popup_recommendations", tags=["Agents"])
async def get_trajectory_popup(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_loader = DatasetLoader()
        await dataset_loader.load()
        repo = BankRepository(dataset_loader)
        rag_engine = await create_engine()
        openai_llm = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=dict
        )
        gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=dict
        )
        agent = TrajectoryAgent(
            repo=repo,
            rag_engine=rag_engine,
            openai_llm=openai_llm,
            gemini_llm=gemini_llm
        )

        # Force fetch the user from DB to ensure customer_id is mapped just in case the JWT middleware detached it
        stmt = select(User).filter(User.email == user.email)
        res = await db.execute(stmt)
        active_user = res.scalars().first()
        
        customer_id = active_user.customer_id if active_user else user.customer_id
        if not customer_id:
            raise HTTPException(status_code=400, detail="Authenticated user is not linked to a customer profile.")

        payload = {"customer_id": customer_id}
        recommendation_result = await agent.run(payload=payload)

        return {
            "status": "success",
            "recommendations": recommendation_result
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from Backend.email import send_auth_email

@app.post("/trajectory/email_recommendations", tags=["Agents"])
async def post_trajectory_email(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dataset_loader = DatasetLoader()
        await dataset_loader.load()
        repo = BankRepository(dataset_loader)
        rag_engine = await create_engine()
        openai_llm = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=dict
        )
        gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=dict
        )
        agent = TrajectoryAgent(
            repo=repo,
            rag_engine=rag_engine,
            openai_llm=openai_llm,
            gemini_llm=gemini_llm
        )

        # Force fetch the user from DB to ensure customer_id is mapped just in case the JWT middleware detached it
        stmt = select(User).filter(User.email == user.email)
        res = await db.execute(stmt)
        active_user = res.scalars().first()
        
        customer_id = active_user.customer_id if active_user else user.customer_id
        if not customer_id:
            raise HTTPException(status_code=400, detail="Authenticated user is not linked to a customer profile.")

        payload = {"customer_id": customer_id}
        recommendation_result = await agent.run(payload=payload)
        
        # If there's a primary recommendation, send it via email
        primary_product = recommendation_result.get("primary_product")
        if primary_product and primary_product != "None":
            # Format appealing HTML email
            email_html = f"""
            <h2>Special Offer Just for You!</h2>
            <p>Based on your recent activity, we think you'd love our <strong>{primary_product}</strong>.</p>
            <p><strong>Benefits:</strong> {recommendation_result.get('reasoning', 'Tailored to your financial journey.')}</p>
            <p>Log in to your Sentinel Banking app to claim this offer.</p>
            """
            
            # Send the email 
            await send_auth_email(
                to_email=user.email,
                subject="Your Exclusive Sentinel Bank Recommendation",
                html_content=email_html
            )
            
            return {
                "status": "success",
                "message": "Recommendation email sent successfully.",
                "primary_product": primary_product
            }
        else:
             return {
                "status": "success",
                "message": "No specific product recommended to email at this time."
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accounts", tags=["Accounts"], response_model=List[AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    stmt = select(Account).filter(Account.customer_id == user.customer_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/accounts/{accountNumber}", tags=["Accounts"], response_model=AccountResponse)
async def get_account_details(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Account).filter(
        Account.account_number == accountNumber, Account.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@app.get("/accounts/{accountNumber}/balance", tags=["Accounts"])
async def get_account_balance(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Account).filter(
        Account.account_number == accountNumber, Account.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_number": accountNumber, "current_balance": float(account.current_balance)}


@app.get("/accounts/{accountNumber}/status", tags=["Accounts"])
async def get_account_status(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Account).filter(
        Account.account_number == accountNumber, Account.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_number": accountNumber, "status": account.account_status}


@app.patch("/accounts/{accountNumber}/freeze", tags=["Accounts"])
async def freeze_account(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Account).filter(
        Account.account_number == accountNumber, Account.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.account_status = "frozen"
    await db.commit()
    return {"message": "Account frozen successfully", "status": account.account_status}


@app.patch("/accounts/{accountNumber}/activate", tags=["Accounts"])
async def activate_account(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Account).filter(
        Account.account_number == accountNumber, Account.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.account_status = "active"
    await db.commit()
    return {
        "message": "Account activated successfully",
        "status": account.account_status,
    }


@app.get("/transactions", tags=["Transactions"])
async def list_transactions(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    # Find all accounts linked to the user's customer record
    acc_stmt = select(Account.account_id).filter(
        Account.customer_id == user.customer_id
    )
    acc_result = await db.execute(acc_stmt)
    account_ids = acc_result.scalars().all()

    if not account_ids:
        return []

    stmt = (
        select(Transaction)
        .filter(Transaction.account_id.in_(account_ids))
        .order_by(Transaction.transaction_timestamp.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/transactions/{transactionId}", tags=["Transactions"])
async def get_transaction_details(
    transactionId: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Join with Account to verify ownership
    stmt = (
        select(Transaction)
        .join(Account)
        .filter(
            Transaction.transaction_id == transactionId,
            Account.customer_id == user.customer_id,
        )
    )
    result = await db.execute(stmt)
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@app.get("/transactions/account/{accountNumber}", tags=["Transactions"])
async def list_transactions_for_account(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Verify account ownership
    acc_stmt = select(Account).filter(
        Account.account_number == accountNumber, Account.customer_id == user.customer_id
    )
    acc_result = await db.execute(acc_stmt)
    account = acc_result.scalars().first()
    if not account:
        raise HTTPException(status_code=403, detail="Unauthorized account access")

    stmt = (
        select(Transaction)
        .filter(Transaction.account_id == account.account_id)
        .order_by(Transaction.transaction_timestamp.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/transactions/filter", tags=["Transactions"])
async def filter_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    transaction_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Find all accounts linked to the user's customer record
    acc_stmt = select(Account.account_id).filter(
        Account.customer_id == user.customer_id
    )
    acc_result = await db.execute(acc_stmt)
    account_ids = acc_result.scalars().all()

    if not account_ids:
        return []

    stmt = select(Transaction).filter(Transaction.account_id.in_(account_ids))

    if start_date:
        stmt = stmt.filter(Transaction.transaction_timestamp >= start_date)
    if end_date:
        stmt = stmt.filter(Transaction.transaction_timestamp <= end_date)
    if min_amount:
        stmt = stmt.filter(Transaction.amount >= min_amount)
    if max_amount:
        stmt = stmt.filter(Transaction.amount <= max_amount)
    if transaction_type:
        stmt = stmt.filter(Transaction.transaction_type == transaction_type)

    stmt = stmt.order_by(Transaction.transaction_timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/transactions/{transactionId}/status", tags=["Transactions"])
async def get_transaction_status(
    transactionId: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(Transaction)
        .join(Account)
        .filter(
            Transaction.transaction_id == transactionId,
            Account.customer_id == user.customer_id,
        )
    )
    result = await db.execute(stmt)
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "transaction_id": transaction.transaction_id,
        "transaction_status": transaction.transaction_status,
        "failure_reason": transaction.failure_reason,
    }


@app.post("/transactions/report-failed", tags=["Transactions"])
async def report_failed_transaction(
    request: ReportFailedRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(Transaction)
        .join(Account)
        .filter(
            Transaction.transaction_id == request.transaction_id,
            Account.customer_id == user.customer_id,
        )
    )
    result = await db.execute(stmt)
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.transaction_status = "failed"
    transaction.failure_reason = request.reason

    await db.commit()
    return {"message": "Transaction reported as failed and status updated"}


@app.post("/transactions/internal-transfer", tags=["Transactions"])
async def internal_transfer(
    request: InternalTransferRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Verify sender account belongs to user and is locked for update
    from_stmt = (
        select(Account)
        .filter(
            Account.account_number == request.from_account_number,
            Account.customer_id == user.customer_id,
        )
        .with_for_update()
    )
    from_result = await db.execute(from_stmt)
    from_account = from_result.scalars().first()

    if not from_account:
        raise HTTPException(
            status_code=403, detail="Unauthorized access to sender account"
        )

    # Verify receiver account exists and lock it
    to_stmt = (
        select(Account)
        .filter(Account.account_number == request.to_account_number)
        .with_for_update()
    )
    to_result = await db.execute(to_stmt)
    to_account = to_result.scalars().first()

    if not to_account:
        raise HTTPException(status_code=404, detail="Receiver account not found")

    if from_account.account_id == to_account.account_id:
        raise HTTPException(
            status_code=400, detail="Cannot transfer to the same account"
        )

    amount = Decimal(str(request.amount))
    if from_account.current_balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Initialize SentinelAgent for Fraud Assessment
    dataset_loader = DatasetLoader()
    await dataset_loader.load()
    repo = BankRepository(dataset_loader)
    rag_engine = await create_engine()
    openai_llm = LLMClient(
        client=AsyncOpenAI(api_key=OPENAI_API_KEY),
        model_name="gpt-4o",
        response_schema=FraudResponse
    )
    gemini_llm = LLMClient(
        client=genai.Client(api_key=GEMINI_API_KEY),
        model_name="gemini-2.5-flash",
        response_schema=FraudResponse
    )

    agent = SentinelAgent(
        repo=repo,
        rag_engine=rag_engine,
        openai_llm=openai_llm,
        gemini_llm=gemini_llm
    )
    
    # Build a simulated payload for the Sentinel Agent
    sentinel_payload = {
        "transaction_id": f"TXN-{uuid.uuid4().hex[:10].upper()}",
        "account_number": request.from_account_number,
        "amount": float(amount),
        "transaction_type": "debit",
        "channel": "in-app",
        "counterparty_bank": "Sentinel",
        "narration": request.narration or "Internal Transfer"
    }

    fraud_result = await agent.run(payload=sentinel_payload)
    risk_score = fraud_result.get("risk_score", 0)

    if risk_score > 0.8:
        return {
            "status": "blocked",
            "message": "Internal transfer flagged as risk",
            "fraud_analysis": fraud_result,
        }


    # Process transfer
    from_new_balance = from_account.current_balance - amount
    to_new_balance = to_account.current_balance + amount

    from_account.current_balance = from_new_balance
    to_account.current_balance = to_new_balance

    # Create transactions for auditing
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

    debit_txn = Transaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
        transaction_reference_number=f"REF-{uuid.uuid4().hex[:10].upper()}",
        account_id=from_account.account_id,
        channel="in-app",
        counterparty_bank="Sentinel",
        narration=request.narration or "Internal Transfer",
        transaction_type="debit",
        amount=amount,
        currency="NGN",
        transaction_balance=from_new_balance,
        transaction_status="completed",
        transaction_timestamp=timestamp,
    )

    credit_txn = Transaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
        transaction_reference_number=f"REF-{uuid.uuid4().hex[:10].upper()}",
        account_id=to_account.account_id,
        channel="in-app",
        counterparty_bank="Sentinel",
        narration=request.narration or "Internal Transfer",
        transaction_type="credit",
        amount=amount,
        currency="NGN",
        transaction_balance=to_new_balance,
        transaction_status="completed",
        transaction_timestamp=timestamp,
    )

    db.add(debit_txn)
    db.add(credit_txn)
    await db.commit()

    return {
        "status": "approved",
        "message": "Internal transfer successful",
        "reference": debit_txn.transaction_reference_number,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
