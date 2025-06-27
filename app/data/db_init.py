from app.data.models import *
from app.data.database import Base, engine
from app.config import setup_logger

logger = setup_logger("init_database", indent=6)

async def init_db():
    logger.info("Initializing database")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

async def main():
    logger.info("Starting database initialization")
    await init_db()
    logger.info("Database initialization complete")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())