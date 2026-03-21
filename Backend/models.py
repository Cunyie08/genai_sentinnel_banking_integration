from sqlalchemy import (
    String, Integer, Numeric, Boolean, Date, DateTime,
    Text, ForeignKey, CheckConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from Backend.database import Base


# ==========================================================
# SHARED SERIALIZATION HELPER
# ==========================================================

def _safe_val(v):
    """Convert DB types that are not JSON-serializable to plain Python types."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return v


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    age: Mapped[Optional[int]] = mapped_column(Integer, CheckConstraint("age >= 0"))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    bvn: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    nin: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    telco_provider: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    state_of_origin: Mapped[Optional[str]] = mapped_column(String(100))
    residential_state: Mapped[Optional[str]] = mapped_column(String(100))
    banking_branch: Mapped[Optional[str]] = mapped_column(String(100))
    onboarding_date: Mapped[Optional[date]] = mapped_column(Date)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    password: Mapped[Optional[str]] = mapped_column(String(100))
    solo_candidate: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    accounts: Mapped[List["Account"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    otp_tokens: Mapped[List["OTPToken"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    service_transactions: Mapped[List["ServiceTransaction"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )
    fraud_alerts: Mapped[List["FraudAlert"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )

    def to_dict(self) -> dict:
        return {
            "customer_id":       self.customer_id,
            "first_name":        self.first_name,
            "last_name":         self.last_name,
            "full_name":         self.full_name,
            "gender":            self.gender,
            "age":               self.age,
            "date_of_birth":     _safe_val(self.date_of_birth),
            "bvn":               self.bvn,
            "nin":               self.nin,
            "phone_number":      self.phone_number,
            "telco_provider":    self.telco_provider,
            "email":             self.email,
            "state_of_origin":   self.state_of_origin,
            "residential_state": self.residential_state,
            "banking_branch":    self.banking_branch,
            "onboarding_date":   _safe_val(self.onboarding_date),
            "username":          self.username,
            "solo_candidate":    self.solo_candidate,
            # password intentionally excluded from to_dict
        }


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    account_type: Mapped[Optional[str]] = mapped_column(String(50))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    current_balance: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), default=0.00)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    opened_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete"
    )
    cards: Mapped[List["Card"]] = relationship(
        back_populates="account", cascade="all, delete"
    )
    service_transactions: Mapped[List["ServiceTransaction"]] = relationship(
        back_populates="account", cascade="all, delete"
    )

    def to_dict(self) -> dict:
        return {
            "account_id":      self.account_id,
            "customer_id":     self.customer_id,
            "account_number":  self.account_number,
            "account_type":    self.account_type,
            "currency":        self.currency,
            "current_balance": _safe_val(self.current_balance),
            "status":          self.status,
            "opened_date":     _safe_val(self.opened_date),
        }


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    transaction_reference_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("accounts.account_id", ondelete="CASCADE")
    )
    channel: Mapped[Optional[str]] = mapped_column(String(50))
    device_id: Mapped[Optional[str]] = mapped_column(String(100))
    counterparty_bank: Mapped[Optional[str]] = mapped_column(String(100))
    narration: Mapped[Optional[str]] = mapped_column(Text)
    transaction_type: Mapped[Optional[str]] = mapped_column(String(20))
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    transaction_balance: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    transaction_status: Mapped[Optional[str]] = mapped_column(String(50))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    is_fraud_score: Mapped[Optional[int]] = mapped_column(
        Integer, CheckConstraint("is_fraud_score >= 0")
    )
    fraud_explainability_trace: Mapped[Optional[str]] = mapped_column(Text)
    merchant_category: Mapped[Optional[str]] = mapped_column(String(100))
    merchant_name: Mapped[Optional[str]] = mapped_column(String(150))
    salary_detected: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    Loan_signal_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    recommended_product: Mapped[Optional[str]] = mapped_column(String(150))
    transaction_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="transactions")
    customer: Mapped["Customer"] = relationship(back_populates="transactions")
    complaints: Mapped[List["Complaint"]] = relationship(back_populates="transaction")

    def to_dict(self) -> dict:
        return {
            "transaction_id":               self.transaction_id,
            "transaction_reference_number": self.transaction_reference_number,
            "account_id":                   self.account_id,
            "customer_id":                  self.customer_id,
            "channel":                      self.channel,
            "device_id":                    self.device_id,
            "counterparty_bank":            self.counterparty_bank,
            "narration":                    self.narration,
            "transaction_type":             self.transaction_type,
            "amount":                       _safe_val(self.amount),
            "currency":                     self.currency,
            "transaction_balance":          _safe_val(self.transaction_balance),
            "transaction_status":           self.transaction_status,
            "failure_reason":               self.failure_reason,
            "is_fraud_score":               self.is_fraud_score,
            "fraud_explainability_trace":   self.fraud_explainability_trace,
            "merchant_category":            self.merchant_category,
            "merchant_name":                self.merchant_name,
            "salary_detected":              self.salary_detected,
            "Loan_signal_score":            _safe_val(self.Loan_signal_score),
            "recommended_product":          self.recommended_product,
            "transaction_timestamp":        _safe_val(self.transaction_timestamp),
        }
    

class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    linked_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("transactions.transaction_id", ondelete="SET NULL")
    )
    linked_reference: Mapped[Optional[str]] = mapped_column(String(50))
    department_code: Mapped[Optional[str]] = mapped_column(String(20))
    department_name: Mapped[Optional[str]] = mapped_column(String(150))
    priority_level: Mapped[Optional[str]] = mapped_column(String(20))
    sentiment: Mapped[Optional[str]] = mapped_column(String(50))
    complaint_channel: Mapped[Optional[str]] = mapped_column(String(50))
    assigned_agent_id: Mapped[Optional[str]] = mapped_column(String(50))
    complaint_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_time_hours: Mapped[Optional[int]] = mapped_column(Integer)
    sla_hours_limit: Mapped[Optional[int]] = mapped_column(Integer)
    sla_breach_flag: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    complaint_status: Mapped[Optional[str]] = mapped_column(String(50))
    fraud_related: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    complaint_text: Mapped[Optional[str]] = mapped_column(Text)
    account_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("accounts.account_id", ondelete="CASCADE")
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="complaints")
    transaction: Mapped[Optional["Transaction"]] = relationship(
        back_populates="complaints"
    )

    def to_dict(self) -> dict:
        return {
            "complaint_id":          self.complaint_id,
            "customer_id":           self.customer_id,
            "linked_transaction_id": self.linked_transaction_id,
            "linked_reference":      self.linked_reference,
            "department_code":       self.department_code,
            "department_name":       self.department_name,
            "priority_level":        self.priority_level,
            "sentiment":             self.sentiment,
            "complaint_channel":     self.complaint_channel,
            "assigned_agent_id":     self.assigned_agent_id,
            "complaint_timestamp":   _safe_val(self.complaint_timestamp),
            "resolution_timestamp":  _safe_val(self.resolution_timestamp),
            "resolution_time_hours": self.resolution_time_hours,
            "sla_hours_limit":       self.sla_hours_limit,
            "sla_breach_flag":       self.sla_breach_flag,
            "complaint_status":      self.complaint_status,
            "fraud_related":         self.fraud_related,
            "complaint_text":        self.complaint_text,
            "account_id":            self.account_id,
        }


class OTPToken(Base):
    __tablename__ = "otp_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    customer: Mapped["Customer"] = relationship(back_populates="otp_tokens")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    customer: Mapped["Customer"] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    customer: Mapped["Customer"] = relationship(back_populates="reset_tokens")


class Card(Base):
    __tablename__ = "cards"

    card_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("accounts.account_id", ondelete="CASCADE")
    )
    card_type: Mapped[str] = mapped_column(String(20), default="virtual")
    card_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    expiry_date: Mapped[str] = mapped_column(String(10), nullable=False)
    cvv: Mapped[str] = mapped_column(String(4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    daily_limit: Mapped[float] = mapped_column(Numeric(18, 2), default=100000.00)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    account: Mapped["Account"] = relationship(back_populates="cards")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(20), default="in-app")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    customer: Mapped["Customer"] = relationship(back_populates="notifications")


class UserSettings(Base):
    __tablename__ = "user_settings"

    setting_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), unique=True
    )
    theme: Mapped[str] = mapped_column(String(20), default="light")
    language: Mapped[str] = mapped_column(String(10), default="en")
    notify_transactions: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_promotions: Mapped[bool] = mapped_column(Boolean, default=True)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    customer: Mapped["Customer"] = relationship(back_populates="settings")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    customer: Mapped["Customer"] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("chat_sessions.session_id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class ServiceTransaction(Base):
    __tablename__ = "service_transactions"

    service_tx_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    account_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("accounts.account_id", ondelete="CASCADE")
    )
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    data_plan: Mapped[Optional[str]] = mapped_column(String(50))
    bill_account_number: Mapped[Optional[str]] = mapped_column(String(100))
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    customer: Mapped["Customer"] = relationship(back_populates="service_transactions")
    account: Mapped["Account"] = relationship(back_populates="service_transactions")


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    alert_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("transactions.transaction_id", ondelete="CASCADE")
    )
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE")
    )
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    decision: Mapped[Optional[str]] = mapped_column(String(20))
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    customer: Mapped["Customer"] = relationship(back_populates="fraud_alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(50))
    actor_role: Mapped[Optional[str]] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50))
    target_id: Mapped[Optional[str]] = mapped_column(String(100))
    details: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ComplaintRoutingDecision(Base):
    __tablename__ = "complaint_routing_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[Optional[str]] = mapped_column(String(50))
    department_code: Mapped[Optional[str]] = mapped_column(String(20))
    department_name: Mapped[Optional[str]] = mapped_column(String(150))
    priority_level: Mapped[Optional[str]] = mapped_column(String(20))
    sla_hours: Mapped[Optional[int]] = mapped_column(Integer)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    routing_method: Mapped[Optional[str]] = mapped_column(String(50))
    keyword_matches: Mapped[Optional[str]] = mapped_column(JSON)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    sentiment: Mapped[Optional[str]] = mapped_column(String(50))
    complaint_text: Mapped[Optional[str]] = mapped_column(Text)
    customer_id: Mapped[Optional[str]] = mapped_column(String(50))
    complaint_channel: Mapped[Optional[str]] = mapped_column(String(50))
    linked_transaction: Mapped[Optional[str]] = mapped_column(String(50))
    agent: Mapped[Optional[str]] = mapped_column(String(50))
    request_id: Mapped[Optional[str]] = mapped_column(String(50))
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    has_department: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    non_empty_reasoning: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    department_present: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)