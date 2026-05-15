# app/portfolio_state.py

from datetime import datetime
import pandas as pd

from app.db_service import (
    query_df,
    execute
)

from app.logger import logger


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
            symbol,
            shares,
            current_price,
            market_value

        FROM positions

    """)

    # =====================================
    # MARKET VALUE
    # =====================================
    total_market_value = 0

    if not positions.empty:

        total_market_value = float(

            positions[
                "market_value"
            ].sum()

        )

    # =====================================
    # LOAD CASH
    # =====================================
    state = query_df("""

        SELECT
            current_cash,
            starting_capital

        FROM system_state

        WHERE id = 1

    """)

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if state.empty:

        logger.warning(
            "No system_state row found"
        )

        return 0

    cash = float(

        state.iloc[0][
            "current_cash"
        ]

    )

    starting_capital = float(

        state.iloc[0][
            "starting_capital"
        ]

    )

    # =====================================
    # TOTAL EQUITY
    # =====================================
    equity = (

        cash
        + total_market_value

    )

    # =====================================
    # UPDATE SYSTEM STATE
    # =====================================
    execute("""

        UPDATE system_state

        SET
            current_equity = ?

        WHERE id = 1

    """, (

        equity,

    ))

    # =====================================
    # UPDATE POSITION ALLOCATIONS
    # =====================================
    if not positions.empty and equity > 0:

        for _, row in positions.iterrows():

            symbol = row["symbol"]

            market_value = float(
                row["market_value"]
            )

            allocation_pct = (

                market_value
                / equity

            )

            execute("""

                UPDATE positions

                SET allocation_pct = ?

                WHERE symbol = ?

            """, (

                allocation_pct,

                symbol

            ))

    # =====================================
    # SAVE EQUITY SNAPSHOT
    # =====================================
    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # Remove duplicate daily snapshot
    execute("""

        DELETE FROM portfolio_history

        WHERE date = ?

    """, (

        today,

    ))

    execute("""

        INSERT INTO portfolio_history (

            date,
            equity,
            cash,
            market_value

        )

        VALUES (?, ?, ?, ?)

    """, (

        today,

        equity,

        cash,

        total_market_value

    ))

    logger.info(

        f"System state refreshed | "
        f"Equity=${equity:,.2f} | "
        f"Cash=${cash:,.2f} | "
        f"Market Value=${total_market_value:,.2f}"

    )

    return {

        "equity":
            equity,

        "cash":
            cash,

        "market_value":
            total_market_value,

        "starting_capital":
            starting_capital

    }


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    refresh_system_state()