import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.logging_config import get_logger

logger = get_logger(__name__)

DATABASE_PATH = "database/stock.db"

logger.info(f"Initializing database at {DATABASE_PATH}")

try:
    with open(ROOT / "database" / "schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    logger.debug("Schema file read successfully")

    conn = sqlite3.connect(ROOT / DATABASE_PATH)

    conn.executescript(schema)

    conn.commit()

    conn.close()

    logger.info("Database created successfully.")
except Exception as e:
    logger.error(f"Error initializing database: {e}", exc_info=True)
    raise