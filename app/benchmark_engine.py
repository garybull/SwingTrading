# app/benchmark_engine.py

import pandas as pd
import numpy as np
import yfinance as yf

from app.portfolio import (
    get_equity_curve
)

from app.logger import logger


# =====================================
# SETTINGS
# =====================================
BENCHMARKS = [

    "SPY",
    "QQQ",
    "TQQQ"

]

STARTING_CAPITAL = 100000


# =====================================
# CAGR
# =====================================
def calculate_cagr(

    starting_value,

    ending_value,

    years

):

    if years <= 0:

        return 0

    return (

        (
            ending_value
            / starting_value
        ) ** (1 / years)

        - 1

    ) * 100


# =====================================
# MAX DRAWDOWN
# =====================================
def calculate_max_drawdown(
    series
):

    rolling_max = (
        series.cummax()
    )

    drawdown = (

        series
        / rolling_max

        - 1

    )

    return abs(
        drawdown.min()
    ) * 100


# =====================================
# SHARPE
# =====================================
def calculate_sharpe(
    returns
):

    if returns.std() == 0:

        return 0

    sharpe = (

        returns.mean()
        / returns.std()

    ) * np.sqrt(252)

    return sharpe


# =====================================
# SORTINO
# =====================================
def calculate_sortino(
    returns
):

    downside = returns[
        returns < 0
    ]

    if downside.std() == 0:

        return 0

    sortino = (

        returns.mean()
        / downside.std()

    ) * np.sqrt(252)

    return sortino


# =====================================
# BUILD SYSTEM CURVE
# =====================================
def get_system_curve():

    equity_curve = (
        get_equity_curve()
    )

    if equity_curve.empty:

        return pd.DataFrame()

    equity_curve["date"] = pd.to_datetime(

        equity_curve["date"]

    )

    equity_curve = equity_curve.sort_values(
        "date"
    )

    equity_curve["normalized"] = (

        equity_curve["equity"]

        / equity_curve.iloc[0]["equity"]

    ) * STARTING_CAPITAL

    return equity_curve


# =====================================
# DOWNLOAD BENCHMARKS
# =====================================
def get_benchmark_curves():

    logger.info(
        "Downloading benchmarks..."
    )

    data = yf.download(

        BENCHMARKS,

        start="2010-01-01",

        auto_adjust=True,

        progress=False

    )

    close = data["Close"]

    benchmark_curves = {}

    for symbol in BENCHMARKS:

        series = close[
            symbol
        ].dropna()

        normalized = (

            series
            / series.iloc[0]

        ) * STARTING_CAPITAL

        benchmark_curves[
            symbol
        ] = normalized

    logger.info(
        "Benchmarks downloaded"
    )

    return benchmark_curves


# =====================================
# METRICS
# =====================================
def calculate_metrics(
    equity_series
):

    returns = (
        equity_series
        .pct_change()
        .dropna()
    )

    starting = float(
        equity_series.iloc[0]
    )

    ending = float(
        equity_series.iloc[-1]
    )

    years = (
        len(equity_series)
        / 252
    )

    metrics = {

        "final_equity":
            round(ending, 2),

        "cagr":
            round(

                calculate_cagr(
                    starting,
                    ending,
                    years
                ),

                2

            ),

        "max_drawdown":
            round(

                calculate_max_drawdown(
                    equity_series
                ),

                2

            ),

        "sharpe":
            round(

                calculate_sharpe(
                    returns
                ),

                2

            ),

        "sortino":
            round(

                calculate_sortino(
                    returns
                ),

                2

            )

    }

    return metrics


# =====================================
# FULL BENCHMARK REPORT
# =====================================
def get_benchmark_report():

    logger.info(
        "Building benchmark report..."
    )

    system_curve = (
        get_system_curve()
    )

    benchmark_curves = (
        get_benchmark_curves()
    )

    report = {}

    # =====================================
    # SYSTEM
    # =====================================
    report["SYSTEM"] = (

        calculate_metrics(

            system_curve[
                "normalized"
            ]

        )

    )

    # =====================================
    # BENCHMARKS
    # =====================================
    for symbol, curve in benchmark_curves.items():

        report[symbol] = (

            calculate_metrics(
                curve
            )

        )

    logger.info(
        "Benchmark report complete"
    )

    return {

        "report": report,

        "system_curve":
            system_curve,

        "benchmark_curves":
            benchmark_curves

    }