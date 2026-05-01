import os
os.environ["PYTHONWARNINGS"] = "ignore"

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from app.strategy import generate_signal

CACHE_FILE = "backtest_cache.pkl"

# =========================
# LOAD + PRECOMPUTE
# =========================
def load_data():
    with open(CACHE_FILE, "rb") as f:
        return pickle.load(f)

def precompute(data):
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

# =========================
# CORE BACKTEST (PARAM DRIVEN)
# =========================
def run_single_test(params):

    data = GLOBAL_DATA

    START_CAPITAL = 90000
    BASE_RISK = 0.015
    MAX_POSITIONS = 12
    MAX_NEW_TRADES = 6

    ATR_TRIGGER = params["atr_trigger"]
    LOW = params["low"]
    MID = params["mid"]
    HIGH = params["high"]

    capital = START_CAPITAL
    positions = []
    equity_curve = []
    trades = []

    all_dates = GLOBAL_DATES

    for i in range(51, len(all_dates) - 1):

        date = all_dates[i]
        next_date = all_dates[i + 1]

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

            pos["highest"] = max(pos["highest"], row["Close"])

            if row["Close"] >= pos["entry"] * 1.04:
                pos["stop"] = max(pos["stop"], pos["entry"])

            trail = pos["highest"] - (3.5 * pos["atr"])
            pos["stop"] = max(pos["stop"], trail)

            if row["Close"] <= pos["stop"]:
                capital += pos["shares"] * row["Close"]
                trades.append(1 if row["Close"] > pos["entry"] else 0)
            else:
                still_open.append(pos)

        positions = still_open

        # =========================
        # EQUITY
        # =========================
        pos_val = 0
        for pos in positions:
            df = data[pos["symbol"]]
            if date in df.index:
                pos_val += pos["shares"] * df.loc[date]["Close"]

        equity_curve.append(capital + pos_val)

        # =========================
        # PYRAMID
        # =========================
        pyramid_orders = []

        for pos in positions:

            if pos["pyramided"]:
                continue

            df = data[pos["symbol"]]
            if date not in df.index:
                continue

            row = df.loc[date]

            if row["Close"] <= df["ma20"].loc[date]:
                continue

            if row["Close"] >= pos["entry"] + (ATR_TRIGGER * pos["atr"]):
                pyramid_orders.append(pos)

        for pos in pyramid_orders:

            df = data[pos["symbol"]]
            idx = df.index.get_loc(date)

            if idx + 1 >= len(df):
                continue

            next_row = df.iloc[idx + 1]
            if next_row.name != next_date:
                continue

            atr_pct = pos["atr"] / pos["entry"]

            if atr_pct < 0.02:
                scale = LOW
            elif atr_pct < 0.04:
                scale = MID
            else:
                scale = HIGH

            add = int(pos["initial_shares"] * scale)
            cost = add * next_row["Open"]

            if add > 0 and cost <= capital:
                capital -= cost
                pos["shares"] += add
                pos["pyramided"] = True

        # =========================
        # SIGNALS
        # =========================
        signals = []

        for symbol, df in data.items():

            if date not in df.index:
                continue

            idx = df.index.get_loc(date)

            if idx < 50 or idx >= len(df) - 1:
                continue

            hist = df.iloc[:idx]

            sig = generate_signal(hist, symbol, None)

            if sig:
                sig["index"] = idx
                signals.append(sig)

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

            if next_row.name != next_date:
                continue

            entry = next_row["Open"]
            stop = sig["stop"]

            risk = capital * BASE_RISK
            per_share = abs(entry - stop)

            if per_share == 0:
                continue

            shares = int(risk / per_share)
            cost = shares * entry

            if shares <= 0 or cost > capital:
                continue

            capital -= cost

            positions.append({
                "symbol": sig["symbol"],
                "entry": entry,
                "stop": stop,
                "shares": shares,
                "initial_shares": shares,
                "highest": entry,
                "atr": sig.get("atr", 0),
                "pyramided": False
            })

    # =========================
    # RESULTS
    # =========================
    final = equity_curve[-1]

    years = len(equity_curve) / 252
    cagr = ((final / START_CAPITAL) ** (1 / years) - 1) * 100

    peak = -np.inf
    max_dd = 0
    for x in equity_curve:
        peak = max(peak, x)
        dd = (peak - x) / peak
        max_dd = max(max_dd, dd)

    return {
        "atr": ATR_TRIGGER,
        "low": LOW,
        "mid": MID,
        "high": HIGH,
        "final": round(final, 2),
        "cagr": round(cagr, 2),
        "max_dd": round(max_dd * 100, 2)
    }


# =========================
# GLOBAL INIT
# =========================
def init_globals(data, dates):
    global GLOBAL_DATA, GLOBAL_DATES
    GLOBAL_DATA = data
    GLOBAL_DATES = dates


# =========================
# MAIN OPTIMIZER
# =========================
def run_optimizer():

    print("🚀 Starting optimization engine...")

    data = load_data()
    data = precompute(data)

    dates = sorted(set().union(*[df.index for df in data.values()]))

    # PARAM GRID
    atr_values = [0.75, 1.0, 1.25]

    sizing_sets = [
        {"low":0.5, "mid":0.35, "high":0.2},     # conservative
        {"low":0.75, "mid":0.5, "high":0.25},    # balanced
        {"low":1.0, "mid":0.7, "high":0.4},      # aggressive
    ]

    tests = []

    for atr in atr_values:
        for s in sizing_sets:
            tests.append({
                "atr_trigger": atr,
                "low": s["low"],
                "mid": s["mid"],
                "high": s["high"]
            })

    results = []

    workers = max(4, multiprocessing.cpu_count() - 2)

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=init_globals,
        initargs=(data, dates)
    ) as executor:

        futures = [executor.submit(run_single_test, t) for t in tests]

        for f in as_completed(futures):
            res = f.result()
            print(res)
            results.append(res)

    df = pd.DataFrame(results)

    df = df.sort_values(by="cagr", ascending=False)

    print("\n===== FINAL RANKED RESULTS =====")
    print(df)

    df.to_csv("optimization_results.csv", index=False)


if __name__ == "__main__":
    run_optimizer()