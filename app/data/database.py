"""
database.py

Initializes the asynchronous SQLAlchemy database engine, session factory, and declarative base
for the application. Provides the AsyncSessionLocal for use throughout the app and sets up
logging for all database connection and session creation events.

Key features:
- Creates an async SQLAlchemy engine using the DATABASE_URL from configuration.
- Provides AsyncSessionLocal for dependency injection in async workflows.
- Defines the declarative Base for model definitions.
- Logs all major setup steps for observability.

Dependencies:
- SQLAlchemy (async engine, session, declarative base)
- app.config (for DATABASE_URL and logger setup)
"""

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
