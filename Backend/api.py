from fastapi import FastAPI, Depends, HTTPException, status, Body, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import Annotated
from Backend.middleware import get_current_user

import sys
import asyncio
import json
import os
import uuid
import bcrypt

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from Backend.database import engine, get_db, Base
from Backend.models import User, Customer, Account, Transaction, Complaint 
from Backend.schemas import UserCreate, UserResponse, Token, UserLogin, RegisterResponse
from Backend.auth import authenticate_user, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, verify_password
import uvicorn

# Initialize DB Tables
# Base.metadata.create_all(bind=engine)

router = APIRouter(tags=["Authentication"])



def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    # bcrypt requires bytes, so we encode the string
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    # decode back to string to store in the database (VARCHAR)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks a plain password against the hashed version."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )



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
                detail="No bank account found with this email. You need to open a bank account first."
            )

        hashed_pw = get_password_hash(user.password)

        new_user = User(
            user_id=f"USR-{uuid.uuid4().hex[:10].upper()}",
            email=user.email,
            password_hash=hashed_pw, 
            customer_id=db_customer.customer_id 
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {
            "message": "User registered successfully", 
            "user_id": new_user.user_id
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
    db: AsyncSession = Depends(get_db)
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
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/auth/refresh", response_model=Token)
def refresh_token(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Refresh the access token.
    Uses the existing valid access token to generate a new one (Sliding Session).
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

@router.post("/auth/forgot-password")
def forgot_password(email: str = Body(..., embed=True)):
    print(f"Password reset requested for {email}")
    return {"message": "If the email exists, a reset link has been sent."}




