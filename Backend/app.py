#Libraries
import uvicorn
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, APIRouter, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import sys
import os
import uuid
import logging
import random
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime, timezone, date
from Backend.database import engine, Base, SessionLocal
from Backend.models import Complaint, Account, Transaction, Customer, User

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Backend.middleware import get_current_user
from app.agents.dispatcher_agent import DispatcherAgent
from app.agents.sentinel_agent import SentinelAgent
from Backend.api import router 
from app.utils.schemas import DispatcherQuery, SentinelQuery, ComplaintQuery
from Backend.schemas import TransactionRequest, CustomerCreate
from Backend.database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield 
    
    
    print("Shutting down: Disposing database engine...")
    await engine.dispose()

app = FastAPI(version="1.0.0", lifespan=lifespan)
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"Message": "Welcome to the Bank System AI Assistant"}


async def process_complaint_routing(complaint_id: str, complaint_text: str):
    """Background task to route complaints using the AI Agent."""
    
    # 1. Create a FRESH, independent database session
    async with SessionLocal() as db: 
        try:
            agent = DispatcherAgent()
            routing_result = await agent.run(input_data={"complaint_text": complaint_text}) 
            
            stmt = select(Complaint).filter(Complaint.complaint_id == complaint_id)
            result = await db.execute(stmt)
            complaint = result.scalars().first()

            if complaint:
                complaint.department_code = routing_result.get("department_code")
                complaint.department_name = routing_result.get("department")
                complaint.priority_level = routing_result.get("priority")
                complaint.sentiment = routing_result.get("sentiment")
                        
                db.add(complaint)
                await db.commit()
                print(f"Successfully routed complaint {complaint_id} to {complaint.department_name}")
            else:
                print(f"Error: Complaint {complaint_id} not found in database.")

        except Exception as e:
            print(f"CRITICAL AI ROUTING FAILURE for {complaint_id}: {e}")

    
@app.post("/make_complaint", tags=["DB_Operations"]) 
async def make_complaint(
    query: ComplaintQuery,
    background_tasks: BackgroundTasks, 
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db) 
):
    try:
        stmt = select(Account).filter(
            Account.account_number == query.account_number,
            Account.customer_id == user.customer_id
        )
        result = await db.execute(stmt)
        account = result.scalars().first()

        if not account:
            raise HTTPException(status_code=403, detail="Unauthorized account access")
        
        new_complaint_id = f"CMP-{uuid.uuid4().hex[:10].upper()}"
        clean_tx_id = query.linked_transaction_id if query.linked_transaction_id else None
        clean_ref = query.linked_reference if query.linked_reference else None
        new_complaint = Complaint(
            complaint_id=new_complaint_id,
            customer_id=user.customer_id, 
            # account_id=query.account_id, 
            linked_transaction_id=clean_tx_id,
            linked_reference=clean_ref,
            
            complaint_timestamp=datetime.now(timezone.utc).replace(tzinfo=None), 
            complaint_status="open",
            complaint_channel=query.complaint_channel,
            complaint_text=query.complaint_text,
            
            
            department_code=None, 
            department_name="Pending AI Routing", 
            priority_level="Pending",
            sentiment="Pending AI Routing" 
        )

        db.add(new_complaint)
        await db.commit() 
        await db.refresh(new_complaint) 

        # Fire off the AI routing task in the background
        background_tasks.add_task(
            process_complaint_routing, 
            complaint_id=new_complaint_id, 
            complaint_text=query.complaint_text
        )

        return {
            "message": "Complaint submitted successfully and is being routed.",
            "complaint_id": new_complaint_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback() 
        # logger.error(f"Complaint creation failed: {e}", exc_info=True)
        print(f"Complaint creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/customers", tags=["DB_Operations"], status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Customer).filter(or_(
                Customer.bvn == customer_data.bvn,
                Customer.email == customer_data.email
            )
        )
        result = await db.execute(stmt)
        existing_customer = result.scalars().first()

        if existing_customer:
            raise HTTPException(
                status_code=409, 
                detail="A customer with this BVN or Email already exists."
            )

        new_customer_id = f"CUST-{uuid.uuid4().hex[:10].upper()}"
        calculated_full_name = f"{customer_data.first_name} {customer_data.last_name}"
        
        today = date.today()
        dob = customer_data.date_of_birth
        calculated_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        
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
            onboarding_date=datetime.now(timezone.utc)
        )

        db.add(new_customer)
        generated_account_number = str(random.randint(1000000000, 9999999999))
        
        starting_balance = float(random.randint(5, 100) * 1000)

        new_account = Account(
            account_id=f"ACCT-{uuid.uuid4().hex[:10].upper()}",
            customer_id=new_customer_id, 
            account_number=generated_account_number,
            account_type="Savings", 
            currency="NGN",
            current_balance=starting_balance,
            opened_date=date.today()
        )
        db.add(new_account) 

        await db.commit()
        await db.refresh(new_customer)
        await db.refresh(new_account)

        return {
            "message": "Customer and Bank Account created successfully",
            "customer_id": new_customer.customer_id,
            "account_number": new_account.account_number,
            "starting_balance": new_account.current_balance
        }
        await db.commit()
        await db.refresh(new_customer)

        return {
            "message": "Customer created successfully",
            "customer_id": new_customer.customer_id
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    

@app.post("/make_transaction", tags=["Agents"])
async def make_transaction(
    request: TransactionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db), 
):
    try:
        stmt = select(Account).filter(
            Account.account_number == request.account_number,
            Account.customer_id == user.customer_id
        ).with_for_update()
        
        result = await db.execute(stmt)
        account = result.scalars().first()

        if not account:
            raise HTTPException(status_code=403, detail="Unauthorized account access")

        transaction_payload = request.model_dump()
        agent = SentinelAgent()
        fraud_result = await agent.run(transaction_payload)
        risk_score = fraud_result.get("risk_score", 0)
        
        if risk_score > 0.8:
            return {
                "status": "blocked",
                "message": "Transaction flagged as high fraud risk",
                "fraud_analysis": fraud_result
            }
        
        safe_amount = Decimal(str(request.amount))
        if request.transaction_type == "debit":
            new_balance = account.current_balance - safe_amount
            if new_balance < 0:
                raise HTTPException(status_code=400, detail="Insufficient funds")
        else: 
            new_balance = account.current_balance + safe_amount

        
        
        transaction = Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}", # Formatted as string
            transaction_reference_number=f"REF-{uuid.uuid4().hex[:10].upper()}",
            account_id=account.account_id,
            channel=request.channel,
            device_id=request.device_id,
            counterparty_bank=request.counterparty_bank,
            narration=request.narration,
            transaction_type=request.transaction_type,
            amount=safe_amount,
            currency=request.currency,
            transaction_balance=new_balance,
            transaction_status="completed",
            failure_reason=None,
            is_fraud_score=int(risk_score * 100), # Converts 0.85 to 85
            fraud_explainability_trace=fraud_result.get("reasoning"),
            transaction_timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        account.current_balance = new_balance

        db.add(transaction)
        await db.commit() 
        await db.refresh(transaction) 

        return {
            "status": "approved",
            "transaction_reference": transaction.transaction_reference_number,
            "fraud_analysis": fraud_result
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback() 
        # logger.error(f"Transaction failed: {e}", exc_info=True)
        print(f"Transaction failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)