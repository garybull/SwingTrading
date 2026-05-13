# app/rolling_analytics.py

import pandas as pd
import numpy as np

from app.portfolio import (
    get_equity_curve
)

from app.logger import logger


# =====================================
# SHARPE
# =====================================
def calculate_sharpe(
    returns
):

    if returns.std() == 0:

        return 0

    return (

        returns.mean()

        / returns.std()

    ) * np.sqrt(252)


# =====================================
# BUILD ROLLING ANALYTICS
# =====================================
def get_rolling_analytics():

    logger.info(
        "Building rolling analytics..."
    )

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

    equity_curve["returns"] = (

        equity_curve["equity"]
        .pct_change()

    )

    # =====================================
    # ROLLING METRICS
    # =====================================
    equity_curve["rolling_30d_return"] = (

        equity_curve["equity"]

        .pct_change(30)

    ) * 100

    equity_curve["rolling_volatility"] = (

        equity_curve["returns"]

        .rolling(30)

        .std()

    ) * np.sqrt(252) * 100

    equity_curve["rolling_sharpe"] = (

        equity_curve["returns"]

        .rolling(30)

        .apply(calculate_sharpe)

    )

    # =====================================
    # ROLLING DRAWDOWN
    # =====================================
    rolling_max = (

        equity_curve["equity"]
        .cummax()

    )

    equity_curve["rolling_drawdown"] = (

        (
            equity_curve["equity"]
            / rolling_max
        )

        - 1

    ) * 100

    logger.info(
        "Rolling analytics complete"
    )

    return equity_curve