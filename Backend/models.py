from sqlalchemy import (
    String, Integer, Numeric, Boolean, Date, DateTime, Text, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from typing import List, Optional
from Backend.database import Base # Adjust this import path if needed

class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    age: Mapped[Optional[int]] = mapped_column(Integer, CheckConstraint('age >= 0'))
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

    # Relationships
    accounts: Mapped[List["Account"]] = relationship(back_populates="customer", cascade="all, delete")
    users: Mapped[List["User"]] = relationship(back_populates="customer", cascade="all, delete")
    complaints: Mapped[List["Complaint"]] = relationship(back_populates="customer", cascade="all, delete")
    notifications: Mapped[List["Notification"]] = relationship(back_populates="customer", cascade="all, delete")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("customers.customer_id", ondelete="SET NULL"))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(50), default="customer", server_default="customer")

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="users")


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"))
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    account_type: Mapped[Optional[str]] = mapped_column(String(50))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    current_balance: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), default=0.00)
    account_status: Mapped[Optional[str]] = mapped_column(String(20), default="active")
    opened_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="account", cascade="all, delete")
    cards: Mapped[List["Card"]] = relationship(back_populates="account", cascade="all, delete")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    transaction_reference_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(50), ForeignKey("accounts.account_id", ondelete="CASCADE"))
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
    is_fraud_score: Mapped[Optional[int]] = mapped_column(Integer, CheckConstraint('is_fraud_score >= 0'))
    fraud_explainability_trace: Mapped[Optional[str]] = mapped_column(Text)
    merchant_category: Mapped[Optional[str]] = mapped_column(String(100))
    merchant_name: Mapped[Optional[str]] = mapped_column(String(150))
    salary_detected: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    car_loan_signal_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    recommended_product: Mapped[Optional[str]] = mapped_column(String(150))
    transaction_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="transactions")
    complaints: Mapped[List["Complaint"]] = relationship(back_populates="transaction")


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"))
    linked_transaction_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("transactions.transaction_id", ondelete="SET NULL"))
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
    complaint_narration: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="complaints")
    transaction: Mapped[Optional["Transaction"]] = relationship(back_populates="complaints")

class Card(Base):
    __tablename__ = "cards"

    card_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(50), ForeignKey("accounts.account_id", ondelete="CASCADE"))
    card_type: Mapped[Optional[str]] = mapped_column(String(20)) # e.g., Debit, Credit
    status: Mapped[Optional[str]] = mapped_column(String(20), default="active")
    card_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    expiry_date: Mapped[str] = mapped_column(String(10), nullable=False)
    cvv: Mapped[str] = mapped_column(String(4), nullable=False)
    daily_limit: Mapped[float] = mapped_column(Numeric(18, 2), default=100000.00)

    account: Mapped["Account"] = relationship(back_populates="cards")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[Optional[str]] = mapped_column(String(20), default="in-app")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="notifications")