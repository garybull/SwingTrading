# app/benchmark_engine.py

import pandas as pd
import numpy as np
import yfinance as yf

from app.config import (
    START_CAPITAL
)

from app.logger import logger

from app.portfolio import (
    get_equity_curve
)


# =====================================
# SETTINGS
# =====================================
BENCHMARKS = [

    "SPY",
    "QQQ",
    "TQQQ"

]


# =====================================
# LOAD BENCHMARK DATA
# =====================================
def load_benchmark_data(symbol):

    logger.info(
        f"Loading benchmark: {symbol}"
    )

    df = yf.download(

        symbol,

        period="10y",

        auto_adjust=True,

        progress=False

    )

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if df.empty:

        logger.warning(
            f"No benchmark data for "
            f"{symbol}"
        )

        return pd.DataFrame()

    return df


# =====================================
# NORMALIZE EQUITY CURVE
# =====================================
def normalize_curve(series):

    if len(series) == 0:

        return pd.Series()

    starting_value = float(
        series.iloc[0]
    )

    return (

        series
        / starting_value

    ) * START_CAPITAL


# =====================================
# MAX DRAWDOWN
# =====================================
def calculate_max_drawdown(series):

    if len(series) == 0:

        return 0

    running_max = series.cummax()

    drawdown = (

        (
            series
            - running_max
        )

        / running_max

    ) * 100

    return round(

        abs(drawdown.min()),

        2

    )


# =====================================
# CAGR
# =====================================
def calculate_cagr(series):

    if len(series) < 2:

        return 0

    start = float(
        series.iloc[0]
    )

    end = float(
        series.iloc[-1]
    )

    years = len(series) / 252

    if years <= 0:

        return 0

    cagr = (

        (
            end / start
        ) ** (

            1 / years

        ) - 1

    ) * 100

    return round(cagr, 2)


# =====================================
# SHARPE
# =====================================
def calculate_sharpe(returns):

    if len(returns) < 2:

        return 0

    std = returns.std()

    if std == 0:

        return 0

    sharpe = (

        returns.mean()

        / std

    ) * np.sqrt(252)

    return round(sharpe, 2)


# =====================================
# SORTINO
# =====================================
def calculate_sortino(returns):

    if len(returns) < 2:

        return 0

    downside = returns[
        returns < 0
    ]

    downside_std = downside.std()

    if downside_std == 0:

        return 0

    sortino = (

        returns.mean()

        / downside_std

    ) * np.sqrt(252)

    return round(sortino, 2)


# =====================================
# SYSTEM CURVE
# =====================================
def get_system_curve():

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

        return pd.DataFrame(

            columns=[

                "date",
                "equity",
                "normalized"

            ]

        )

    curve = equity_curve.copy()

    curve["normalized"] = (
        normalize_curve(
            curve["equity"]
        )
    )

    return curve


# =====================================
# BENCHMARK CURVES
# =====================================
def get_benchmark_curves():

    curves = {}

    for symbol in BENCHMARKS:

        df = load_benchmark_data(
            symbol
        )

        # =====================================
        # EMPTY SAFETY
        # =====================================
        if df.empty:

            continue

        # =====================================
        # CLOSE SERIES
        # =====================================
        close = df["Close"]

        # =====================================
        # HANDLE DATAFRAME CASE
        # =====================================
        if isinstance(
            close,
            pd.DataFrame
        ):

            close = close.iloc[:, 0]

        close = close.dropna()

        if close.empty:

            continue

        normalized = (
            normalize_curve(close)
        )

        curves[symbol] = pd.DataFrame({

            "date":
                close.index,

            "close":
                close.values,

            "normalized":
                normalized.values

        })

    return curves


# =====================================
# BENCHMARK REPORT
# =====================================
def get_benchmark_report():

    report = {

        "SYSTEM": {

            "final_equity": 0,
            "cagr": 0,
            "max_drawdown": 0,
            "sharpe": 0,
            "sortino": 0

        },

        "SPY": {

            "final_equity": 0,
            "cagr": 0,
            "max_drawdown": 0,
            "sharpe": 0,
            "sortino": 0

        },

        "QQQ": {

            "final_equity": 0,
            "cagr": 0,
            "max_drawdown": 0,
            "sharpe": 0,
            "sortino": 0

        },

        "TQQQ": {

            "final_equity": 0,
            "cagr": 0,
            "max_drawdown": 0,
            "sharpe": 0,
            "sortino": 0

        }

    }

    # =====================================
    # SYSTEM METRICS
    # =====================================
    system_curve = (
        get_system_curve()
    )

    if not system_curve.empty:

        equity = system_curve[
            "normalized"
        ]

        returns = (
            equity.pct_change()
            .dropna()
        )

        report["SYSTEM"] = {

            "final_equity":

                round(
                    float(
                        equity.iloc[-1]
                    ),
                    2
                ),

            "cagr":

                calculate_cagr(
                    equity
                ),

            "max_drawdown":

                calculate_max_drawdown(
                    equity
                ),

            "sharpe":

                calculate_sharpe(
                    returns
                ),

            "sortino":

                calculate_sortino(
                    returns
                )

        }

    # =====================================
    # BENCHMARK METRICS
    # =====================================
    benchmark_curves = (
        get_benchmark_curves()
    )

    for symbol, curve in benchmark_curves.items():

        equity = curve[
            "normalized"
        ]

        returns = (
            equity.pct_change()
            .dropna()
        )

        report[symbol] = {

            "final_equity":

                round(
                    float(
                        equity.iloc[-1]
                    ),
                    2
                ),

            "cagr":

                calculate_cagr(
                    equity
                ),

            "max_drawdown":

                calculate_max_drawdown(
                    equity
                ),

            "sharpe":

                calculate_sharpe(
                    returns
                ),

            "sortino":

                calculate_sortino(
                    returns
                )

        }

    logger.info(
        "Benchmark report built"
    )

    return report


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    report = (
        get_benchmark_report()
    )

    print(
        "\n===== BENCHMARK REPORT =====\n"
    )

    for symbol, stats in report.items():

        print(f"\n{symbol}")

        for k, v in stats.items():

            print(f"{k}: {v}")