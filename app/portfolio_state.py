# app/portfolio_state.py

from datetime import datetime

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
    # LAZY IMPORTS
    # =====================================
    from app.regime_engine import (
        determine_market_regime
    )

    from app.live_portfolio import (
        get_live_portfolio
    )

    # =====================================
    # LIVE PORTFOLIO
    # =====================================
    portfolio = get_live_portfolio()

    positions_df = portfolio[
        "positions"
    ]

    cash = float(
        portfolio[
            "cash"
        ]
    )

    total_market_value = float(
        portfolio[
            "market_value"
        ]
    )

    total_equity = float(
        portfolio[
            "total_equity"
        ]
    )

    # =====================================
    # LOAD SYSTEM STATE
    # =====================================
    state = query_df("""

        SELECT
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

        return {

            "equity": 0,
            "cash": 0,
            "market_value": 0,
            "starting_capital": 0

        }

    starting_capital = float(

        state.iloc[0][
            "starting_capital"
        ]

    )

    # =====================================
    # DETERMINE REGIME
    # =====================================
    regime_data = (
        determine_market_regime()
    )

    regime = regime_data.get(
        "regime",
        "UNKNOWN"
    )

    # =====================================
    # CURRENT LEADER
    # =====================================
    current_leader = "CASH"

    if regime == "RISK_ON":

        recommended = query_df("""

            SELECT
                symbol

            FROM recommended_portfolio

            ORDER BY score DESC

            LIMIT 1

        """)

        if not recommended.empty:

            current_leader = str(

                recommended.iloc[0][
                    "symbol"
                ]

            )

    # =====================================
    # UPDATE SYSTEM STATE
    # =====================================
    execute("""

        UPDATE system_state

        SET
            current_equity = ?,
            current_leader = ?,
            market_regime = ?,
            current_cash = ?

        WHERE id = 1

    """, (

        total_equity,
        current_leader,
        regime,
        cash

    ))

    # =====================================
    # UPDATE POSITION ALLOCATIONS
    # =====================================
    if not positions_df.empty and total_equity > 0:

        for _, row in positions_df.iterrows():

            symbol = row["symbol"]

            market_value = float(
                row["market_value"]
            )

            allocation_pct = (

                market_value
                / total_equity

            )

            execute("""

                UPDATE positions

                SET
                    current_price = ?,
                    market_value = ?,
                    allocation_pct = ?

                WHERE symbol = ?

            """, (

                float(
                    row["current_price"]
                ),

                market_value,

                allocation_pct,

                symbol

            ))

    # =====================================
    # SAVE DAILY SNAPSHOT
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
        total_equity,
        cash,
        total_market_value

    ))

    logger.info(

        f"System state refreshed | "

        f"Cash=${cash:,.2f} | "

        f"Market Value=${total_market_value:,.2f} | "

        f"Equity=${total_equity:,.2f}"

    )

    # =====================================
    # RETURN
    # =====================================
    return {

        "equity":
            total_equity,

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