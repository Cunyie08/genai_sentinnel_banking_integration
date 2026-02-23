from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal

class RoutingResponse(BaseModel):
    intent: str = Field(description="Why the model is routing to the department")
    department: str = Field(description="Banking department we are sending the complaint to")
    department_code: str = Field(description="department code")
    confidence: float = Field(ge=0, le=1, description="Confidence score between 0 and 1")
    reasoning: str = Field(description="How the model arrived at the decision")
    priority: Literal["low", "medium", "high"] = Field(description="The assigned urgency level of the complaint based on financial risk, time sensitivity, or customer distress.")
    sentiment: Literal["angry", "calm", "neutral"]

class FraudResponse(BaseModel):
    agent: str = Field(description="Fraud detection system or model version that evaluated the transaction.")
    risk_percentage: float = Field(ge=0,le=1,description="Fraud risk score expressed as a percentage (0 = no risk, 100 = confirmed fraud).")
    decision: Literal["approve", "review", "block"] = Field(description="Final action taken based on the fraud risk assessment.")
    reasoning: str = Field(description="Detailed explanation describing why the transaction received this fraud risk percentage and decision.")
    


class DispatcherQuery(BaseModel):
    complaint_text: str = Field(..., max_length=2000)

class SentinelQuery(BaseModel):
    transaction_details: Dict[str, Any]

# class ComplaintQuery(BaseModel):
#     account_id: str = Field(..., description="The ID of the account the complaint is related to")
#     linked_transaction_id: Optional[str] = Field(None, description="Optional: ID of the specific transaction causing the issue")
#     linked_reference: Optional[str] = Field(None, description="Optional: Any reference number provided by the user")
#     complaint_channel: str = Field(..., example="mobile_app", description="How the complaint was submitted (e.g., web, mobile)")
#     complaint_text: str = Field(..., description="The actual complaint written by the customer")

class ComplaintQuery(BaseModel):
    # Changed from account_id to account_number
    account_number: str = Field(..., description="The 10-digit account number the complaint is related to")
    linked_transaction_id: Optional[str] = Field(None)
    linked_reference: Optional[str] = Field(None)
    complaint_channel: str = Field(..., example="mobile_app")
    complaint_text: str = Field(...)

# class TransactionRequest(BaseModel):
#     account_number: str = Field(..., description="The 10-digit account number")
#     channel: str
#     device_id: str
#     counterparty_bank: str
#     narration: str
#     transaction_type: Literal["debit", "credit"]
#     amount: float = Field(gt=0)
#     currency: str
#     merchant_category: str | None = None
#     merchant_name: str | None = None

class TransactionRequest(BaseModel):
    # Changed from account_id to account_number
    account_number: str = Field(..., description="The 10-digit account number")
    channel: str
    device_id: str
    counterparty_bank: str
    narration: str
    transaction_type: Literal["debit", "credit"]
    amount: float = Field(gt=0)
    currency: str
    merchant_category: str | None = None
    merchant_name: str | None = None