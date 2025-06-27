from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.config import setup_logger

logger = setup_logger("setup_database", indent=6)

logger.info("Creating engine, async session factory and base...")

engine = create_async_engine(url = DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False,
    class_=AsyncSession,
    bind=engine
    )

Base = declarative_base()

logger.info("Creating engine, async session factory and base...")
