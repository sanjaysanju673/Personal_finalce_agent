import sqlite3
from datetime import datetime
from config.logging_config import get_logger

logger = get_logger(__name__)

DB_PATH = "database/stock.db"


def save_stock_data(result):
    try:
        logger.debug(f"Saving stock data for {result['symbol']}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        symbol = result["symbol"]
        company_name = result["company_name"]
        fundamentals = result["fundamentals"]
        technicals = result["technicals"]
        news = result["news"]
        final_score = result["final_score"]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT OR REPLACE INTO stocks
            (
                symbol,
                company_name,
                sector
            )
            VALUES
            (?, ?, ?)
            """,
            (symbol, company_name, "Unknown")
        )

        cursor.execute(
            """
            INSERT INTO fundamentals
            (
                symbol,
                roe,
                roce,
                debt_equity,
                sales_growth,
                profit_growth,
                market_cap,
                updated_at
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                fundamentals.get("roe", 0),
                fundamentals.get("roce", 0),
                fundamentals.get("debt_equity", 0),
                fundamentals.get("sales_growth", 0),
                fundamentals.get("profit_growth", 0),
                0,
                now
            )
        )

        cursor.execute(
            """
            INSERT INTO technicals
            (
                symbol,
                rsi,
                sma50,
                sma200,
                volume,
                breakout,
                updated_at
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                technicals.get("rsi", 0),
                technicals.get("sma50", 0),
                technicals.get("sma200", 0),
                0,
                0,
                now
            )
        )

        cursor.execute(
            """
            INSERT INTO news
            (
                symbol,
                headline,
                sentiment,
                score,
                published_at
            )
            VALUES
            (?, ?, ?, ?, ?)
            """,
            (
                symbol,
                "Daily Analysis",
                news.get("sentiment", "Neutral"),
                news.get("news_score", 50),
                now
            )
        )

        cursor.execute(
            """
            INSERT INTO scores
            (
                symbol,
                fundamental_score,
                technical_score,
                news_score,
                final_score,
                updated_at
            )
            VALUES
            (?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                0,
                0,
                news.get("news_score", 50),
                final_score,
                now
            )
        )

        conn.commit()
        logger.info(f"Successfully saved data for {symbol} to database")
        conn.close()

    except Exception as e:
        logger.error(f"Error saving stock data for {result.get('symbol','?')}: {e}", exc_info=True)
        if 'conn' in locals():
            conn.close()
        raise
