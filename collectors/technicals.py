import yfinance as yf
import pandas_ta as ta
import pandas as pd
import math

def safe_last_value(series):
    """Return the last non-NaN value from a Pandas Series, or None if none exist."""
    valid = series.dropna()
    if valid.empty:
        return None
    return float(valid.iloc[-1])

def calculate_indicators(symbol):
    ticker = f"{symbol}.NS"
    df = yf.download(ticker, period="1y", progress=False)

    if df.empty:
        return None

    # Technical indicators
    df["RSI"] = ta.rsi(df["Close"], length=14)
    df["SMA50"] = ta.sma(df["Close"], length=50)
    df["SMA200"] = ta.sma(df["Close"], length=200)

    return {
        "symbol": symbol,
        "rsi": safe_last_value(df["RSI"]),
        "sma50": safe_last_value(df["SMA50"]),
        "sma200": safe_last_value(df["SMA200"]),
        "close": safe_last_value(df["Close"])
    }
