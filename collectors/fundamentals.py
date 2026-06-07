import yfinance as yf

from config.logging_config import get_logger

logger = get_logger(__name__)


def fetch_fundamentals(symbol):

    try:

        ticker = yf.Ticker(
            f"{symbol}.NS"
        )

        info = ticker.info

        roe = info.get(
            "returnOnEquity",
            0
        )

        debt_equity = info.get(
            "debtToEquity",
            0
        )

        profit_margin = info.get(
            "profitMargins",
            0
        )

        market_cap = info.get(
            "marketCap",
            0
        )

        if roe:
            roe = roe * 100

        if profit_margin:
            profit_margin = profit_margin * 100

        return {

            "symbol": symbol,

            "roe": round(
                roe,
                2
            ),

            "roce": 0,

            "debt_equity": round(
                debt_equity,
                2
            ),

            "sales_growth": 0,

            "profit_growth": round(
                profit_margin,
                2
            ),

            "market_cap": market_cap

        }

    except Exception as e:

        logger.error(
            f"Fundamental fetch failed for {symbol}: {e}"
        )

        return None