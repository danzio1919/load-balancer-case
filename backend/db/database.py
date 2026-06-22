import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from core.config import settings

db_url = settings.DATABASE_URL
if "sqlite" in db_url:
    path_str = db_url.split(":///")[1] if ":///" in db_url else ""
    if path_str:
        db_path = Path(path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as db:
        yield db
