import requests
from bs4 import BeautifulSoup


def get_screener_url(symbol):

    return f"https://www.screener.in/company/{symbol}/"


def fetch_fundamentals(symbol):

    try:

        url = get_screener_url(symbol)

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        return {
            "symbol": symbol,
            "roe": None,
            "roce": None,
            "debt_equity": None,
            "sales_growth": None,
            "profit_growth": None
        }

    except Exception as e:

        print(e)

        return None