# app/regime_engine.py

import pandas as pd

from app.logger import logger

from app.market_data_service import (
    get_historical_data,
    get_live_price
)


# =====================================
# SETTINGS
# =====================================
SPY_SYMBOL = "SPY"

QQQ_SYMBOL = "QQQ"

LOOKBACK = 200


# =====================================
# SAFE CLOSE SERIES
# =====================================
def get_close_series(df):

    close_series = df["Close"]

    # =====================================
    # HANDLE DATAFRAME CASE
    # =====================================
    if isinstance(

        close_series,

        pd.DataFrame

    ):

        close_series = (
            close_series.iloc[:, 0]
        )

    return close_series.dropna()


# =====================================
# CALCULATE TREND
# =====================================
def calculate_trend(df):

    close_series = (
        get_close_series(df)
    )

    # =====================================
    # SAFETY
    # =====================================
    if len(close_series) < LOOKBACK:

        logger.warning(
            "Not enough history "
            "for trend calculation"
        )

        return {

            "close": 0,

            "sma_200": 0,

            "above_200dma": False

        }

    latest_close = float(
        close_series.iloc[-1]
    )

    sma_200 = float(

        close_series

        .rolling(LOOKBACK)

        .mean()

        .iloc[-1]

    )

    return {

        "close":
            latest_close,

        "sma_200":
            sma_200,

        "above_200dma":

            latest_close > sma_200

    }


# =====================================
# GET VIX
# =====================================
def get_vix():

    vix_price = get_live_price(
        "^VIX"
    )

    return round(vix_price, 2)


# =====================================
# DETERMINE MARKET REGIME
# =====================================
def determine_market_regime():

    logger.info(
        "Determining market regime..."
    )

    # =====================================
    # LOAD DATA
    # =====================================
    spy_df = get_historical_data(
        SPY_SYMBOL
    )

    qqq_df = get_historical_data(
        QQQ_SYMBOL
    )

    # =====================================
    # SAFETY
    # =====================================
    if spy_df is None or spy_df.empty:

        logger.error(
            "SPY data unavailable"
        )

        return {

            "regime": "UNKNOWN"

        }

    if qqq_df is None or qqq_df.empty:

        logger.error(
            "QQQ data unavailable"
        )

        return {

            "regime": "UNKNOWN"

        }

    # =====================================
    # TREND CALCULATIONS
    # =====================================
    spy_trend = calculate_trend(
        spy_df
    )

    qqq_trend = calculate_trend(
        qqq_df
    )

    # =====================================
    # VIX
    # =====================================
    vix = get_vix()

    # =====================================
    # RULES
    # MATCH BACKTEST EXACTLY
    # =====================================
    risk_on = (
        spy_trend["above_200dma"]
    )

    regime = (

        "RISK_ON"

        if risk_on

        else "RISK_OFF"

    )

    logger.info(

        f"Regime: {regime} | "
        f"SPY Above 200DMA: "
        f"{spy_trend['above_200dma']}"

    )

    return {

        "regime":
            regime,

        "vix":
            vix,

        "spy_close":
            round(
                spy_trend["close"],
                2
            ),

        "spy_200dma":
            round(
                spy_trend["sma_200"],
                2
            ),

        "qqq_close":
            round(
                qqq_trend["close"],
                2
            ),

        "qqq_200dma":
            round(
                qqq_trend["sma_200"],
                2
            ),

        "spy_above_200dma":
            spy_trend[
                "above_200dma"
            ],

        "qqq_above_200dma":
            qqq_trend[
                "above_200dma"
            ]

    }


# =====================================
# SUGGESTED EXPOSURE
# ANALYTICS ONLY
# =====================================
def get_suggested_exposure():

    regime_data = (
        determine_market_regime()
    )

    vix = float(
        regime_data["vix"]
    )

    if regime_data["regime"] != "RISK_ON":

        return {

            "suggested_exposure": 0,

            "label":
                "Risk Off",

            "reason":
                "Risk-off regime"

        }

    # =====================================
    # VIX BASED SCALING
    # =====================================
    if vix < 18:

        exposure = 95

        label = "Maximum"

        reason = (
            "Low volatility regime"
        )

    elif vix < 25:

        exposure = 75

        label = "Moderate"

        reason = (
            "Elevated volatility"
        )

    elif vix < 35:

        exposure = 50

        label = "Defensive"

        reason = (
            "High volatility"
        )

    else:

        exposure = 0

        label = "Extreme Risk"

        reason = (
            "Extreme volatility"
        )

    return {

        "suggested_exposure":
            exposure,

        "label":
            label,

        "reason":
            reason,

        "vix":
            vix

    }

# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    regime = determine_market_regime()

    print("\n===== MARKET REGIME =====\n")

    for k, v in regime.items():

        print(f"{k}: {v}")