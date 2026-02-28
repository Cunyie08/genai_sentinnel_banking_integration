from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# --- Auth Schemas ---

class UserBase(BaseModel):
    username: str
    email: EmailStr
    age: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str # Can be email or username
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Chat Schemas ---

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

# --- Onboarding Schemas ---

class OnboardingSubmission(BaseModel):
    answers: Dict[str, Any]

class OnboardingResponse(BaseModel):
    id: int
    user_id: int
    answers: Dict[str, Any]
    derived_profile: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Agent Schemas ---

class RoutingResponse(BaseModel):
    # intent: str = Field(description="Human-readable explanation of why complaint was routed")
    department_code: Literal["TSU", "COC", "FRM", "DCS", "AOD", "CLS"] = Field(description="Final banking department code")
    department_name: str = Field(description="Full department name")
    priority_level: Literal["Critical", "High", "Medium", "Low"] = Field(description="Priority level determined from complaint text and policy")
    sla_hours: int = Field(ge=1, description="Expected resolution SLA in hours from policy constants")
    routing_method: Literal["keyword", "rag", "keyword+rag", "default"] = Field(description="Routing strategy used to determine department")
    keyword_matches: List[str] = Field(description="Keywords detected in complaint that influenced routing")
    confidence: float = Field(ge=0, le=1,description="Final routing confidence score (0–1)")
    reasoning: str = Field(description="Policy-grounded reasoning combined with explanation overlay")

# class RoutingResponse(BaseModel):
#     intent: str = Field(description="Why the model is routing to the department")
#     department: str = Field(description="Banking department we are sending the complaint to")
#     confidence: float = Field(ge=0, le=1, description="Confidence score between 0 and 1")
#     reasoning: str = Field(description="How the model arrived at the decision")

# class FraudResponse(BaseModel):
#     intent: str = Field(description="Transaction Fraud Analysis")
#     department: str = Field(description="Fraud Prevention")
#     confidence: float = Field(ge=0, le=1, description="Confidence score between 0 and 1")
#     reasoning: str = Field(description="How the model arrived at the decision")

class RiskBreakdown(BaseModel):
    flag_score: int
    merchant_risk: int
    timing_risk: int

class FraudResponse(BaseModel):
    total_risk_score: int = Field(ge=0, le=100, description="Composite fraud risk score (0–100)")
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(description="Risk classification derived from RISK_THRESHOLDS")
    risk_breakdown: RiskBreakdown
    recommended_action: str = Field(description="Recommended action mapped from risk level")
    requires_challenge: bool = Field(description="True if push-to-app or OTP step-up authentication required")
    should_block: bool = Field(description="True if transaction must be blocked immediately")
    confidence: float = Field(ge=0, le=1, description="RAG retrieval confidence for policy explanation")
    ml_probability: float = Field(ge=0, le=1,description="ML-predicted probability of fraud")
    policy_explanation: str = Field(description="Merged policy_explanation + LLM explanation layer")

class TrajectoryResponse(BaseModel):
    explanation: str
    risk_summary: str
    governance_note: str