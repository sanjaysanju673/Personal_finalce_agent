import pandas as pd
from config.logging_config import get_logger

logger = get_logger(__name__)

NIFTY_500_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

def get_nifty500():
    logger.info(f"Fetching Nifty 500 stock list from {NIFTY_500_URL}")
    try:
        df = pd.read_csv(NIFTY_500_URL)
        selected_df = df[[
            "Symbol",
            "Company Name",
            "Industry"
        ]]
        logger.info(f"Successfully loaded {len(selected_df)} stocks from Nifty 500")
        return selected_df
    except Exception as e:
        logger.error(f"Error fetching Nifty 500 list: {e}", exc_info=True)
        raise