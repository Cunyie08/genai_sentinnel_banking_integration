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
    department: str = Field(
        description="Banking department we are sending the complaint to"
    )
    confidence: float = Field(
        ge=0, le=1, description="Confidence score between 0 and 1"
    )
    reasoning: str = Field(description="How the model arrived at the decision")


class FraudResponse(BaseModel):
    agent: str = Field(
        description="Fraud detection system or model version that evaluated the transaction."
    )
    risk_percentage: float = Field(
        ge=0,
        le=1,
        description="Fraud risk score expressed as a percentage (0 = no risk, 100 = confirmed fraud).",
    )
    decision: Literal["approve", "review", "block"] = Field(
        description="Final action taken based on the fraud risk assessment."
    )
    reasoning: str = Field(
        description="Detailed explanation describing why the transaction received this fraud risk percentage and decision."
    )


# --- Transaction Schemas ---


class TransactionRequest(BaseModel):
    account_number: str = Field(..., description="The 10-digit account number")
    channel: str = "mobile"
    device_id: str
    counterparty_bank: str
    narration: str
    transaction_type: Literal["debit", "credit"]
    amount: float = Field(gt=0)
    currency: str
    merchant_name: str | None = None


class TransactionConfirmRequest(BaseModel):
    transaction_id: str
    password: str


class ReportFailedRequest(BaseModel):
    transaction_id: str
    reason: str


class InternalTransferRequest(BaseModel):
    from_account_number: str
    to_account_number: str
    amount: float = Field(gt=0)
    narration: Optional[str] = None


# --- Customer Schemas ---


class CustomerCreate(BaseModel):
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    date_of_birth: date
    bvn: str = Field(
        ...,
        min_length=11,
        max_length=11,
        description="11-digit Bank Verification Number",
    )
    nin: str = Field(
        ...,
        min_length=11,
        max_length=11,
        description="11-digit National Identity Number",
    )
    phone_number: str
    telco_provider: str
    email: EmailStr
    state_of_origin: str
    residential_state: str
    banking_branch: str


# --- Auth Extended Schemas ---


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str
    purpose: Literal["registration", "reset", "transaction"]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# --- User Profile Extended ---


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    telco_provider: Optional[str] = None


class PreferencesUpdate(BaseModel):
    theme: Optional[Literal["light", "dark"]] = None
    language: Optional[str] = None
    notify_transactions: Optional[bool] = None
    notify_promotions: Optional[bool] = None


class SettingsResponse(BaseModel):
    theme: str
    language: str
    notify_transactions: bool
    notify_promotions: bool
    two_factor_enabled: bool

    class Config:
        from_attributes = True

# --- Account Schemas ---


class AccountResponse(BaseModel):
    account_id: str
    account_number: str
    account_type: Optional[str] = None
    currency: Optional[str] = None
    balance: float
    current_balance: float
    status: Optional[str] = None
    opened_date: Optional[date] = None

    class Config:
        from_attributes = True
        

# --- Account Schemas ---


class AccountResponse(BaseModel):
    account_id: str
    account_number: str
    account_type: Optional[str] = None
    currency: Optional[str] = None
    balance: float
    current_balance: float
    status: Optional[str] = None
    opened_date: Optional[date] = None

    class Config:
        from_attributes = True


class FullUserResponse(UserResponse):
    customer_details: Optional[Dict[str, Any]] = None
    account_details: List[AccountResponse] = []


# --- Quick Services Schemas ---


class AirtimePurchaseRequest(BaseModel):
    account_id: str
    provider: str
    phone_number: str
    amount: float = Field(gt=0)


class DataPurchaseRequest(BaseModel):
    account_id: str
    provider: str
    phone_number: str
    data_plan: str
    amount: float = Field(gt=0)


class BillPayRequest(BaseModel):
    account_id: str
    provider: str
    category: str
    bill_account_number: str
    amount: float = Field(gt=0)


class ServiceTransactionResponse(BaseModel):
    service_tx_id: str
    service_type: str
    provider: Optional[str] = None
    amount: float
    status: str
    reference: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderOut(BaseModel):
    name: str
    code: str


class BillCategoryOut(BaseModel):
    name: str
    code: str


# --- Admin Schemas ---


class AdminUserStatusUpdate(BaseModel):
    status: str = Field(..., description="active | suspended | deactivated")


class TicketAssign(BaseModel):
    assigned_to: str = Field(
        ..., description="user_id of the agent to assign the ticket to"
    )


class TicketResolve(BaseModel):
    resolution_note: Optional[str] = None


class AnalyticsSummary(BaseModel):
    total: int
    period: str
    breakdown: dict


# --- Audit Schemas ---


class AuditLogOut(BaseModel):
    log_id: int
    actor_id: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True





# --- Card Schemas ---


class CardRequest(BaseModel):
    account_id: str
    card_type: Literal["Debit", "Credit"]


class CardResponse(BaseModel):
    card_id: str
    account_id: str
    card_type: Optional[str] = None
    status: Optional[str] = None
    card_number: str
    expiry_date: str
    daily_limit: float

    class Config:
        from_attributes = True


class CardLimitUpdate(BaseModel):
    daily_limit: float = Field(gt=0)


# --- Notification Schemas ---


class NotificationResponse(BaseModel):
    notification_id: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationSend(BaseModel):
    customer_id: str
    title: str
    message: str


# --- Settings Schemas ---


class ThemeUpdate(BaseModel):
    theme: Literal["light", "dark"]


class LanguageUpdate(BaseModel):
    language: str


class NotificationsUpdate(BaseModel):
    enabled: bool
    email: Optional[bool] = None
    sms: Optional[bool] = None


class SecurityUpdate(BaseModel):
    mfa_enabled: Optional[bool] = None
    password_change_required: Optional[bool] = None
