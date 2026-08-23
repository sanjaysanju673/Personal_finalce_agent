import json
import sqlite3
from datetime import datetime, timedelta

from config.logging_config import get_logger
from config.settings import DATABASE_PATH

logger = get_logger(__name__)

DB_PATH = DATABASE_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    logger.info(f"Initializing database at {DB_PATH}")
    try:
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            schema = f.read()
        conn = get_connection()
        conn.executescript(schema)
        conn.commit()
        conn.close()
        logger.info("Database created successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise


def save_stock_data(result):
    try:
        logger.debug(f"Saving stock data for {result['symbol']}")
        conn = get_connection()
        cursor = conn.cursor()

        symbol = result["symbol"]
        company_name = result.get("company_name", "Unknown")
        sector = result.get("sector", "Unknown")
        fundamentals = result.get("fundamentals", {})
        technicals = result.get("technicals", {})
        news = result.get("news", {})
        final_score = result.get("final_score", 0)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT OR REPLACE INTO stocks
            (symbol, company_name, sector)
            VALUES (?, ?, ?)
            """,
            (symbol, company_name, sector),
        )

        cursor.execute(
            """
            INSERT INTO fundamentals
            (symbol, roe, roce, debt_equity, sales_growth, profit_growth, market_cap, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                fundamentals.get("roe", 0),
                fundamentals.get("roce", 0),
                fundamentals.get("debt_equity", 0),
                fundamentals.get("sales_growth", 0),
                fundamentals.get("profit_growth", 0),
                0,
                now,
            ),
        )

        cursor.execute(
            """
            INSERT INTO technicals
            (symbol, rsi, sma50, sma200, volume, breakout, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                technicals.get("rsi", 0),
                technicals.get("sma50", 0),
                technicals.get("sma200", 0),
                0,
                0,
                now,
            ),
        )

        cursor.execute(
            """
            INSERT INTO news
            (symbol, headline, sentiment, score, published_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                symbol,
                "Daily Analysis",
                news.get("sentiment", "Neutral"),
                news.get("news_score", 50),
                now,
            ),
        )

        cursor.execute(
            """
            INSERT INTO scores
            (symbol, fundamental_score, technical_score, news_score, final_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                result.get("fundamental_score", 0),
                result.get("technical_score", 0),
                news.get("news_score", 50),
                final_score,
                now,
            ),
        )

        conn.commit()
        logger.info(f"Successfully saved data for {symbol} to database")
        conn.close()

    except Exception as e:
        logger.error(f"Error saving stock data for {result.get('symbol','?')}: {e}", exc_info=True)
        raise


def save_scan_result(result, mode="fast"):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute(
            """
            INSERT INTO scan_runs (mode, symbol, top_n, started_at, finished_at, status, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mode,
                result.get("symbol"),
                result.get("top_n"),
                result.get("started_at", now),
                now,
                "completed",
                json.dumps({
                    "scanned_candidates": result.get("scanned_candidates", 0),
                    "top_candidates": len(result.get("top_candidates", [])),
                    "symbol": result.get("symbol"),
                }),
            ),
        )

        for candidate in result.get("top_candidates", []):
            cursor.execute(
                """
                INSERT OR REPLACE INTO stock_results
                (symbol, company_name, industry, fundamental_score, technical_score, preliminary_score,
                 report_score, news_score, risk_score, final_score, mode, source, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.get("symbol"),
                    candidate.get("company_name", ""),
                    candidate.get("industry", ""),
                    candidate.get("fundamental_score"),
                    candidate.get("technical_score"),
                    candidate.get("preliminary_score"),
                    candidate.get("report_score"),
                    candidate.get("news_score"),
                    candidate.get("risk_score"),
                    candidate.get("final_score"),
                    mode,
                    "workflow",
                    now,
                ),
            )

        conn.commit()
        logger.info("Stored market scan result for %s in DB", result.get("symbol"))
    finally:
        conn.close()


def get_latest_stock_result(symbol):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT symbol, company_name, industry, fundamental_score, technical_score,
                   preliminary_score, report_score, news_score, risk_score, final_score,
                   mode, cached_at
            FROM stock_results
            WHERE symbol = ?
            ORDER BY cached_at DESC
            LIMIT 1
            """,
            (symbol,),
        ).fetchone()
        if not row:
            return None
        keys = [
            "symbol", "company_name", "industry", "fundamental_score", "technical_score",
            "preliminary_score", "report_score", "news_score", "risk_score", "final_score",
            "mode", "cached_at",
        ]
        return dict(zip(keys, row))
    finally:
        conn.close()


def get_recent_top_candidates(top_n=20, max_age_hours=24):
    conn = get_connection()
    try:
        cutoff = (datetime.now() - timedelta(hours=max_age_hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            """
            SELECT symbol, company_name, industry, fundamental_score, technical_score,
                   preliminary_score, report_score, news_score, risk_score, final_score,
                   mode, cached_at
            FROM stock_results
            WHERE cached_at >= ?
            ORDER BY preliminary_score DESC, cached_at DESC
            LIMIT ?
            """,
            (cutoff, top_n),
        ).fetchall()
        keys = [
            "symbol", "company_name", "industry", "fundamental_score", "technical_score",
            "preliminary_score", "report_score", "news_score", "risk_score", "final_score",
            "mode", "cached_at",
        ]
        return [dict(zip(keys, row)) for row in rows]
    finally:
        conn.close()


def should_refresh_market_cache(top_n=20, max_age_hours=24):
    return len(get_recent_top_candidates(top_n=top_n, max_age_hours=max_age_hours)) == 0


initialize_database()
