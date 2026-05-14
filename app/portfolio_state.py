# app/portfolio_state.py

from app.logger import logger

from app.db_service import (
    query_df,
    execute
)


# =====================================
# REFRESH SYSTEM STATE
# =====================================
def refresh_system_state():

    logger.info(
        "Refreshing system state..."
    )

    # =====================================
    # LOAD POSITIONS
    # =====================================
    positions = query_df("""

        SELECT

            market_value

        FROM positions

    """)

    # =====================================
    # TOTAL MARKET VALUE
    # =====================================
    if not positions.empty:

        total_market_value = float(

            positions[
                "market_value"
            ].sum()

        )

    else:

        total_market_value = 0

    # =====================================
    # LOAD CASH
    # =====================================
    state = query_df("""

        SELECT

            current_cash

        FROM system_state

        WHERE id = 1

    """)

    if not state.empty:

        cash = float(

            state.iloc[0][
                "current_cash"
            ]

        )

    else:

        cash = 0

    # =====================================
    # TOTAL EQUITY
    # =====================================
    equity = (

        total_market_value
        + cash

    )

    # =====================================
    # UPDATE SYSTEM STATE
    # =====================================
    execute("""

        UPDATE system_state

        SET current_equity = ?

        WHERE id = 1

    """, (

        equity,

    ))

    logger.info(

        f"System equity updated: "
        f"${equity:,.2f}"

    )

    return equity