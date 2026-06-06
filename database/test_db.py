from collectors.stock_list import (
    get_nifty500
)

df = get_nifty500()

print(df.head())

print(
    f"Total Stocks: {len(df)}"
)