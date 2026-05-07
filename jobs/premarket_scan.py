import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
import json
import time

from app.strategy import generate_signal
from app.data import get_sp500_symbols

# =========================
# CONFIG
# =========================
DB_PATH = "trading_system.db"

START_CAPITAL = 90000
BASE_RISK = 0.015

MAX_RESULTS = 10
MAX_POSITION_PCT = 0.20

UNIVERSE = get_sp500_symbols()


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
# WEIGHTS
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
        weight = max(0.5, min(1.5, weight))
        weights.append(weight)

    return weights


# =========================
# WRITE RESULTS
# =========================
def write_results(results):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DELETE FROM signals WHERE status = 'PENDING'")

    for r in results:
        c.execute("""
            INSERT INTO signals (
                symbol,
                score,
                entry,
                stop,
                target,
                shares,
                weight,
                status,
                setup,
                reasons
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
        """, (
            r["symbol"],
            r["score"],
            r["entry"],
            r["stop"],
            r["target"],
            r["shares"],
            r["weight"],
            r.get("setup", "Unknown"),
            json.dumps(r.get("reasons", []))
        ))

    conn.commit()
    conn.close()


# =========================
# LOAD DATA (WITH PROGRESS)
# =========================
def load_data(symbols, progress_callback=None):
    data = {}

    total = len(symbols)

    for idx, symbol in enumerate(symbols, start=1):

        # 🔥 PROGRESS DURING DOWNLOAD (THIS WAS MISSING)
        if progress_callback:
            progress_callback(f"Loading {symbol}", idx, total)

        try:
            # retry once (network flakiness)
            for attempt in range(2):
                try:
                    df = yf.download(
                        symbol,
                        period="1y",
                        interval="1d",
                        auto_adjust=True,
                        progress=False
                    )
                    break
                except Exception:
                    if attempt == 1:
                        raise
                    time.sleep(0.3)

            if df is None or df.empty or len(df) < 200:
                continue

            # flatten columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]

            # remove duplicates
            df = df.loc[:, ~df.columns.duplicated()]

            required = ["Open", "High", "Low", "Close"]
            if not all(col in df.columns for col in required):
                continue

            df = df[required].apply(pd.to_numeric, errors="coerce").dropna()

            if len(df) < 200:
                continue

            # indicators
            df["ma50"] = df["Close"].rolling(50).mean()
            df["ma20"] = df["Close"].rolling(20).mean()

            tr = pd.concat([
                df["High"] - df["Low"],
                (df["High"] - df["Close"].shift()).abs(),
                (df["Low"] - df["Close"].shift()).abs()
            ], axis=1).max(axis=1)

            df["atr"] = tr.rolling(14).mean()

            df = df.dropna()

            if len(df) < 200:
                continue

            data[symbol] = df

        except Exception as e:
            print(f"⚠️ Error loading {symbol}: {e}")

    return data


# =========================
# MAIN SCAN
# =========================
def run(return_results=False, progress_callback=None):

    print("🚀 Running premarket scan...")

    # Load SPY
    spy_df = yf.download(
        "SPY",
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if isinstance(spy_df.columns, pd.MultiIndex):
        spy_df.columns = [col[0] for col in spy_df.columns]

    spy_df = spy_df.astype(float)

    # 🔥 PASS CALLBACK INTO LOAD
    data = load_data(UNIVERSE, progress_callback=progress_callback)

    if progress_callback:
        progress_callback("Analyzing signals...", 0, 1)

    signals = []

    total = len(data)

    for idx, (symbol, df) in enumerate(data.items(), start=1):

        # progress during signal generation
        if progress_callback:
            progress_callback(f"Analyzing {symbol}", idx, total)

        aligned_spy = spy_df.reindex(df.index).ffill()

        sig = generate_signal(df.iloc[:-1], symbol, aligned_spy)

        if sig:
            last = df.iloc[-1]

            signals.append({
                "symbol": symbol,
                "score": float(sig["score"]),
                "entry": float(last["Close"]),
                "stop": float(sig["stop"]),
                "target": float(last["Close"] * 1.08),
                "strong": False,
                "setup": sig.get("setup", "Unknown"),
                "reasons": sig.get("reasons", [])
            })

    # rank + limit
    signals = sorted(signals, key=lambda x: x["score"], reverse=True)[:MAX_RESULTS]

    weights = compute_weights(signals)

    capital = START_CAPITAL
    results = []

    for sig, w in zip(signals, weights):

        entry = sig["entry"]
        stop = sig["stop"]

        shares = calc_size(capital, entry, stop, BASE_RISK * w)

        if shares <= 0:
            continue

        cost = shares * entry
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
            "weight": round(w, 2),
            "setup": sig["setup"],
            "reasons": sig["reasons"]
        })

    write_results(results)

    print(f"✅ Scan complete — {len(results)} trades saved")
    print(f"💰 Remaining capital: {round(capital, 2)}")

    if return_results:
        return results