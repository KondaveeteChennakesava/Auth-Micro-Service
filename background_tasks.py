"""
Background tasks for the auth microservice.
Includes periodic cleanup of expired tokens from the blacklist.
"""
import asyncio
import logging
from datetime import datetime, timezone
from database import cleanup_expired_tokens

logger = logging.getLogger(__name__)


async def cleanup_expired_tokens_task():
    """Background task to clean up expired tokens from blacklist"""
    while True:
        try:
            await asyncio.sleep(3600)

            logger.info("Running token cleanup task...")
            deleted_count = cleanup_expired_tokens()
            logger.info(
                f"Cleaned up {deleted_count} expired tokens from blacklist")

        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}", exc_info=True)
            await asyncio.sleep(60)


async def startup_cleanup():
    """Run cleanup once on startup"""
    try:
        logger.info("Running startup token cleanup...")
        deleted_count = cleanup_expired_tokens()
        logger.info(f"Startup cleanup: removed {deleted_count} expired tokens")
    except Exception as e:
        logger.error(f"Error in startup cleanup: {str(e)}", exc_info=True)
