from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.settings import DATABASE_URL

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in settings")


engine = create_async_engine(DATABASE_URL, echo=False)


SessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as db:
        yield db