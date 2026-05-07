import yfinance as yf
import pandas as pd

from app.strategy import generate_signal

symbols = ["AAPL", "MSFT", "NVDA", "AMD", "META", "TSLA"]


def load_data(symbol):
    df = yf.download(
        symbol,
        period="1y",   # 🔥 FIX: must be >= 200 days
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.astype(float)

    # Indicators
    df["ma50"] = df["Close"].rolling(50).mean()

    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"] - df["Close"].shift()).abs()
    ], axis=1).max(axis=1)

    df["atr"] = tr.rolling(14).mean()

    return df


def main():

    print("\n🔍 DEBUGGING SIGNALS\n")

    # Load SPY
    spy_df = yf.download(
        "SPY",
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if isinstance(spy_df.columns, pd.MultiIndex):
        spy_df.columns = spy_df.columns.get_level_values(0)

    spy_df = spy_df.astype(float)

    for symbol in symbols:
        print(f"\n===== {symbol} =====")

        df = load_data(symbol)

        if df is None or len(df) < 200:
            print("❌ Not enough data")
            continue

        # 🔥 ALIGN SPY TO STOCK (CRITICAL FIX)
        aligned_spy = spy_df.reindex(df.index).ffill()

        sig = generate_signal(df.iloc[:-1], symbol, aligned_spy, debug=True)

        print("RESULT:", sig)
        print("-" * 50)


if __name__ == "__main__":
    main()