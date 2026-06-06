import yfinance as yf

import pandas_ta as ta


def calculate_indicators(symbol):

    ticker = f"{symbol}.NS"

    df = yf.download(
        ticker,
        period="1y",
        progress=False
    )

    if df.empty:
        return None

    df["RSI"] = ta.rsi(
        df["Close"],
        length=14
    )

    df["SMA50"] = ta.sma(
        df["Close"],
        length=50
    )

    df["SMA200"] = ta.sma(
        df["Close"],
        length=200
    )

    latest = df.iloc[-1]

    return {
        "symbol": symbol,
        "rsi": float(latest["RSI"]),
        "sma50": float(latest["SMA50"]),
        "sma200": float(latest["SMA200"]),
        "close": float(latest["Close"])
    }