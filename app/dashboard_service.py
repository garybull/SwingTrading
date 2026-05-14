# app/dashboard_service.py

from app.config import (
    START_CAPITAL
)

from app.logger import logger

from app.live_portfolio import (
    get_live_portfolio
)

from app.db_service import (
    query_df
)


# =====================================
# LOAD SYSTEM STATE
# =====================================
def load_system_state():

    system_state = query_df("""

        SELECT *

        FROM system_state

        LIMIT 1

    """)

    if system_state.empty:

        return {}

    return system_state.iloc[0].to_dict()


# =====================================
# LOAD RECENT REBALANCE LOG
# =====================================
def load_recent_rebalances(

    limit=10

):

    return query_df(f"""

        SELECT *

        FROM rebalance_log

        ORDER BY id DESC

        LIMIT {limit}

    """)


# =====================================
# BUILD DASHBOARD DATA
# =====================================
def build_dashboard_data():

    logger.info(
        "Building dashboard data..."
    )

    # =====================================
    # LIVE PORTFOLIO
    # =====================================
    portfolio_data = (
        get_live_portfolio()
    )

    positions = portfolio_data[
        "positions"
    ]

    equity = float(

        portfolio_data.get(
            "equity",
            0
        )

    )

    cash = float(

        portfolio_data.get(
            "cash",
            0
        )

    )

    total_equity = float(

        portfolio_data.get(
            "total_equity",
            0
        )

    )

    # =====================================
    # EMPTY ACCOUNT SAFETY
    # =====================================
    if total_equity <= 0:

        total_equity = START_CAPITAL

        cash = START_CAPITAL

    # =====================================
    # PERFORMANCE
    # =====================================
    total_return_pct = (

        (

            total_equity

            - START_CAPITAL

        )

        / START_CAPITAL

    ) * 100

    # =====================================
    # SYSTEM STATE
    # =====================================
    system_state = (
        load_system_state()
    )

    # =====================================
    # RECENT REBALANCES
    # =====================================
    recent_rebalances = (
        load_recent_rebalances()
    )

    logger.info(
        "Dashboard data built"
    )

    return {

        "positions":
            positions,

        "equity":
            equity,

        "cash":
            cash,

        "total_equity":
            total_equity,

        "total_return_pct":
            total_return_pct,

        "system_state":
            system_state,

        "recent_rebalances":
            recent_rebalances

    }