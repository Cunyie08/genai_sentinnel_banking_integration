import uvicorn
from fastapi import Depends, FastAPI, APIRouter, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Backend.middleware import get_current_user
from app.agents.dispatcher_agent import DispatcherAgent
from app.agents.sentinel_agent import SentinelAgent
from Backend.api import router 

app = FastAPI(version="1.0.0")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- New Models for Banking ---

class InternalTransfer(BaseModel):
    source_account_id: str
    destination_account_id: str
    amount: float
    description: Optional[str] = None

class FailedReport(BaseModel):
    transaction_id: str
    reason: str

# --- Original Models ---

class DispatcherQuery(BaseModel):
    complaint_text: str

class SentinelQuery(BaseModel):
    transaction_details: Dict[str, Any]

@app.get("/")
def home():
    return {"Message": "Welcome to the Bank System AI Assistant"}

# --- New Transaction Endpoints ---

@app.get("/transactions")
async def get_all_transactions(user: dict = Depends(get_current_user)):
    """List all transactions."""
    return {"transactions": []}  # Replace with database logic

@app.get("/transactions/{transactionId}")
async def get_transaction_by_id(transactionId: str, user: dict = Depends(get_current_user)):
    """Get details of a specific transaction."""
    return {"transaction_id": transactionId, "details": {}}

@app.get("/transactions/account/{accountId}")
async def get_account_transactions(accountId: str, user: dict = Depends(get_current_user)):
    """Get all transactions for a specific account."""
    return {"account_id": accountId, "transactions": []}

@app.get("/transactions/filter")
async def filter_transactions(
    date: Optional[str] = Query(None), 
    amount: Optional[float] = Query(None), 
    type: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Filter transactions by date, amount, or type."""
    return {"filters": {"date": date, "amount": amount, "type": type}, "results": []}

@app.get("/transactions/{transactionId}/status")
async def get_transaction_status(transactionId: str, user: dict = Depends(get_current_user)):
    """Check the status (Pending/Success/Failed) of a transaction."""
    return {"transaction_id": transactionId, "status": "Success"}

@app.post("/transactions/report-failed")
async def report_failed_transaction(report: FailedReport, user: dict = Depends(get_current_user)):
    """Report a transaction that did not process correctly."""
    return {"message": f"Report received for {report.transaction_id}"}

@app.post("/transactions/internal-transfer")
async def internal_transfer(transfer: InternalTransfer, user: dict = Depends(get_current_user)):
    """Handle money transfer between two internal accounts."""
    return {"status": "Transfer Initiated", "details": transfer}

# --- Original Agent Endpoints ---

@app.post("/dispatcher")
async def run_dispatcher(query: DispatcherQuery, user: dict = Depends(get_current_user)):
    agent = DispatcherAgent()
    result = await agent.run({"complaint_text": query.complaint_text})
    return result

@app.post("/sentinel")
async def run_sentinel(query: SentinelQuery, user: dict = Depends(get_current_user)):
    agent = SentinelAgent()
    result = await agent.run(query.transaction_details)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)