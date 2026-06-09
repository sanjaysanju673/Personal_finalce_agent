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

        revenue_growth = info.get(
            "revenueGrowth",
            0
        )

        earnings_growth = info.get(
            "earningsGrowth",
            0
        )

        current_ratio = info.get(
            "currentRatio",
            0
        )

        market_cap = info.get(
            "marketCap",
            0
        )

        # Convert decimals to %

        roe = round(
            roe * 100,
            2
        ) if roe else 0

        profit_margin = round(
            profit_margin * 100,
            2
        ) if profit_margin else 0

        revenue_growth = round(
            revenue_growth * 100,
            2
        ) if revenue_growth else 0

        earnings_growth = round(
            earnings_growth * 100,
            2
        ) if earnings_growth else 0

        # -------------------------
        # Derived fields for
        # ReportAgent compatibility
        # -------------------------

        debt_trend = (
            "decreasing"
            if debt_equity <= 1
            else "increasing"
        )

        cash_flow = (
            "strong"
            if current_ratio >= 1.5
            else "weak"
        )

        management_sentiment = (
            "positive"
            if (
                revenue_growth >= 10 and
                profit_margin >= 10
            )
            else "neutral"
        )

        return {

            "symbol": symbol,

            "roe": roe,

            "debt_equity": round(
                debt_equity,
                2
            ),

            "profit_growth": profit_margin,

            "revenue_growth": revenue_growth,

            "eps_growth": earnings_growth,

            "current_ratio": round(
                current_ratio,
                2
            ),

            "market_cap": market_cap,

            # For Report Agent

            "debt_trend": debt_trend,

            "cash_flow": cash_flow,

            "management_sentiment":
                management_sentiment

        }

    except Exception as e:

        logger.error(
            f"Fundamental fetch failed for {symbol}: {e}"
        )

        return None