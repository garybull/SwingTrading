import pandas as pd


def safe_scalar(x):
    if isinstance(x, pd.Series):
        return float(x.iloc[-1])
    return float(x)


def generate_signal(df, symbol, spy_df=None, debug=False):

    if df is None or len(df) < 200:
        if debug: print(f"{symbol}: FAIL - not enough data")
        return None

    if spy_df is None or len(spy_df) < 200:
        if debug: print(f"{symbol}: FAIL - no SPY")
        return None

    try:
        price = float(df["Close"].iloc[-1])
        ma50 = float(df["ma50"].iloc[-1])
        ma200 = float(df["Close"].rolling(200).mean().iloc[-1])
        atr = float(df["atr"].iloc[-1])
    except:
        if debug: print(f"{symbol}: FAIL - indicator error")
        return None

    if not all(pd.notna([price, ma50, ma200, atr])):
        if debug: print(f"{symbol}: FAIL - NaN values")
        return None

    reasons = []
    setup = "Trend Continuation"

    # =========================
    # TREND FILTER
    # =========================
    if not (price > ma50 > ma200):
        if debug: print(f"{symbol}: FAIL - trend")
        return None
    else:
        reasons.append("Strong uptrend (Price > 50MA > 200MA)")

    # =========================
    # ALIGN SPY
    # =========================
    spy_close = spy_df["Close"].reindex(df.index).ffill()

    try:
        rs_20 = (price / df["Close"].iloc[-20]) / (
            spy_close.iloc[-1] / spy_close.iloc[-20]
        )
        rs_60 = (price / df["Close"].iloc[-60]) / (
            spy_close.iloc[-1] / spy_close.iloc[-60]
        )
    except:
        if debug: print(f"{symbol}: FAIL - RS calc error")
        return None

    if pd.isna(rs_20) or pd.isna(rs_60):
        if debug: print(f"{symbol}: FAIL - RS NaN")
        return None

    if rs_20 < 1.05 or rs_60 < 1.10:
        if debug: print(f"{symbol}: FAIL - RS too low ({rs_20:.2f}, {rs_60:.2f})")
        return None
    else:
        reasons.append(f"Relative strength strong (20d: {rs_20:.2f}, 60d: {rs_60:.2f})")

    # =========================
    # EXTENSION FILTER
    # =========================
    extension = price / ma50
    if extension > 1.20:
        if debug: print(f"{symbol}: FAIL - too extended")
        return None
    else:
        reasons.append(f"Not overextended ({extension:.2f} vs 50MA)")

    # =========================
    # MOMENTUM
    # =========================
    momentum = price / df["Close"].iloc[-20]
    if momentum < 1.05:
        if debug: print(f"{symbol}: FAIL - weak momentum")
        return None
    else:
        reasons.append(f"Momentum confirmed (+{(momentum - 1)*100:.1f}% / 20d)")

    # =========================
    # STRUCTURE
    # =========================
    recent_low = df["Low"].rolling(10).min().iloc[-1]
    if price < recent_low * 1.03:
        if debug: print(f"{symbol}: FAIL - weak structure")
        return None
    else:
        reasons.append("Strong price structure (holding above recent lows)")

    # =========================
    # SCORE
    # =========================
    score = (rs_20 * 0.4) + (rs_60 * 0.4) + (momentum * 0.2)

    # =========================
    # RISK MODEL
    # =========================
    entry = price
    stop = entry - (2.5 * atr)

    reasons.append(f"ATR-based stop ({round(2.5 * atr, 2)} risk per share)")

    if debug:
        print(f"{symbol}: ✅ PASS | Score: {round(score,2)}")

    return {
        "symbol": symbol,
        "entry": entry,
        "stop": stop,
        "atr": atr,
        "score": score,
        "rs_20": rs_20,
        "rs_60": rs_60,
        "reasons": reasons,   # 🔥 NEW
        "setup": setup        # 🔥 NEW
    }