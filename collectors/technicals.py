import yfinance as yf
import pandas_ta as ta
from config.logging_config import get_logger

logger = get_logger(__name__)

def safe_last_value(series):

    try:

        valid = series.dropna()

        if valid.empty:
            logger.debug("Series is empty, returning 0")
            return 0

        return float(valid.iloc[-1])

    except Exception as e:
        logger.debug(f"Error getting last value from series: {e}")
        return 0


def calculate_indicators(symbol):
    logger.debug(f"Calculating technical indicators for {symbol}")
    try:

        ticker = f"{symbol}.NS"

        df = yf.download(
            ticker,
            period="1y",
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            logger.warning(f"No data available for {symbol}")
            return {
                "symbol": symbol,
                "rsi": 0,
                "sma50": 0,
                "sma200": 0,
                "close": 0
            }

        logger.debug(f"Downloaded {len(df)} records for {symbol}")

        # Fix MultiIndex columns

        if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:

            df.columns = df.columns.droplevel(1)

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

        rsi_val = safe_last_value(df["RSI"])
        sma50_val = safe_last_value(df["SMA50"])
        sma200_val = safe_last_value(df["SMA200"])
        close_val = safe_last_value(df["Close"])

        logger.info(f"Technical indicators for {symbol}: RSI={rsi_val}, SMA50={sma50_val}, SMA200={sma200_val}, Close={close_val}")

        return {

            "symbol": symbol,

            "rsi": rsi_val,

            "sma50": sma50_val,

            "sma200": sma200_val,

            "close": close_val
        }

    except Exception as e:

        logger.error(
            f"Technical Error for {symbol}: {e}", exc_info=True
        )

        return {

            "symbol": symbol,

            "rsi": 0,

            "sma50": 0,

            "sma200": 0,

            "close": 0
        }