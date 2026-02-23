from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr 
    password: str

class RegisterResponse(BaseModel):
    message: str
    user_id: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 

class UserResponse(UserBase):
    user_id: str 
    role: str
    
    
    class Config:
        from_attributes = True

# --- Chat Schemas ---

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class OnboardingSubmission(BaseModel):
    answers: Dict[str, Any]

class OnboardingResponse(BaseModel):
    id: str 
    user_id: str 
    answers: Dict[str, Any]
    derived_profile: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Agent Schemas ---

class RoutingResponse(BaseModel):
    intent: str = Field(description="Why the model is routing to the department")
    department: str = Field(description="Banking department we are sending the complaint to")
    confidence: float = Field(ge=0, le=1, description="Confidence score between 0 and 1")
    reasoning: str = Field(description="How the model arrived at the decision")

class FraudResponse(BaseModel):
    agent: str = Field(description="Fraud detection system or model version that evaluated the transaction.")
    risk_percentage: float = Field(ge=0,le=1,description="Fraud risk score expressed as a percentage (0 = no risk, 100 = confirmed fraud).")
    decision: Literal["approve", "review", "block"] = Field(description="Final action taken based on the fraud risk assessment.")
    reasoning: str = Field(description="Detailed explanation describing why the transaction received this fraud risk percentage and decision.")

# --- Transaction Schemas ---

# class TransactionRequest(BaseModel):
#     # Changed from UUID to str to support 'ACCT-...' format
#     account_id: str 
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

# --- Customer Schemas ---

class CustomerCreate(BaseModel):
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    date_of_birth: date
    bvn: str = Field(..., min_length=11, max_length=11, description="11-digit Bank Verification Number")
    nin: str = Field(..., min_length=11, max_length=11, description="11-digit National Identity Number")
    phone_number: str
    telco_provider: str
    email: EmailStr
    state_of_origin: str
    residential_state: str
    banking_branch: str