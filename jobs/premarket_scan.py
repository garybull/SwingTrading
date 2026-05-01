import sqlite3
import pandas as pd
import numpy as np
import pickle

from app.strategy import generate_signal

# =========================
# CONFIG
# =========================
DB_PATH = "trading_system.db"
CACHE_FILE = "backtest_cache.pkl"

START_CAPITAL = 90000
BASE_RISK = 0.015

MAX_RESULTS = 10          # 🔥 focus on best trades
MAX_POSITION_PCT = 0.20   # 🔥 cap any one position at 20%


# =========================
# LOAD DATA
# =========================
import yfinance as yf

UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "META", "TSLA", "AMD", "AVGO", "NFLX"
]

def load_data():
    data = {}

    for symbol in UNIVERSE:
        df = yf.download(symbol, period="6mo", interval="1d", auto_adjust=True, progress=False)

        # 🔥 FIX: flatten multi-index if present
        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)

        if df is not None and not df.empty:
            data[symbol] = df

    return data


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
# WEIGHTS (PRIORITIZATION)
# =========================
def compute_weights(signals):
    scores = np.array([s["score"] for s in signals])

    if len(scores) == 0:
        return []

    mean = np.mean(scores)
    std = np.std(scores) if np.std(scores) > 0 else 1

    weights = []

    for s in signals:
        z = (s["score"] - mean) / std
        weight = 1 + (z * 0.25)

        # clamp range
        weight = max(0.5, min(1.5, weight))

        weights.append(weight)

    return weights


# =========================
# DEDUPE (FIXED)
# =========================
def dedupe(signals):
    seen = set()
    result = []

    for s in signals:
        sym = s["symbol"]

        # normalize duplicates
        if sym in ["GOOG", "GOOGL"]:
            key = "GOOG"
        else:
            key = sym

        if key in seen:
            continue

        seen.add(key)
        result.append(s)

    return result


# =========================
# WRITE RESULTS
# =========================
def write_results(results):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DELETE FROM scan_results")

    for r in results:
        c.execute("""
            INSERT INTO scan_results
            (symbol, score, entry_price, stop_price, target_price, strong, shares, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["symbol"],
            r["score"],
            r["entry"],
            r["stop"],
            r["target"],
            r["strong"],
            r["shares"],
            r["weight"]
        ))

    conn.commit()
    conn.close()


# =========================
# MAIN SCAN
# =========================
def run(return_results=False):

    print("🚀 Running premarket scan...")

    data = load_data()
    signals = []

    # =========================
    # GENERATE SIGNALS
    # =========================
    for symbol, df in data.items():

        if len(df) < 100:
            continue

        df = df.copy()

        # indicators (must match strategy)
        df["ma50"] = df["Close"].rolling(50).mean()
        df["ma20"] = df["Close"].rolling(20).mean()

        tr = pd.concat([
            df["High"] - df["Low"],
            (df["High"] - df["Close"].shift()).abs(),
            (df["Low"] - df["Close"].shift()).abs()
        ], axis=1).max(axis=1)

        df["atr"] = tr.rolling(14).mean()

        # no lookahead
        sig = generate_signal(df.iloc[:-1], symbol, None)

        if sig:
            last = df.iloc[-1]

            signals.append({
                "symbol": symbol,
                "score": float(sig["score"]),
                "entry": float(last["Close"]),
                "stop": float(sig["stop"]),
                "target": float(last["Close"] * 1.08),
                "strong": False
            })

    # =========================
    # CLEAN + SORT
    # =========================
    signals = dedupe(signals)
    signals = sorted(signals, key=lambda x: x["score"], reverse=True)[:MAX_RESULTS]

    weights = compute_weights(signals)

    # =========================
    # CAPITAL DEPLOYMENT (FIXED)
    # =========================
    capital = START_CAPITAL
    results = []

    for sig, w in zip(signals, weights):

        entry = sig["entry"]
        stop = sig["stop"]

        # risk-based sizing
        shares = calc_size(capital, entry, stop, BASE_RISK * w)

        if shares <= 0:
            continue

        cost = shares * entry

        # 🔥 POSITION CAP (IMPORTANT)
        max_allowed = capital * MAX_POSITION_PCT

        if cost > max_allowed:
            shares = int(max_allowed / entry)
            cost = shares * entry

        if shares <= 0 or cost > capital:
            continue

        capital -= cost

        results.append({
            "symbol": sig["symbol"],
            "score": round(sig["score"], 2),
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "target": round(sig["target"], 2),
            "strong": sig["strong"],
            "shares": shares,
            "weight": round(w, 2)
        })

    # =========================
    # SAVE
    # =========================
    write_results(results)

    print(f"✅ Scan complete — {len(results)} trades saved")
    print(f"💰 Remaining capital: {round(capital, 2)}")

    if return_results:
        return results