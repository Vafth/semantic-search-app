from sqlmodel import SQLModel
from db.engine import async_engine, AsyncSessionLocal
from logging import getLogger

from repository.user import create_user, get_user_by_username
from common.schemas.internal import UserRole
from core.config import settings

from core.security import get_hash_password

logger = getLogger(__name__)


async def create_db_and_tables():
    logger.info("Running migrations...")
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Tables ready.")

    logger.info("Checking owner account...")
    async with AsyncSessionLocal() as session:

        existing = await get_user_by_username(session, settings.OWNER_USERNAME)
        if not existing:

            await create_user(session, settings.OWNER_USERNAME, get_hash_password(settings.OWNER_PASSWORD), role=UserRole.owner)
            logger.info(f"Owner account '{settings.OWNER_USERNAME}' created.")
        else:
            logger.info("Owner account already exists, skipping.")