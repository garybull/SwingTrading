import random
import pandas as pd
import numpy as np
import yfinance as yf

from app.strategy import generate_signal
from app.position_sizing import calculate_position_size


# =========================
# CONFIG
# =========================
START_CAPITAL = 90000
MAX_POSITIONS = 10
RISK_PER_TRADE = 0.01

SYMBOLS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "GOOGL"]  # keep small for speed


# =========================
# DATA FETCH
# =========================
def get_data(symbol):
    df = yf.download(symbol, period="10y", interval="1d", auto_adjust=True)

    if df is None or len(df) < 100:
        return None

    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]]

    return df


# =========================
# BACKTEST
# =========================
def run_backtest():
    data = {}

    for s in SYMBOLS:
        df = get_data(s)
        if df is not None:
            data[s] = df

    all_dates = sorted(set().union(*[df.index for df in data.values()]))

    capital = START_CAPITAL
    equity_curve = []
    open_positions = []
    trades = []

    for date in all_dates:

        # =========================
        # UPDATE OPEN POSITIONS
        # =========================
        still_open = []

        for pos in open_positions:
            symbol = pos["symbol"]
            df = data[symbol]

            if date not in df.index:
                still_open.append(pos)
                continue

            row = df.loc[date]

            # STOP HIT
            if row["Low"] <= pos["stop"]:
                pnl = (pos["stop"] - pos["entry"]) * pos["shares"]
                capital += pnl
                trades.append(pnl)
                continue

            # TARGET HIT
            if row["High"] >= pos["target"]:
                pnl = (pos["target"] - pos["entry"]) * pos["shares"]
                capital += pnl
                trades.append(pnl)
                continue

            still_open.append(pos)

        open_positions = still_open

        # =========================
        # SCAN FOR NEW TRADES
        # =========================
        signals = []

        for symbol, df in data.items():
            if date not in df.index:
                continue

            idx = df.index.get_loc(date)

            if idx < 50:
                continue

            hist = df.iloc[:idx].copy()

            signal = generate_signal(hist, symbol)

            if signal:
                signals.append(signal)

        # =========================
        # SORT & TAKE TOP N
        # =========================
        signals = sorted(signals, key=lambda x: x["score"], reverse=True)
        signals = signals[:MAX_POSITIONS]

        # =========================
        # ENTER NEW POSITIONS
        # =========================
        for sig in signals:

            if len(open_positions) >= MAX_POSITIONS:
                break

            entry = sig["entry"]
            stop = sig["stop"]
            target = sig["target"]

            atr = (target - entry) / 3

            shares, value = calculate_position_size(
                capital,
                entry,
                stop,
                atr
            )

            if shares <= 0:
                continue

            open_positions.append({
                "symbol": sig["symbol"],
                "entry": entry,
                "stop": stop,
                "target": target,
                "shares": shares
            })

        equity_curve.append(capital)

    # =========================
    # RESULTS
    # =========================
    total_return = (capital - START_CAPITAL) / START_CAPITAL * 100

    wins = [t for t in trades if t > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0

    # drawdown
    peak = -np.inf
    max_dd = 0

    for x in equity_curve:
        peak = max(peak, x)
        dd = (peak - x) / peak
        max_dd = max(max_dd, dd)

    print("\n===== FINAL RESULTS =====")
    print(f"Final Equity: {round(capital, 2)}")
    print(f"Total Return: {round(total_return, 2)}%")
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {round(win_rate, 2)}%")
    print(f"Max Drawdown: {round(max_dd * 100, 2)}%")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_backtest()