# app/chart_engine.py

import json

import pandas as pd
import yfinance as yf

import plotly
import plotly.graph_objects as go

from app.logger import logger


# =====================================
# ATR
# =====================================
def calculate_atr(
    df,
    period=14
):

    high_low = (
        df["High"]
        - df["Low"]
    )

    high_close = abs(
        df["High"]
        - df["Close"].shift()
    )

    low_close = abs(
        df["Low"]
        - df["Close"].shift()
    )

    ranges = pd.concat([

        high_low,
        high_close,
        low_close

    ], axis=1)

    true_range = ranges.max(
        axis=1
    )

    atr = (

        true_range
        .rolling(period)
        .mean()

    )

    return atr


# =====================================
# BUILD RECOMMENDATION CHART
# =====================================
def build_recommendation_chart(
    symbol
):

    logger.info(
        f"Building chart for {symbol}"
    )

    # =====================================
    # DOWNLOAD DATA
    # =====================================
    df = yf.download(

        symbol,

        period="14d",

        interval="1h",

        auto_adjust=True,

        progress=False,

        threads=False

    )

    if df.empty:

        return {}

    df = df.dropna()

    # =====================================
    # REGULAR MARKET HOURS ONLY
    # =====================================
    df = df.between_time(

        "09:30",

        "16:00"

    )

    if df.empty:

        return {}

    # =====================================
    # EMA20
    # =====================================
    df["EMA20"] = (

        df["Close"]

        .squeeze()

        .ewm(span=20)

        .mean()

    )

    # =====================================
    # ATR
    # =====================================
    df["ATR"] = calculate_atr(
        df
    )

    # =====================================
    # CURRENT LEVELS
    # =====================================
    current_price = float(

        df["Close"]

        .squeeze()

        .iloc[-1]

    )

    atr = float(

        df["ATR"]

        .iloc[-1]

    )

    stop_price = round(

        current_price
        - (2 * atr),

        2

    )

    target_1 = round(

        current_price
        + (2 * atr),

        2

    )

    target_2 = round(

        current_price
        + (4 * atr),

        2

    )

    # =====================================
    # RISK / REWARD
    # =====================================
    risk_pct = round(

        (
            (
                current_price
                - stop_price
            )

            / current_price

        ) * 100,

        2

    )

    reward_pct = round(

        (
            (
                target_2
                - current_price
            )

            / current_price

        ) * 100,

        2

    )

    if risk_pct > 0:

        rr_ratio = round(

            reward_pct
            / risk_pct,

            2

        )

    else:

        rr_ratio = 0

    # =====================================
    # FIGURE
    # =====================================
    fig = go.Figure()

    # =====================================
    # PRICE LINE
    # =====================================
    fig.add_trace(

        go.Scatter(

            x=df.index,

            y=df["Close"].squeeze(),

            mode="lines",

            name=symbol,

            line=dict(
                width=3
            )

        )

    )
    # =====================================
    # EMA20
    # =====================================
    fig.add_trace(

        go.Scatter(

            x=df.index,

            y=df["EMA20"].squeeze(),

            mode="lines",

            name="EMA20",

            line=dict(
                width=2,
                dash="dot"
            )

        )

    )

    # =====================================
    # ENTRY LINE
    # =====================================
    fig.add_hline(

        y=current_price,

        annotation_text=(
            f"ENTRY ${round(current_price,2)}"
        )

    )

    # =====================================
    # STOP LINE
    # =====================================
    fig.add_hline(

        y=stop_price,

        line_dash="dash",

        annotation_text=(
            f"STOP ${stop_price}"
        )

    )

    # =====================================
    # AUTO ZOOM
    # =====================================
    if len(df.index) > 80:

        start_idx = df.index[-80]

    else:

        start_idx = df.index[0]

    end_idx = df.index[-1]

    fig.update_xaxes(

        range=[
            start_idx,
            end_idx
        ]

    )

    # =====================================
    # LAYOUT
    # =====================================
    fig.update_layout(

        title=(
            f"{symbol} Hourly Setup"
        ),

        template="plotly_dark",

        height=700,

        hovermode="x unified",

        xaxis_rangeslider_visible=False,

        showlegend=True

    )

    chart_json = json.dumps(

        fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )

    logger.info(
        f"Chart complete for {symbol}"
    )

    return {

        "symbol": symbol,

        "chart": chart_json,

        "entry": round(
            current_price,
            2
        ),

        "stop": stop_price,

        "target_1": target_1,

        "target_2": target_2,

        "risk_pct": risk_pct,

        "reward_pct": reward_pct,

        "rr_ratio": rr_ratio

    }