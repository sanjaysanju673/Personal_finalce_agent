import pandas as pd

NIFTY_500_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

def get_nifty500():

    df = pd.read_csv(NIFTY_500_URL)

    return df[[
        "Symbol",
        "Company Name",
        "Industry"
    ]]