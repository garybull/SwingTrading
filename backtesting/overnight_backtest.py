# =========================
# SAFE WARNING SUPPRESSION
# =========================
import os
os.environ["PYTHONWARNINGS"] = "ignore"

import warnings
warnings.filterwarnings("ignore")

# =========================
# IMPORTS
# =========================
import pandas as pd
import numpy as np
import pickle
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

from app.strategy import generate_signal

# =========================
# CONFIG
# =========================
START_CAPITAL = 90000

MAX_POSITIONS = 12
MAX_NEW_TRADES = 6

BASE_RISK = 0.015

PYRAMID_TRIGGER = 1.03
PYRAMID_SIZE = 0.5

ENTRY_SLIPPAGE = 0.0005
EXIT_SLIPPAGE = 0.0005

CACHE_FILE = "backtest_cache.pkl"

GLOBAL_DATA = None


# =========================
# PRECOMPUTE
# =========================
def precompute_indicators(data):
    for df in data.values():

        df["ma50"] = df["Close"].rolling(50).mean()
        df["ma20"] = df["Close"].rolling(20).mean()

        tr = pd.concat([
            df["High"] - df["Low"],
            (df["High"] - df["Close"].shift()).abs(),
            (df["Low"] - df["Close"].shift()).abs()
        ], axis=1).max(axis=1)

        df["atr"] = tr.rolling(14).mean()

    return data


def load_data():
    with open(CACHE_FILE, "rb") as f:
        return pickle.load(f)


def init_worker(data):
    global GLOBAL_DATA
    GLOBAL_DATA = data


# =========================
# SIGNAL SCAN
# =========================
def process_symbol(args):
    symbol, date, spy = args
    df = GLOBAL_DATA[symbol]

    if date not in df.index:
        return None

    idx = df.index.get_loc(date)

    if idx < 50 or idx >= len(df) - 1:
        return None

    if df["Volume"].iloc[idx] < 1_000_000:
        return None

    if df["Close"].iloc[idx] < 20:
        return None

    hist = df.iloc[:idx + 1]

    signal = generate_signal(hist, symbol, spy)

    if signal:
        signal["index"] = idx
        return signal

    return None


# =========================
# POSITION SIZE
# =========================
def calc_size(capital, entry, stop, risk_pct):
    risk_amount = capital * risk_pct
    risk_per_share = abs(entry - stop)

    if risk_per_share == 0:
        return 0

    return int(risk_amount / risk_per_share)


# =========================
# BACKTEST
# =========================
def run_backtest():

    print("🚀 Running TREND + PYRAMIDING (fixed equity)...")

    data = load_data()
    data = precompute_indicators(data)

    global GLOBAL_DATA
    GLOBAL_DATA = data

    all_dates = sorted(set().union(*[df.index for df in data.values()]))

    capital = START_CAPITAL
    positions = []
    equity_curve = []
    trades = []

    num_workers = max(4, multiprocessing.cpu_count() - 2)

    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=init_worker,
        initargs=(data,)
    ) as executor:

        for date in all_dates:

            still_open = []

            # =========================
            # UPDATE POSITIONS
            # =========================
            for pos in positions:

                df = data[pos["symbol"]]

                if date not in df.index:
                    still_open.append(pos)
                    continue

                row = df.loc[date]
                exit_price = row["Close"] * (1 - EXIT_SLIPPAGE)

                # 🔥 PYRAMID ADD
                if not pos["pyramided"]:
                    if row["Close"] >= pos["entry"] * PYRAMID_TRIGGER:

                        add_shares = int(pos["shares"] * PYRAMID_SIZE)
                        cost = add_shares * row["Close"]

                        if add_shares > 0 and cost <= capital:
                            capital -= cost
                            pos["shares"] += add_shares
                            pos["pyramided"] = True

                # trailing stop logic
                pos["highest"] = max(pos["highest"], row["Close"])

                if row["Close"] >= pos["entry"] * 1.04:
                    pos["stop"] = max(pos["stop"], pos["entry"])

                trail = pos["highest"] - (3.5 * pos["atr"])
                pos["stop"] = max(pos["stop"], trail)

                if row["Close"] <= pos["stop"]:
                    proceeds = pos["shares"] * exit_price
                    capital += proceeds

                    pnl = (exit_price - pos["entry"]) * pos["shares"]
                    trades.append(pnl)
                else:
                    still_open.append(pos)

            positions = still_open

            # =========================
            # SCAN
            # =========================
            spy = data.get("SPY")

            args = [(symbol, date, spy) for symbol in data.keys()]
            raw = executor.map(process_symbol, args, chunksize=20)

            signals = [r for r in raw if r]
            signals = sorted(signals, key=lambda x: x["score"], reverse=True)

            # =========================
            # ENTRIES
            # =========================
            for sig in signals[:MAX_NEW_TRADES]:

                if len(positions) >= MAX_POSITIONS:
                    break

                df = data[sig["symbol"]]
                idx = sig["index"]

                if idx + 1 >= len(df):
                    continue

                next_row = df.iloc[idx + 1]

                entry = next_row["Open"] * (1 + ENTRY_SLIPPAGE)
                stop = sig["stop"]

                shares = calc_size(capital, entry, stop, BASE_RISK)
                cost = shares * entry

                if shares <= 0 or cost > capital:
                    continue

                capital -= cost

                positions.append({
                    "symbol": sig["symbol"],
                    "entry": entry,
                    "stop": stop,
                    "shares": shares,
                    "entry_date": next_row.name,
                    "highest": entry,
                    "atr": sig.get("atr", 0),
                    "pyramided": False
                })

            # =========================
            # 🔥 CORRECT EQUITY CALC
            # =========================
            position_value = 0

            for pos in positions:
                df = data[pos["symbol"]]
                if date in df.index:
                    position_value += pos["shares"] * df.loc[date]["Close"]

            total_equity = capital + position_value
            equity_curve.append(total_equity)

    # =========================
    # RESULTS
    # =========================
    final = equity_curve[-1]

    years = len(all_dates) / 252
    cagr = ((final / START_CAPITAL) ** (1 / years) - 1) * 100

    wins = [t for t in trades if t > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0

    peak = -np.inf
    max_dd = 0

    for x in equity_curve:
        peak = max(peak, x)
        dd = (peak - x) / peak
        max_dd = max(max_dd, dd)

    print("\n===== TREND + PYRAMID RESULTS (FIXED) =====")
    print(f"Final Equity: {round(final, 2)}")
    print(f"CAGR: {round(cagr, 2)}%")
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {round(win_rate, 2)}%")
    print(f"Max Drawdown: {round(max_dd * 100, 2)}%")


if __name__ == "__main__":
    run_backtest()