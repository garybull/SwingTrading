import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

from app.strategy import calculate_indicators, generate_signal
from app.portfolio import calculate_position_size


START_BALANCE = 90000
MAX_POSITIONS = 5


def get_sp500_symbols():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = pd.read_csv(url)
    return [s.replace(".", "-") for s in df["Symbol"].tolist()]


def get_data(symbol):
    df = yf.download(symbol, period="10y", interval="1d", auto_adjust=True)

    if df is None or len(df) < 200:
        return None

    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df = calculate_indicators(df)
    df = df.dropna()

    return df


def backtest():
    symbols = get_sp500_symbols()
    symbols = symbols[:100]  # limit for runtime

    print(f"Testing {len(symbols)} symbols...")

    data = {}

    for s in symbols:
        df = get_data(s)
        if df is not None:
            data[s] = df

    # get all trading dates
    all_dates = sorted(set(date for df in data.values() for date in df.index))

    # randomly sample 50 dates
    test_dates = sorted(random.sample(all_dates, 50))

    balance = START_BALANCE
    positions = []
    trade_log = []

    for date in test_dates:
        print(f"\nProcessing {date.date()} | Balance: {round(balance,2)}")

        # check exits first
        new_positions = []

        for pos in positions:
            df = data[pos["symbol"]]

            if date not in df.index:
                new_positions.append(pos)
                continue

            row = df.loc[date]

            # stop hit
            if row["Low"] <= pos["stop"]:
                exit_price = pos["stop"]
                pnl = (exit_price - pos["entry"]) * pos["shares"]
                balance += pnl

                trade_log.append(pnl)
                continue

            # target hit
            if row["High"] >= pos["target"]:
                exit_price = pos["target"]
                pnl = (exit_price - pos["entry"]) * pos["shares"]
                balance += pnl

                trade_log.append(pnl)
                continue

            new_positions.append(pos)

        positions = new_positions

        # open new trades
        if len(positions) < MAX_POSITIONS:
            candidates = []

            for symbol, df in data.items():
                if date not in df.index:
                    continue

                subset = df[df.index <= date]

                signal = generate_signal(subset)

                if signal and signal["strong"]:
                    signal["symbol"] = symbol
                    candidates.append(signal)

            candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

            for c in candidates:
                if len(positions) >= MAX_POSITIONS:
                    break

                shares = calculate_position_size(c["entry"], c["stop"], balance)

                if shares == 0:
                    continue

                positions.append({
                    "symbol": c["symbol"],
                    "entry": c["entry"],
                    "stop": c["stop"],
                    "target": c["target"],
                    "shares": shares
                })

    total_pnl = sum(trade_log)

    print("\n===== RESULTS =====")
    print(f"Final Balance: {round(balance,2)}")
    print(f"Total PnL: {round(total_pnl,2)}")
    print(f"Trades: {len(trade_log)}")

    if trade_log:
        print(f"Win Rate: {round(sum(1 for x in trade_log if x > 0)/len(trade_log)*100,2)}%")


if __name__ == "__main__":
    backtest()