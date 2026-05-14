# app/strategy.py
import pandas as pd


# =========================
# SAFE SCALAR
# =========================
def safe_scalar(x):

    if isinstance(x, pd.Series):
        return float(x.iloc[-1])

    return float(x)


# =========================
# SCORE ASSET
# =========================
def score_asset(df, symbol):

    # =========================
    # VALIDATION
    # =========================
    if df is None or len(df) < 200:
        return None

    try:

        close = safe_scalar(
            df["Close"].iloc[-1]
        )

        ma50 = safe_scalar(
            df["Close"]
            .rolling(50)
            .mean()
            .iloc[-1]
        )

        ma200 = safe_scalar(
            df["Close"]
            .rolling(200)
            .mean()
            .iloc[-1]
        )

    except:
        return None

    # =========================
    # TREND FILTER
    # =========================
    if not (
        close > ma50 > ma200
    ):
        return None

    # =========================
    # MOMENTUM
    # =========================
    mom_1m = (
        close
        / safe_scalar(
            df["Close"].iloc[-21]
        )
    ) - 1

    mom_3m = (
        close
        / safe_scalar(
            df["Close"].iloc[-63]
        )
    ) - 1

    mom_6m = (
        close
        / safe_scalar(
            df["Close"].iloc[-126]
        )
    ) - 1

    # =========================
    # VOLATILITY
    # =========================
    returns = (
        df["Close"]
        .pct_change()
        .dropna()
    )

    volatility = safe_scalar(
        returns.iloc[-63:].std()
    )

    if volatility <= 0:
        return None

    # =========================
    # COMPOSITE SCORE
    # =========================
    score = (
        (mom_1m * 0.2)
        + (mom_3m * 0.4)
        + (mom_6m * 0.4)
    )

    # Risk-adjusted
    score = score / volatility

    return {

        "symbol": symbol,

        "score": score,

        "close": close,

        "mom_1m": mom_1m,

        "mom_3m": mom_3m,

        "mom_6m": mom_6m,

        "volatility": volatility

    }