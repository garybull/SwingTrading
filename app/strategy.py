import pandas as pd


def generate_signal(df, symbol, spy_df=None):

    if len(df) < 100:
        return None

    price = float(df["Close"].iloc[-1])
    ma50 = float(df["ma50"].iloc[-1])
    ma20 = float(df["ma20"].iloc[-1])
    atr = float(df["atr"].iloc[-1])

    if pd.isna(ma50) or pd.isna(ma20) or pd.isna(atr):
        return None

    # Trend filter
    if price < ma50 * 1.01:
        return None

    # No chase
    if price > ma20 * 1.15:
        return None

    # Pullback structure
    recent_low = df["Low"].rolling(10).min().iloc[-2]
    recent_high = df["High"].rolling(10).max().iloc[-2]

    if recent_low < ma20 * 0.98:
        return None

    pullback_pct = (recent_high - recent_low) / recent_high
    if pullback_pct > 0.12:
        return None

    # Re-acceleration
    if df["Close"].iloc[-1] <= df["Close"].iloc[-2]:
        return None

    # Relative strength
    rs_score = 1.0
    if spy_df is not None and len(spy_df) >= 50:
        spy_close = spy_df["Close"]
        stock_return = price / df["Close"].iloc[-20]
        spy_return = spy_close.iloc[-1] / spy_close.iloc[-20]

        if spy_return != 0:
            rs_score = stock_return / spy_return

    momentum_score = price / df["Close"].iloc[-5]
    trend_score = price / ma50

    score = (trend_score * 0.4) + (momentum_score * 0.3) + (rs_score * 0.3)

    entry = float(price)
    stop = float(entry - (2.2 * atr))

    return {
        "symbol": symbol,
        "entry": entry,
        "stop": stop,
        "atr": float(atr),
        "score": float(score)
    }