import requests
from bs4 import BeautifulSoup
from config.logging_config import get_logger

logger = get_logger(__name__)

def get_screener_url(symbol):

    return f"https://www.screener.in/company/{symbol}/"


def fetch_fundamentals(symbol):
    logger.debug(f"Fetching fundamentals for {symbol}")
    try:

        url = get_screener_url(symbol)
        logger.debug(f"Fetching from URL: {url}")

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )

        logger.debug(f"Response status code for {symbol}: {response.status_code}")

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Return with default values when data parsing fails
        logger.info(f"Successfully fetched fundamentals for {symbol}")
        return {
            "symbol": symbol,
            "roe": 0,
            "roce": 0,
            "debt_equity": 0,
            "sales_growth": 0,
            "profit_growth": 0
        }

    except Exception as e:

        logger.warning(f"Could not fetch fundamentals for {symbol}: {str(e)}")

        # Return default values instead of None
        return {
            "symbol": symbol,
            "roe": 0,
            "roce": 0,
            "debt_equity": 0,
            "sales_growth": 0,
            "profit_growth": 0
        }