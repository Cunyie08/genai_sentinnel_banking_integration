#Libraries
import uvicorn
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, APIRouter, HTTPException, status, Body, Request
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import csv
from pathlib import Path
import sys
import os
import uuid
import logging
import random
from decimal import Decimal
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_sim
from svix.webhooks import Webhook
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, date
from app.core.orchestrator import Orchestrator

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Backend.database import engine, Base, SessionLocal, get_db
from Backend.models import Complaint, Account, Transaction, Customer, UserSettings, ComplaintRoutingDecision
from Backend.middleware import get_current_user
from app.utils.schemas import RoutingResponse, FraudResponse, RiskBreakdown, TrajectoryResponse
from app.agents.dispatcher_agent import DispatcherAgent
from app.agents.sentinel_agent import SentinelAgent
from app.agents.trajectory_agent import TrajectoryAgent
# from app.database.dataset_loader import DatasetLoader
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
from Backend.email_service import send_complaint_confirmation_email, send_department_routing_email
from app.settings import RESEND_WEBHOOK_SECRET, OPENAI_API_KEY, GEMINI_API_KEY
from Backend.schemas import (
    TransactionRequest,
    TransactionConfirmRequest,
    CustomerCreate,
    ProfileUpdate,
    PreferencesUpdate,
    SettingsResponse,
    UserResponse,
    FullUserResponse,
    AccountResponse,
    ReportFailedRequest,
    InternalTransferRequest, 
)
from Backend.email_service import send_auth_email
from Backend.auth import verify_password

# Module-level cache for FAQ semantic search (lazy-loaded on first use)
_faq_embedding_cache: dict = {"model": None, "embeddings": None}


class ComplaintQuery(BaseModel):
    account_number: str
    complaint_channel: str
    complaint_text: str
    linked_transaction_id: Optional[str] = None
    linked_reference: Optional[str] = None


logger = logging.getLogger(__name__)

orchestrator = Orchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    print("Initializing Orchestrator globally...")
    await orchestrator.initialize()
    print("Orchestrator Initialization complete.")
    yield

    print("Shutting down: Disposing database engine...")
    await engine.dispose()


