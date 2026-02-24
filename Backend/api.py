from fastapi import FastAPI, Depends, HTTPException, status, Body, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta, timezone
from typing import Annotated
from Backend.middleware import get_current_user

import sys
import asyncio
import json
import os
import uuid
import bcrypt
import secrets
import string

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from Backend.database import engine, get_db, Base
from Backend.models import (
    User,
    Customer,
    Account,
    Transaction,
    Complaint,
    OTPToken,
    RefreshToken,
    PasswordResetToken,
)
from Backend.schemas import (
    UserCreate,
    UserResponse,
    Token,
    UserLogin,
    RegisterResponse,
    OTPVerifyRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
)
from Backend.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    verify_password,
)
from Backend.email import send_otp_email, send_password_reset_email
import uvicorn

router = APIRouter(tags=["Authentication"])


def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks a plain password against the hashed version."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def generate_otp(length: int = 6) -> str:
    """Generates a random numeric OTP code."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


@router.post("/auth/register", response_model=RegisterResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        stmt_user = select(User).filter(User.email == user.email)
        result_user = await db.execute(stmt_user)
        db_user = result_user.scalars().first()

        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        stmt_customer = select(Customer).filter(Customer.email == user.email)
        result_customer = await db.execute(stmt_customer)
        db_customer = result_customer.scalars().first()

        if not db_customer:
            raise HTTPException(
                status_code=403,
                detail="No bank account found with this email. You need to open a bank account first.",
            )

        hashed_pw = get_password_hash(user.password)

        new_user = User(
            user_id=f"USR-{uuid.uuid4().hex[:10].upper()}",
            email=user.email,
            password_hash=hashed_pw,
            customer_id=db_customer.customer_id,
            is_active=False,  # User is inactive until OTP verified
        )

        db.add(new_user)

        # Generate and Send OTP
        otp_code = generate_otp()
        otp_token = OTPToken(
            user_id=new_user.user_id,
            otp_code=otp_code,
            purpose="registration",
            expires_at=datetime.now() + timedelta(minutes=15),
        )
        db.add(otp_token)

        await db.commit()
        await db.refresh(new_user)

        await send_otp_email(to_email=user.email, otp_code=otp_code)

        return {
            "message": "User registered successfully. Please verify your email with the OTP sent.",
            "user_id": new_user.user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).filter(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active. Please verify your OTP.",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Optional: Generate Refresh Token and store in DB here if implementing rotation

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/verify-otp")
async def verify_otp(request: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).filter(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt_otp = select(OTPToken).filter(
        OTPToken.user_id == user.user_id,
        OTPToken.otp_code == request.otp_code,
        OTPToken.purpose == request.purpose,
        OTPToken.is_used == False,
        OTPToken.expires_at > datetime.now(),
    )
    result_otp = await db.execute(stmt_otp)
    otp = result_otp.scalars().first()

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp.is_used = True

    if request.purpose == "registration":
        user.is_active = True

    await db.commit()

    return {"message": "OTP verified successfully"}


@router.post("/auth/resend-otp")
async def resend_otp(
    email: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)
):
    stmt = select(User).filter(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_code = generate_otp()
    otp_token = OTPToken(
        user_id=user.user_id,
        otp_code=otp_code,
        purpose="registration",  # Assuming resend for registration
        expires_at=datetime.now() + timedelta(minutes=15),
    )
    db.add(otp_token)
    await db.commit()

    await send_otp_email(to_email=email, otp_code=otp_code)

    return {"message": "A new OTP has been sent."}


@router.post("/auth/forgot-password")
async def forgot_password(
    request: PasswordResetRequest, db: AsyncSession = Depends(get_db)
):
    stmt = select(User).filter(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user:
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.user_id,
            token=token,
            expires_at=datetime.now() + timedelta(minutes=15),
        )
        db.add(reset_token)
        await db.commit()

        reset_link = f"https://sentinel-bank.com/reset-password?token={token}"
        await send_password_reset_email(to_email=request.email, reset_link=reset_link)

    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/auth/reset-password")
async def reset_password(
    request: PasswordResetConfirm, db: AsyncSession = Depends(get_db)
):
    stmt_token = select(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.now(),
    )
    result_token = await db.execute(stmt_token)
    reset_token = result_token.scalars().first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    stmt_user = select(User).filter(User.user_id == reset_token.user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalars().first()

    user.password_hash = get_password_hash(request.new_password)
    reset_token.is_used = True

    await db.commit()
    return {"message": "Password reset successfully"}


@router.patch("/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    # current_user from middleware might be a dict or model, ensure it's the User model or fetch it
    stmt = select(User).filter(User.email == current_user.get("sub"))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    user.password_hash = get_password_hash(request.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/auth/logout")
async def logout(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    # If using DB-backed refresh tokens, revoke them here
    # Example:
    # stmt = delete(RefreshToken).where(RefreshToken.user_id == current_user.get("user_id"))
    # await db.execute(stmt)
    # await db.commit()
    return {"message": "Logged out successfully (tokens should be cleared on client)"}


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Refresh the access token. (Sliding Session)
    """
    username = current_user.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
