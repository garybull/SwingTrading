import pandas as pd


def safe_scalar(x):
    if isinstance(x, pd.Series):
        return float(x.iloc[-1])
    return float(x)


def generate_signal(df, symbol, spy_df=None):

    # =========================
    # VALIDATION
    # =========================
    if df is None or len(df) < 200:
        return None

    if spy_df is None or len(spy_df) < 200:
        return None

    try:
        price = safe_scalar(df["Close"].iloc[-1])
        ma50 = safe_scalar(df["ma50"].iloc[-1])
        ma200 = safe_scalar(df["Close"].rolling(200).mean().iloc[-1])
        atr = safe_scalar(df["atr"].iloc[-1])
    except:
        return None

    if not all(map(pd.notna, [price, ma50, ma200, atr])):
        return None

    # =========================
    # TREND FILTER (STRONG)
    # =========================
    if not (price > ma50 > ma200):
        return None

    # =========================
    # RELATIVE STRENGTH vs SPY
    # =========================
    spy_close = spy_df["Close"]

    if len(spy_close) < len(df):
        spy_close = spy_close.reindex(df.index).ffill()

    # 20-day RS
    rs_20 = (price / df["Close"].iloc[-20]) / (
        spy_close.iloc[-1] / spy_close.iloc[-20]
    )

    # 60-day RS
    rs_60 = (price / df["Close"].iloc[-60]) / (
        spy_close.iloc[-1] / spy_close.iloc[-60]
    )

    if pd.isna(rs_20) or pd.isna(rs_60):
        return None

    # Require outperformance
    if rs_20 < 1.05 or rs_60 < 1.10:
        return None

    # =========================
    # MOMENTUM QUALITY
    # =========================
    # Avoid parabolic moves
    extension = price / ma50

    if extension > 1.20:
        return None

    # Avoid weak drift
    momentum = price / df["Close"].iloc[-20]

    if momentum < 1.05:
        return None

    # =========================
    # STRUCTURE (NOT FALLING APART)
    # =========================
    recent_low = df["Low"].rolling(10).min().iloc[-1]

    if price < recent_low * 1.03:
        return None

    # =========================
    # SCORE (KEY)
    # =========================
    score = (rs_20 * 0.4) + (rs_60 * 0.4) + (momentum * 0.2)

    # =========================
    # TRADE LEVELS
    # =========================
    entry = float(price)
    stop = float(entry - (2.5 * atr))

    return {
        "symbol": symbol,
        "entry": entry,
        "stop": stop,
        "atr": float(atr),
        "score": float(score),
        "rs_20": float(rs_20),
        "rs_60": float(rs_60)
    }