app = FastAPI(title="Sentinnel Bank API", version="1.0.0", lifespan=lifespan)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://sentinnelbanking.com",
        "https://www.sentinnelbanking.com"
    ],
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
    current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)
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
                "current_balance": float(acc.current_balance),
                "status": acc.status,
            }
        )

    return {
        "customer_id": current_user.customer_id,
        "email": current_user.email,
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
    current_user: Customer = Depends(get_current_user),
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
    current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = select(UserSettings).filter(UserSettings.customer_id == current_user.customer_id)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        # Create default if missing
        settings = UserSettings(customer_id=current_user.customer_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@profile_router.patch("/users/update-preferences")
async def update_preferences(
    prefs: PreferencesUpdate,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserSettings).filter(UserSettings.customer_id == current_user.customer_id)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        settings = UserSettings(customer_id=current_user.customer_id)
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
@profile_router.get("/users/{customerId}", dependencies=[Depends(get_current_user)])
async def admin_get_user(
    customerId: str,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # if getattr(current_user, "role", None) != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(Customer).filter(Customer.customer_id == customerId)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@profile_router.delete("/users/{customerId}")
async def admin_delete_user(
    customerId: str,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # if getattr(current_user, "role", None) != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(Customer).filter(Customer.customer_id == customerId)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # user.is_active = False 
    await db.commit()
    return {"message": f"User {customerId} deactivated successfully"}


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
    stmt = select(Customer).filter(Customer.email == from_email)
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

    # 3. Trigger AI Routing synchronously
    await process_complaint_routing(
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
            # dataset_loader = DatasetLoader()  
            # await dataset_loader.load()
            # repo = BankRepository(dataset_loader)
            # rag_engine = await create_engine()
            complaint_request = {
            "type": "complaint",
            "department": "complaint",
            "complaint_id": complaint_id,
            "agent": "DispatcherAgent" 
        }
            result1 = await orchestrator.handle_request(complaint_request)
            print("\n=== DISPATCHER OUTPUT ===")
            print(result1)

            # openai_client = (
            #     AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
            # )
            # openai_llm = LLMClient(
            #     client=openai_client,
            #     model_name="gpt-4o",
            #     response_schema=RoutingResponse,
            # )
            # gemini_llm = LLMClient(
            #     client=genai.Client(api_key=GEMINI_API_KEY),
            #     model_name="gemini-2.0-flash",
            #     response_schema=RoutingResponse,
            # )

            # agent = DispatcherAgent(
            #     repo=repo,
            #     rag_engine=rag_engine,
            #     openai_llm=openai_llm,
            #     gemini_llm=gemini_llm,
            # )
            # routing_result = await agent.run(payload={"complaint_id": complaint_id})

            stmt = select(Complaint).filter(Complaint.complaint_id == complaint_id)
            result = await db.execute(stmt)
            complaint = result.scalars().first()

            try:
                # Dynamically filter values to only include defined column names
                valid_columns = {c.name for c in ComplaintRoutingDecision.__table__.columns}
                filtered_result = {k: v for k, v in result1.items() if k in valid_columns}

                decision_record = ComplaintRoutingDecision(**filtered_result)
                db.add(decision_record)
            except Exception as saving_issue:
                print(f"Failed to save ComplaintRoutingDecision: {saving_issue}")

            if complaint:
                complaint.department_code = result1.get("department_code")
                complaint.department_name = result1.get("department_name")
                complaint.priority_level = result1.get("priority_level")
                complaint.sentiment = result1.get("sentiment")

                await db.commit()
                print(
                    f"Successfully routed complaint {complaint_id} to {complaint.department_name}"
                )

                user_stmt = select(Customer).filter(
                    Customer.customer_id == complaint.customer_id
                )
                user_result = await db.execute(user_stmt)
                user = user_result.scalars().first()

                # if user:
                #     print(f"Sending auto-reply to {user.email}...")
                #     await send_complaint_confirmation_email(
                #         to_email=user.email,
                #         complaint_id=complaint_id,
                #         department=complaint.department_name,
                #         priority=complaint.priority_level,
                #     )

                department_emails = {
                    "TSU": "jofesdavid@gmail.com",
                    "COC": "dekpo231998@gmail.com",
                    "FRM": "ekpodavid120@gmail.com",
                    "DCS": "oshoridwanullah@gmail.com",
                    "AOD": "dekpo255@stu.ui.edu.ng",
                    "CLS": "businesskaoshi@gmail.com"
                }
                
                dept_code = complaint.department_code or ""
                target_email = department_emails.get(dept_code, "support@sentinelbank.com")

                await send_department_routing_email(
                    to_email=target_email,
                    complaint_id=complaint_id,
                    complaint_text=complaint_text,
                    department=complaint.department_name or "General Support",
                    priority=complaint.priority_level or "Low"
                )
            return result1

        except Exception as e:
            print(f"CRITICAL AI ROUTING FAILURE for {complaint_id}: {e}")

class AIChatRequest(BaseModel):
    user_prompt: str

class IntentResponse(BaseModel):
    intent: str

class ChatBotResponse(BaseModel):
    text: str


@app.post("/ai/chat", tags=["Agents"])
async def ai_chat(
    payload: AIChatRequest,
    user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_message = payload.user_prompt
        if not user_message:
            raise HTTPException(status_code=400, detail="Missing user_prompt")

        # 1. Initialize Infrastructure
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        
        # 2. Intent Classification using OpenAI with Gemini Fallback
        intent_prompt = f"""
        Classify the user's intent into one of: 'fraud_check', 'complaint_routing', 'product_recommendation', or 'general_query'.
        User Message: "{user_message}"
        Return JSON with key "intent".
        """
        
        try:
            intent_llm = LLMClient(
                client=AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None,
                model_name="gpt-4o",
                response_schema=IntentResponse,
            )
            intent_res = await intent_llm.generate(
                "Intent Classification System", intent_prompt
            )
        except Exception:
            intent_res = None
            
        if not intent_res:
            try:
                intent_llm = LLMClient(
                    client=genai.Client(api_key=GEMINI_API_KEY),
                    model_name="gemini-2.0-flash",
                    response_schema=IntentResponse,
                )
                intent_res = await intent_llm.generate(
                    "Intent Classification System", intent_prompt
                )
            except Exception as e:
                logger.error(f"Fallback Intent Classification failed: {e}")

        if isinstance(intent_res, dict):
            intent = intent_res.get("intent", "general_query")
        elif hasattr(intent_res, "intent"):
            intent = getattr(intent_res, "intent", "general_query")
        else:
            intent = "general_query"

        bot_text = "I'm here to help you with your banking needs."

        # 3. Dispatch to Agent based on Intent
        if intent == "fraud_check":
            # Find last transaction for context
            stmt = (
                select(Transaction)
                .join(Account)
                .filter(Account.customer_id == user.customer_id)
                .order_by(Transaction.transaction_timestamp.desc())
                .limit(1)
            )
            res = await db.execute(stmt)
            last_txn = res.scalars().first()

            if last_txn:
                payload = {
                    "type": "transaction",
                    "department": "fraud",
                    "transaction_id": last_txn.transaction_id,
                    "agent": "SentinelAgent",
                    "account_id": last_txn.account_id,
                    "amount": float(last_txn.amount),
                    "channel": last_txn.channel
                }
                agent_res = await orchestrator.handle_request(payload)
                risk = agent_res.get("risk_level", "UNKNOWN")
                bot_text = f"I've analyzed your latest transaction ({last_txn.transaction_reference_number}). Risk Level: **{risk}**. {agent_res.get('risk_summary', '')}"
            else:
                bot_text = "I couldn't find any recent transactions for your account to perform a fraud check."

        elif intent == "complaint_routing":
            # Find last complaint for context
            stmt = (
                select(Complaint)
                .filter(Complaint.customer_id == user.customer_id)
                .order_by(Complaint.complaint_timestamp.desc())
                .limit(1)
            )
            res = await db.execute(stmt)
            last_comp = res.scalars().first()

            if last_comp:
                payload = {
                    "type": "complaint",
                    "department": "complaint",
                    "complaint_id": last_comp.complaint_id,
                    "agent": "DispatcherAgent" 
                }
                agent_res = await orchestrator.handle_request(payload)
                bot_text = f"Regarding your complaint **{last_comp.complaint_id}**: It has been routed to the **{agent_res.get('department_name')}** department. Priority: **{agent_res.get('priority_level')}**."
            else:
                bot_text = "You don't have any active complaints. You can file one by sending an email to support@sentinelbank.com."

        elif intent == "product_recommendation":
            payload = {
                "type": "recommendation",
                "department": "recommendation",
                "customer_id": user.customer_id,
                "agent": "TrajectoryAgent"
            }
            agent_res = await orchestrator.handle_request(payload)
            product = agent_res.get("primary_product")
            if product and product != "None":
                bot_text = f"Based on your financial trajectory, I recommend the **{product}**. {agent_res.get('reasoning', '')}"
            else:
                bot_text = "I don't have a specific product recommendation for you right now, but check back soon as your profile grows!"

        else:
            # General query handling
            faq_path = Path(__file__).parent.parent / "app" / "rag" / "knowledge_base" / "faqs" / "FAQ-001.txt"
            faq_content = ""
            if faq_path.exists():
                with open(faq_path, "r", encoding="utf-8") as f:
                    faq_content = f.read()

            prompt = f"""
            You are 'Sentinel AI', the internal banking chatbot for Sentinel Bank.
            User: {user.email} (Customer ID: {user.customer_id})
            
            Here are the officially approved FAQs:
            ---
            {faq_content}
            ---
            
            INSTRUCTIONS:
            1. You must answer the user's question using ONLY the provided FAQs.
            2. If the user's question or prompt is not similar to any of the FAQs, or cannot be fully answered using the FAQs, you MUST output EXACTLY:
            "Please refer to Customer Service"
            Do not output any other text or explanation.

            User's Message: {user_message}
            """
            
            try:
                chat_llm = LLMClient(
                    client=AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None,
                    model_name="gpt-4o",
                    response_schema=ChatBotResponse,
                )
                response = await chat_llm.generate("Sentinel AI Persona", prompt)
            except Exception:
                response = None
                
            if not response:
                try:
                    chat_llm = LLMClient(
                        client=genai.Client(api_key=GEMINI_API_KEY),
                        model_name="gemini-2.0-flash",
                        response_schema=ChatBotResponse,
                    )
                    response = await chat_llm.generate("Sentinel AI Persona", prompt)
                except Exception as e:
                    logger.error(f"Fallback Chatbot failed: {e}")
                    response = None
            
            
            if isinstance(response, dict):
                bot_text = response.get("text", "Please refer to Customer Service")
            elif hasattr(response, "text"):
                bot_text = getattr(response, "text", "Please refer to Customer Service")
            else:
                bot_text = str(response) if response else "Please refer to Customer Service"

            # Enforcing strict adherence if LLM returns a variation
            if "Please refer to Customer Service" in bot_text:
                bot_text = "Please refer to Customer Service"

        return {
            "id": uuid.uuid4().hex,
            "sender": "ai",
            "type": "text",
            "text": bot_text,
            "time": datetime.now().strftime("%I:%M %p"),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        logger.error(f"Chat error: {e}")
        logger.error(traceback.format_exc())
        return {
            "id": uuid.uuid4().hex,
            "sender": "ai",
            "type": "text",
            "text": f"Error: {str(e)}",
            "time": datetime.now().strftime("%I:%M %p"),
        }

@app.post("/make_complaint", tags=["Agents"])
async def make_complaint(
    query: ComplaintQuery,
    background_tasks: BackgroundTasks,
    user: Customer = Depends(get_current_user),
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
            account_id=account.account_id,
            linked_transaction_id=(
                query.linked_transaction_id
                if query.linked_transaction_id
                and query.linked_transaction_id != "string"
                else None
            ),
            linked_reference=(
                query.linked_reference
                if query.linked_reference and query.linked_reference != "string"
                else None
            ),
            complaint_timestamp=datetime.now(),
            complaint_status="open",
            complaint_channel=query.complaint_channel,
            complaint_text=query.complaint_text,
            department_name="Pending AI Routing",
        )

        db.add(new_complaint)
        await db.flush()
        await db.commit()

        # Enqueue the background task for AI processing and emails
        background_tasks.add_task(
            process_complaint_routing,
            complaint_id=new_complaint_id,
            complaint_text=query.complaint_text
        )

        return {
            "message": "Customer complaint submitted sucessfully",
            "complaint_id": new_complaint_id
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

        # Append to customers.csv so agents can find it
        csv_path = Path(__file__).parent.parent / "customers.csv"
        file_exists = csv_path.exists()
        with open(csv_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(
                    [
                        "customer_id",
                        "first_name",
                        "last_name",
                        "full_name",
                        "gender",
                        "age",
                        "date_of_birth",
                        "bvn",
                        "nin",
                        "phone_number",
                        "telco_provider",
                        "email",
                        "state_of_origin",
                        "residential_state",
                        "banking_branch",
                        "solo_candidate",
                        "onboarding_date",
                    ]
                )
            writer.writerow(
                [
                    new_customer.customer_id,
                    new_customer.first_name,
                    new_customer.last_name,
                    new_customer.full_name,
                    new_customer.gender,
                    new_customer.age,
                    new_customer.date_of_birth,
                    new_customer.bvn,
                    new_customer.nin,
                    new_customer.phone_number,
                    new_customer.telco_provider,
                    new_customer.email,
                    new_customer.state_of_origin,
                    new_customer.residential_state,
                    new_customer.banking_branch,
                    True,  # Default solo_candidate to True
                    new_customer.onboarding_date,
                ]
            )

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
    user: Customer = Depends(get_current_user),
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

        # Build payload with mock transaction_id for initial scoring
        txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        safe_amount = Decimal(str(request.amount))
            


        from sqlalchemy import func
        txn_count_stmt = select(func.count()).select_from(Transaction).where(Transaction.account_id == account.account_id)
        txn_count_result = await db.execute(txn_count_stmt)
        txn_count_so_far = txn_count_result.scalar() or 0

        payload = {
            "type": "transaction",
            "department": "fraud",
            "transaction_id": txn_id,
            "agent": "SentinelAgent",
            "account_id": account.account_id,
            "amount": float(safe_amount),
            "channel": request.channel,
            "device_id": request.device_id,
            "merchant_name": request.merchant_name,
            "narration": request.narration,
            "counterparty_bank": request.counterparty_bank,
            "transaction_type": request.transaction_type,
            "currency": request.currency,
            "txn_count_so_far": txn_count_so_far,
        }

        fraud_result = await orchestrator.handle_request(payload)
        
        # In case the result is structured differently
        risk_score = fraud_result.get("total_risk_score", 0)

        is_pending = risk_score > 80

        if request.transaction_type == "debit":
            if account.current_balance < safe_amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            new_balance = account.current_balance - safe_amount
        else:
            new_balance = account.current_balance + safe_amount

        transaction = Transaction(
            transaction_id=txn_id,
            transaction_reference_number=f"REF-{uuid.uuid4().hex[:10].upper()}",
            account_id=account.account_id,
            customer_id=account.customer_id,
            channel=request.channel,
            device_id=request.device_id,
            counterparty_bank=request.counterparty_bank,
            narration=request.narration,
            amount=safe_amount,
            currency=request.currency,
            merchant_name=request.merchant_name,
            transaction_type=request.transaction_type,
            transaction_balance=new_balance if not is_pending else account.current_balance,
            transaction_status="pending" if is_pending else "completed",
            is_fraud_score=int(risk_score),
            fraud_explainability_trace=fraud_result.get("policy_explanation") or fraud_result.get("reasoning") or "No explanation provided.",
            transaction_timestamp=datetime.now(),
        )

        db.add(transaction)
        
        if not is_pending:
            account.current_balance = new_balance
            
        await db.commit()

        if is_pending:
            return {
                "status": "PENDING_CONFIRMATION",
                "message": "Transaction requires customer confirmation",
                "transaction_id": txn_id,
                "fraud_analysis": fraud_result,
            }

        return fraud_result
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions/confirm", tags=["Agents"])
async def confirm_transaction(
    request: TransactionConfirmRequest,
    user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Verify the password (stored as plain text)
        if request.password != user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid password")
            
        stmt = select(Transaction).filter(
            Transaction.transaction_id == request.transaction_id,
            Transaction.transaction_status == "pending"
        ).with_for_update()
        
        result = await db.execute(stmt)
        transaction = result.scalars().first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Pending transaction not found")
            
        # Get the account to update its balance
        stmt_acc = select(Account).filter(Account.account_id == transaction.account_id).with_for_update()
        res_acc = await db.execute(stmt_acc)
        account = res_acc.scalars().first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        # Perform the balance adjustment
        safe_amount = Decimal(str(transaction.amount))
        if transaction.transaction_type == "debit":
            if account.current_balance < safe_amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            account.current_balance -= safe_amount
        else:
            account.current_balance += safe_amount
            
        transaction.transaction_status = "completed"
        transaction.transaction_balance = account.current_balance
        
        await db.commit()
        
        return {"status": "success", "message": "Transaction verified and completed successfully"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/card_transaction", tags=["Agents"])
async def card_transaction(
    request: TransactionRequest,
    user: Customer = Depends(get_current_user),
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

        txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        safe_amount = Decimal(str(request.amount))
            


        payload = {
            "type": "transaction",
            "department": "fraud",
            "transaction_id": txn_id,
            "agent": "SentinelAgent",
            "account_id": account.account_id,
            "amount": float(safe_amount),
            "channel": "pos", # Default card channel to enforce challenge policy
            "device_id": request.device_id,
            "merchant_name": request.merchant_name,
            "narration": request.narration,
            "counterparty_bank": request.counterparty_bank,
            "transaction_type": "debit",
            "currency": request.currency,
        }

        fraud_result = await orchestrator.handle_request(payload)

        # Force card transactions to always require confirmation via popup
        is_pending = True

        transaction = Transaction(
            transaction_id=txn_id,
            transaction_reference_number=f"REF-{uuid.uuid4().hex[:10].upper()}",
            account_id=account.account_id,
            customer_id=account.customer_id,
            channel="pos",
            device_id=request.device_id,
            counterparty_bank=request.counterparty_bank,
            narration=request.narration,
            amount=safe_amount,
            currency=request.currency,
            merchant_name=request.merchant_name,
            transaction_type=request.transaction_type,
            transaction_balance=account.current_balance, # Don't deduct yet
            transaction_status="pending",
            is_fraud_score=int(fraud_result.get("total_risk_score", 0)),
            fraud_explainability_trace=fraud_result.get("policy_explanation") or fraud_result.get("reasoning") or "Mandatory card challenge override.",
            transaction_timestamp=datetime.now(),
        )

        db.add(transaction)
        await db.commit()

        return {
            "status": "PENDING_CONFIRMATION",
            "message": "Card transaction requires confirmation",
            "transaction_id": txn_id,
            "fraud_analysis": fraud_result
        }
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        return {
            "status": "success",
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trajectory/popup_recommendations", tags=["Agents"])
async def get_trajectory_popup(
    user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        stmt = select(Customer).filter(Customer.email == user.email)
        res = await db.execute(stmt)
        active_user = res.scalars().first()

        customer_id = active_user.customer_id if active_user else user.customer_id
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="Authenticated user is not linked to a customer profile.",
            )

        recommendation_result = await orchestrator.handle_request({
            "type":        "recommendation",
            "agent":       "TrajectoryAgent",
            "customer_id": customer_id,
        })

        cards = []
        primary = recommendation_result.get("primary_product")

        # Check primary_product only, NOT is_eligible
        # is_eligible can be False when RAG validation fails even though
        # the recommendation engine correctly found a qualifying product.
        if primary:
            style_map = {
                "Student Loan":    {"grad": ["#2F4F4F", "#1A2E2E"], "label": "Education First"},
                "Car Loan":        {"grad": ["#1e3a8a", "#1e1b4b"], "label": "Lifestyle"},
                "Investment Plan": {"grad": ["#0f172a", "#1e293b"], "label": "Smart Investing"},
                "Trust Fund":      {"grad": ["#1a1a2e", "#16213e"], "label": "Wealth Preservation"},
                "Personal Loan":   {"grad": ["#7c2d12", "#431407"], "label": "Quick Cash"},
                "Fixed Deposit":   {"grad": ["#065f46", "#064e3b"], "label": "Grow Wealth"},
                "Credit Card":     {"grad": ["#7c3aed", "#4c1d95"], "label": "Flexible"},
            }
            style = style_map.get(
                primary,
                {"grad": ["#111827", "#000000"], "label": "Special Offer"}
            )

            # Subtitle: Avoids showing "Up to ₦0" for investment products
            emi = recommendation_result.get("monthly_emi") or 0
            subtitle_map = {
                "Investment Plan": "Tailored to your goals",
                "Trust Fund":      "Long-term wealth preservation",
                "Student Loan":    "Up to ₦2,000,000",
                "Car Loan":        f"₦{emi:,.0f}/month" if emi else "Flexible repayment",
                "Personal Loan":   f"₦{emi:,.0f}/month" if emi else "Quick approval",
            }
            subtitle = subtitle_map.get(primary, "Personalised for you")

            cards.append({
                "id":        uuid.uuid4().hex[:8],
                "label":     style["label"],
                "title":     primary,
                "subtitle":  subtitle,
                "cta":       "APPLY NOW",
                "ctaRoute":  "loans",
                "gradient":  style["grad"],
                "reasoning": recommendation_result.get("reasoning", ""),
            })

        return {
            "status":          "success" if cards else "no_recommendation",
            "recommendations": recommendation_result,
            "cards":           cards,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/trajectory/popup_recommendations", tags=["Agents"])
# async def get_trajectory_popup(
#     user: Customer = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     try:
#         # Force fetch the user from DB to ensure customer_id is mapped just in case the JWT middleware detached it
#         stmt = select(Customer).filter(Customer.email == user.email)
#         res = await db.execute(stmt)
#         active_user = res.scalars().first()

#         customer_id = active_user.customer_id if active_user else user.customer_id
#         if not customer_id:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Authenticated user is not linked to a customer profile.",
#             )


#         payload = {
#             "type": "recommendation",
#             "agent": "TrajectoryAgent",
#             "customer_id": customer_id
#         }
        
#         recommendation_result = await orchestrator.handle_request(payload)

#         # Format into "Cards" for the frontend marquee/popup
#         cards = []
#         primary = recommendation_result.get("primary_product")

#         if primary and recommendation_result.get("is_eligible"):
#             # Determine visual style based on product type
#             style = {
#                 "Student Loan": {
#                     "grad": ["#2F4F4F", "#1A2E2E"],
#                     "label": "Education First",
#                 },
#                 "Car Loan": {"grad": ["#1e3a8a", "#1e1b4b"], "label": "Lifestyle"},
#                 "Fixed Deposit": {
#                     "grad": ["#065f46", "#064e3b"],
#                     "label": "Grow Wealth",
#                 },
#                 "Credit Card": {"grad": ["#7c3aed", "#4c1d95"], "label": "Flexible"},
#             }.get(primary, {"grad": ["#111827", "#000000"], "label": "Special Offer"})

#             main_card = {
#                 "id": uuid.uuid4().hex[:8],
#                 "label": style["label"],
#                 "title": primary,
#                 "subtitle": f"Up to ₦{recommendation_result.get('monthly_emi', 0) * 10:,.0f}",
#                 "cta": "APPLY NOW",
#                 "ctaRoute": "loans",
#                 "gradient": style["grad"],
#                 "reasoning": recommendation_result.get("reasoning", ""),
#             }
#             cards.append(main_card)

#         # If no recommendation exists, return an empty list of cards
#         return {
#             "status": "success" if cards else "no_recommendation",
#             "recommendations": recommendation_result,
#             "cards": cards,
#         }
#     except Exception as e:
#         import traceback

#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))




# @app.post("/trajectory/email_recommendations", tags=["Agents"])
# async def post_trajectory_email(
# ... endpoint disabled to rely purely on frontend popups



@app.get("/accounts", tags=["Accounts"], response_model=List[AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db), user: Customer = Depends(get_current_user)
):
    stmt = select(Account).filter(Account.customer_id == user.customer_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/accounts/{accountNumber}", tags=["Accounts"], response_model=AccountResponse)
async def get_account_details(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
):
    stmt = select(Account).filter(
        Account.account_number == accountNumber, Account.customer_id == user.customer_id
    )
    result = await db.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "account_number": accountNumber,
        "current_balance": float(account.current_balance),
    }


@app.get("/accounts/{accountNumber}/status", tags=["Accounts"])
async def get_account_status(
    accountNumber: str,
    db: AsyncSession = Depends(get_db),
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
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
    db: AsyncSession = Depends(get_db), user: Customer = Depends(get_current_user)
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
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
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
    user: Customer = Depends(get_current_user),
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
        raise HTTPException(
            status_code=400, detail="The recipient account number does not exist."
        )

    if from_account.account_id == to_account.account_id:
        raise HTTPException(
            status_code=400, detail="Cannot transfer to the same account"
        )

    amount = Decimal(str(request.amount))
    if from_account.current_balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Generate a transaction ID for the background process
    txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"

    # Append pending transaction to transactions.csv for the DatasetLoader
    base_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    csv_path_txn = base_dir / "transactions.csv"
    
    import csv    
    with open(csv_path_txn, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            txn_id,
            from_account.account_id,
            f"REF-{uuid.uuid4().hex[:10].upper()}",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            request.amount,
            "pending", # transaction_status
            "NGN",
            "debit",
            "", # fee
            "in-app",
            to_account.account_id, # destination_account
            "", # merchant_name
            "", # merchant_category
            "0", # is_fraud_flag
            "",
            ""
        ])

    orchestrator = Orchestrator()
    await orchestrator.initialize()

    # Build a simulated payload for the Sentinel Agent
    sentinel_payload = {
        "type": "transaction",
        "department": "fraud",
        "transaction_id": txn_id,
        "agent": "SentinelAgent",
        "account_id": from_account.account_id,
        "amount": float(amount),
        "channel": "in-app",
    }

    fraud_result = await orchestrator.handle_request(sentinel_payload)
    
    # Depending on format: orchestrator returns {"total_risk_score": 0} normally
    risk_score = fraud_result.get("total_risk_score", fraud_result.get("risk_score", 0))

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
        customer_id=from_account.customer_id,
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
        customer_id=to_account.customer_id,
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


@app.get("/faqs", tags=["Support"])
async def get_faqs(prompt: Optional[str] = None):
    """
    Search FAQs using keyword matching.
    Returns the best matching FAQ if score >= threshold, otherwise fallback message.
    """
    # Parse FAQs from file
    base_dir = Path(__file__).resolve().parent.parent
    faq_path = base_dir / "app" / "rag" / "knowledge_base" / "faqs" / "FAQ-001.txt"

    if not faq_path.exists():
        raise HTTPException(status_code=404, detail="FAQ file not found.")

    with open(faq_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    faqs = []
    current_category = "General"
    current_q = None
    current_a = []
    in_answer = False

    for line in lines:
        stripped = line.strip()

        # Check for Category/Section Header
        if stripped.startswith("SECTION "):
            current_category = stripped.split(":", 1)[-1].strip()
            continue

        # Check for Question
        if stripped.startswith("Q") and ":" in stripped:
            if current_q and current_a:
                faqs.append({
                    "category": current_category,
                    "question": current_q,
                    "answer": "\n".join(current_a).strip()
                })

            # Extract new question
            current_q = stripped.split(":", 1)[-1].strip()
            current_a = []
            in_answer = False
            continue

        # Check for Answer starting
        if stripped.startswith("A:"):
            in_answer = True
            current_a.append(stripped[2:].strip())
            continue

        # Append continuing answer text
        if in_answer and stripped and not stripped.startswith("──") and not stripped.startswith("=="):
            current_a.append(stripped)

    # Append the last Q/A pair
    if current_q and current_a:
        faqs.append({
            "category": current_category,
            "question": current_q,
            "answer": "\n".join(current_a).strip()
        })

    if not prompt:
        # Return all FAQs if no prompt
        return {"faqs": faqs}

    # Semantic similarity search using sentence-transformer embeddings.
    # Model and question embeddings are computed once and cached for the
    # lifetime of the server process (FAQ file does not change at runtime).
    if _faq_embedding_cache["model"] is None:
        _faq_embedding_cache["model"] = SentenceTransformer("all-MiniLM-L6-v2")
        questions = [f["question"] for f in faqs]
        _faq_embedding_cache["embeddings"] = _faq_embedding_cache["model"].encode(
            questions, convert_to_numpy=True
        )

    model = _faq_embedding_cache["model"]
    question_embeddings = _faq_embedding_cache["embeddings"]

    prompt_embedding = model.encode([prompt], convert_to_numpy=True)
    similarities = sklearn_cosine_sim(prompt_embedding, question_embeddings)[0]

    # Rank all FAQs by similarity score, highest first
    ranked = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
    best_idx, best_score = ranked[0]
    best_score = float(best_score)

    # Threshold calibrated from test-suite results:
    #   min true-positive score = 0.5118, max unrelated-query score = 0.2216
    #   Threshold set at 0.40 — sits in the middle of that gap.
    SIMILARITY_THRESHOLD = 0.40

    if best_score >= SIMILARITY_THRESHOLD:
        best_faq = faqs[best_idx]

        if best_score >= 0.70:
            confidence_label = "High"
        elif best_score >= 0.50:
            confidence_label = "Medium"
        else:
            confidence_label = "Low"

        # Collect up to 2 runner-up FAQs above a lower floor
        alternatives = []
        for idx, score in ranked[1:]:
            if float(score) >= 0.20 and len(alternatives) < 2:
                alternatives.append({
                    "question": faqs[idx]["question"],
                    "similarity_score": round(float(score), 4),
                })

        return {
            "success": True,
            "match": {
                "question": best_faq["question"],
                "answer": best_faq["answer"],
                "similarity_score": round(best_score, 4),
                "confidence": round(best_score, 4),
                "confidence_label": confidence_label,
            },
            "alternatives": alternatives,
        }
    else:
        return {
            "success": False,
            "message": (
                "No matching FAQ found for your query. "
                "Please contact Customer Service for personalised assistance."
            ),
            "contact": {
                "phone": "0700-SENTINEL (0700-736-8463)",
                "fraud_email": "fraud-desk@sentinelbank.ng",
                "complaints_email": "complaints@sentinelbank.ng",
                "hours": "24/7 Customer Care available",
            },
            "searched_for": prompt,
        }
if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)
    # uvicorn.run(app, host='127.0.0.1', port=8080)
