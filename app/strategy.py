import pandas as pd


def safe_scalar(x):
    if isinstance(x, pd.Series):
        return float(x.iloc[-1])
    return float(x)


def generate_signal(df, symbol, spy_df=None):

    if len(df) < 100:
        return None

    try:
        price = safe_scalar(df["Close"].iloc[-1])
        ma50 = safe_scalar(df["ma50"].iloc[-1])
        ma20 = safe_scalar(df["ma20"].iloc[-1])
        atr = safe_scalar(df["atr"].iloc[-1])
    except:
        return None

    if not all(map(pd.notna, [price, ma50, ma20, atr])):
        return None

    # Trend filter
    if price < ma50 * 1.01:
        return None

    # No chase
    if price > ma20 * 1.15:
        return None

    # Pullback
    recent_low = df["Low"].rolling(10).min().iloc[-2]
    recent_high = df["High"].rolling(10).max().iloc[-2]

    if pd.isna(recent_low) or pd.isna(recent_high):
        return None

    if recent_low < ma20 * 0.98:
        return None

    pullback_pct = (recent_high - recent_low) / recent_high
    if pullback_pct > 0.12:
        return None

    # Re-acceleration
    if df["Close"].iloc[-1] <= df["Close"].iloc[-2]:
        return None

    # Scoring
    momentum_score = price / df["Close"].iloc[-5]
    trend_score = price / ma50

    score = (trend_score * 0.4) + (momentum_score * 0.3) + 0.3

    entry = float(price)
    stop = float(entry - (2.2 * atr))

    return {
        "symbol": symbol,
        "entry": entry,
        "stop": stop,
        "atr": float(atr),
        "score": float(score)
    }