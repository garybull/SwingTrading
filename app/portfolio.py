# app/portfolio.py

import pandas as pd

from app.live_portfolio import (
    get_live_portfolio
)

from app.logger import logger

from app.pnl_engine import (
    get_pnl_summary
)

from app.db_service import (
    query_df
)

from app.risk_engine import (
    get_risk_report
)

risk_report = (
    get_risk_report()
)


# =====================================
# SYSTEM STATE
# =====================================
def get_system_state():

    query = """

        SELECT *

        FROM system_state

        LIMIT 1

    """

    df = query_df(query)

    if df.empty:

        return {

            "market_regime": "UNKNOWN",

            "current_leader": "",

            "current_equity": 0,

            "current_cash": 0,

            "next_rebalance_date": "",

            "last_rebalance_date": ""

        }

    return df.iloc[0].to_dict()


# =====================================
# RANKINGS
# =====================================
def get_rankings(limit=25):

    query = f"""

        SELECT *

        FROM rankings

        ORDER BY rank ASC

        LIMIT {limit}

    """

    return query_df(query)


# =====================================
# REBALANCE HISTORY
# =====================================
def get_rebalance_history(limit=100):

    query = f"""

        SELECT *

        FROM rebalance_log

        ORDER BY id DESC

        LIMIT {limit}

    """

    return query_df(query)


# =====================================
# EXECUTED TRADES
# =====================================
def get_executed_trades(limit=100):

    query = f"""

        SELECT

            id,
            date,
            symbol,
            side,
            shares,
            fill_price,
            total_value,
            notes

        FROM executed_trades

        ORDER BY id DESC

        LIMIT {limit}

    """

    return query_df(query)


# =====================================
# RECOMMENDED PORTFOLIO
# =====================================
def get_recommended_portfolio():

    query = """

        SELECT

            symbol,
            target_allocation,
            score,
            action,
            current_price,
            target_value,
            recommended_shares

        FROM recommended_portfolio

        ORDER BY target_allocation DESC

    """

    return query_df(query)


# =====================================
# EQUITY CURVE
# =====================================
def get_equity_curve():

    query = """

        SELECT

            date,
            equity

        FROM portfolio_history

        ORDER BY date ASC

    """

    return query_df(query)


# =====================================
# PERFORMANCE METRICS
# =====================================
def calculate_performance(equity_curve):

    if equity_curve.empty:

        return {

            "cagr": 0,

            "max_drawdown": 0

        }

    equity_curve = equity_curve.copy()

    starting_equity = float(
        equity_curve.iloc[0]["equity"]
    )

    if starting_equity <= 0:

        return {

            "cagr": 0,

            "max_drawdown": 0

        }

    ending_equity = float(
        equity_curve.iloc[-1]["equity"]
    )

    if ending_equity <= 0:

        return {

            "cagr": 0,

            "max_drawdown": 0

        }

    # =====================================
    # CAGR
    # =====================================
    equity_curve["date"] = pd.to_datetime(
        equity_curve["date"]
    )

    start_date = equity_curve[
        "date"
    ].min()

    end_date = equity_curve[
        "date"
    ].max()

    total_days = (

        end_date
        - start_date

    ).days

    years = total_days / 365.25
    # =====================================
    # NOT ENOUGH HISTORY
    # =====================================
    if years < 0.15:

        cagr = None

    else:

        cagr = (

            (
                ending_equity
                / starting_equity
            ) ** (1 / years)

            - 1

        ) * 100


    # =====================================
    # MAX DRAWDOWN
    # =====================================
    equity_curve["rolling_max"] = (

        equity_curve["equity"]
        .cummax()

    )

    equity_curve["drawdown"] = (

        equity_curve["equity"]

        / equity_curve["rolling_max"]

        - 1

    )

    max_drawdown = (

        equity_curve["drawdown"]
        .min()

        * 100

    )

    return {

        "cagr":

            round(cagr, 2)

            if cagr is not None

            else None,

        "max_drawdown": round(
            abs(max_drawdown),
            2
        )

    }


# =====================================
# CURRENT DRAWDOWN
# =====================================
def get_current_drawdown(equity_curve):

    if equity_curve.empty:

        return 0

    current_equity = float(
        equity_curve.iloc[-1]["equity"]
    )

    peak_equity = float(

        equity_curve["equity"]
        .max()

    )

    # =====================================
    # SAFETY
    # =====================================
    if peak_equity <= 0:

        return 0

    drawdown = (

        (
            current_equity
            / peak_equity
        )

        - 1

    ) * 100

    return round(
        abs(drawdown),
        2
    )


# =====================================
# DASHBOARD DATA
# =====================================
def get_dashboard_data():

    logger.info(
        "Loading dashboard data..."
    )

    # =====================================
    # LIVE PORTFOLIO
    # =====================================
    live_portfolio = (
        get_live_portfolio()
    )

    positions = live_portfolio[
        "positions"
    ]

    # =====================================
    # DB DATA
    # =====================================
    rankings = get_rankings()

    rebalance_history = (
        get_rebalance_history()
    )

    executed_trades = (
        get_executed_trades()
    )

    recommended_portfolio = (
        get_recommended_portfolio()
    )

    equity_curve = (
        get_equity_curve()
    )

    equity_curve_json = (

        equity_curve.to_dict(
            orient="records"
        )

    )

    system_state = (
        get_system_state()
    )

    # =====================================
    # LIVE EQUITY OVERRIDE
    # =====================================
    system_state["current_equity"] = (

        live_portfolio[
            "total_equity"
        ]

    )

    system_state["current_cash"] = (

        live_portfolio[
            "cash"
        ]

    )

    # =====================================
    # PERFORMANCE
    # =====================================
    performance = (
        calculate_performance(
            equity_curve
        )
    )

    pnl_summary = (
        get_pnl_summary()
    )

    drawdown = (
        get_current_drawdown(
            equity_curve
        )
    )

    latest_rebalance = None

    if not rebalance_history.empty:

        latest_rebalance = (

            rebalance_history
            .iloc[0]
            .to_dict()

        )

    logger.info(
        "Dashboard data loaded"
    )

    return {

        "positions": positions,

        "rankings": rankings,

        "rebalance_history":
            rebalance_history,

        "executed_trades":
            executed_trades,

        "recommended_portfolio":
            recommended_portfolio,

        "equity_curve":
            equity_curve,
        
        "equity_curve_json":
            equity_curve_json,

        "system_state":
            system_state,

        "performance":
            performance,

        "drawdown":
            drawdown,

        "latest_rebalance":
            latest_rebalance,

        "pnl_summary":
            pnl_summary,
            
        "risk_report":
            risk_report

    }