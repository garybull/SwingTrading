import pandas as pd
import ssl
import certifi
import urllib.request
import yfinance as yf


def get_sp500_symbols():
    import pandas as pd

    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

    df = pd.read_csv(url)

    if df.empty:
        raise ValueError("Failed to load S&P 500 symbols")

    symbols = df["Symbol"].tolist()
    symbols = [s.replace(".", "-") for s in symbols]

    return symbols

def get_data(symbol):
    df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True)

    if df is None or len(df) < 200:
        return None

    # 🔥 CRITICAL FIX: flatten columns if multi-index
    if isinstance(df.columns, tuple) or hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    # Ensure proper column names
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    return df