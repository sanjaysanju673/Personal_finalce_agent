import sqlite3
from config.logging_config import get_logger

logger = get_logger(__name__)

DATABASE_PATH = "database/stock.db"

logger.info(f"Initializing database at {DATABASE_PATH}")

try:
    with open(
        "database/schema.sql",
        "r"
    ) as f:
        schema = f.read()
    logger.debug("Schema file read successfully")

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.executescript(schema)

    conn.commit()

    conn.close()

    logger.info(
        "Database created successfully."
    )
except Exception as e:
    logger.error(f"Error initializing database: {e}", exc_info=True)
    raise