from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select 
from fastapi import HTTPException, status

from app.settings import SECRET_KEY
from Backend.models import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    """Verify a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") 
        if email is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticate a user against the database."""
    stmt = select(User).filter(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        return False
    
    if not verify_password(password, user.password_hash):
        return False
    
    return user