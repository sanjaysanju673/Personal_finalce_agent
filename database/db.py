import sqlite3
from config.settings import DATABASE_PATH
from config.logging_config import get_logger

logger = get_logger(__name__)

def get_connection():
    logger.debug(f"Establishing database connection to {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        logger.debug("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}", exc_info=True)
        raise
