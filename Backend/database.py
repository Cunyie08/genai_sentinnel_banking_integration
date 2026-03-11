from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.settings import DATABASE_URL
from app.data.db_connections import get_engine

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in settings")


engine = get_engine(echo=False)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

class CustomBase:
    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

Base = declarative_base(cls=CustomBase)


async def get_db():
    async with SessionLocal() as db:
        yield db
