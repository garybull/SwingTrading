# app/benchmark_engine.py

import pandas as pd
import numpy as np

from app.portfolio import (
    get_equity_curve
)

from app.logger import logger

from app.market_data_service import (
    get_historical_data
)


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

    logger.info(
        "Building system curve..."
    )

    equity_curve = (
        get_equity_curve()
    )

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if equity_curve.empty:

        logger.warning(
            "No equity curve found"
        )

        return pd.DataFrame()

    equity_curve = (
        equity_curve.copy()
    )

    equity_curve["date"] = pd.to_datetime(

        equity_curve["date"]

    )

    equity_curve = equity_curve.sort_values(
        "date"
    )

    starting_equity = float(

        equity_curve.iloc[0][
            "equity"
        ]

    )

    # =====================================
    # SAFETY
    # =====================================
    if starting_equity <= 0:

        logger.warning(
            "Invalid starting equity"
        )

        return pd.DataFrame()

    equity_curve["normalized"] = (

        equity_curve["equity"]

        / starting_equity

    ) * STARTING_CAPITAL

    logger.info(
        "System curve built"
    )

    return equity_curve


# =====================================
# BUILD BENCHMARK CURVES
# =====================================
def get_benchmark_curves():

    logger.info(
        "Building benchmark curves..."
    )

    benchmark_curves = {}

    # =====================================
    # SYMBOL LOOP
    # =====================================
    for symbol in BENCHMARKS:

        logger.info(
            f"Loading {symbol}"
        )

        df = get_historical_data(
            symbol
        )

        # =====================================
        # EMPTY SAFETY
        # =====================================
        if df is None:

            logger.warning(

                f"No benchmark data "
                f"for {symbol}"

            )

            continue

        if df.empty:

            continue

        # =====================================
        # CLOSE SERIES
        # =====================================
        close = (
            df["Close"]
            .dropna()
        )

        if len(close) == 0:

            continue

        starting_price = float(
            close.iloc[0]
        )

        # =====================================
        # SAFETY
        # =====================================
        if starting_price <= 0:

            continue

        normalized = (

            close
            / starting_price

        ) * STARTING_CAPITAL

        benchmark_curves[
            symbol
        ] = normalized

    logger.info(
        "Benchmark curves built"
    )

    return benchmark_curves


# =====================================
# METRICS
# =====================================
def calculate_metrics(
    equity_series
):

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if equity_series is None:

        return {}

    if len(equity_series) < 2:

        return {}

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
    # SYSTEM METRICS
    # =====================================
    if not system_curve.empty:

        report["SYSTEM"] = (

            calculate_metrics(

                system_curve[
                    "normalized"
                ]

            )

        )

    # =====================================
    # BENCHMARK METRICS
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

        "report":
            report,

        "system_curve":
            system_curve,

        "benchmark_curves":
            benchmark_curves

    }