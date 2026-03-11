from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from Backend.auth import verify_access_token
from Backend.database import get_db
from Backend.models import Customer

oauth2_scheme = HTTPBearer()

async def get_current_user(
    token: HTTPAuthorizationCredentials = Security(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """FastAPI Dependency to protect routes and fetch the user."""
    payload = verify_access_token(token.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing the subject (email)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(Customer).filter(Customer.email == email)
    result = await db.execute(stmt)
    customer = result.scalars().first()

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user belonging to this token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return customer