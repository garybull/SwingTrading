# app/reconciliation.py

import pandas as pd

from app.config import (
    START_CAPITAL
)

from app.logger import logger

from app.db_service import (
    query_df,
    execute
)


# =====================================
# REBUILD POSITIONS
# =====================================
def rebuild_positions_from_trades():

    logger.info(
        "Starting reconciliation..."
    )

    # =====================================
    # LOAD TRADES
    # =====================================
    trades = query_df("""

        SELECT *

        FROM executed_trades

        ORDER BY date ASC, id ASC

    """)

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if trades.empty:

        logger.warning(
            "No executed trades found"
        )

        # =====================================
        # RESET POSITIONS
        # =====================================
        execute("""

            DELETE FROM positions

        """)

        execute("""

            UPDATE system_state

            SET current_cash = ?,
                current_equity = ?

            WHERE id = 1

        """, (

            START_CAPITAL,
            START_CAPITAL

        ))

        return {

            "positions": {},

            "cash": START_CAPITAL

        }

    positions = {}

    cash = START_CAPITAL

    # =====================================
    # REPLAY TRADES
    # =====================================
    for _, trade in trades.iterrows():

        symbol = trade["symbol"]

        side = trade["side"]

        shares = int(
            trade["shares"]
        )

        fill_price = float(
            trade["fill_price"]
        )

        total_value = (
            shares * fill_price
        )

        # =====================================
        # INIT POSITION
        # =====================================
        if symbol not in positions:

            positions[symbol] = {

                "shares": 0,

                "avg_price": 0

            }

        current_shares = positions[
            symbol
        ]["shares"]

        current_avg = positions[
            symbol
        ]["avg_price"]

        # =====================================
        # BUY
        # =====================================
        if side == "BUY":

            new_shares = (
                current_shares + shares
            )

            # =====================================
            # WEIGHTED AVERAGE
            # =====================================
            if new_shares > 0:

                new_avg = (

                    (
                        current_shares
                        * current_avg
                    )

                    +

                    (
                        shares
                        * fill_price
                    )

                ) / new_shares

            else:

                new_avg = 0

            positions[symbol][
                "shares"
            ] = new_shares

            positions[symbol][
                "avg_price"
            ] = new_avg

            cash -= total_value

        # =====================================
        # SELL
        # =====================================
        elif side == "SELL":

            positions[symbol][
                "shares"
            ] -= shares

            cash += total_value

    # =====================================
    # CLEAR POSITIONS TABLE
    # =====================================
    execute("""

        DELETE FROM positions

    """)

    # =====================================
    # BUILD OPEN POSITIONS
    # =====================================
    open_positions = []

    total_market_value = 0

    for symbol, pos in positions.items():

        shares = int(
            pos["shares"]
        )

        avg_price = float(
            pos["avg_price"]
        )

        # =====================================
        # SKIP CLOSED POSITIONS
        # =====================================
        if shares <= 0:

            continue

        market_value = (
            shares * avg_price
        )

        allocation_pct = (

            market_value

            / START_CAPITAL

        )

        total_market_value += (
            market_value
        )

        open_positions.append({

            "symbol": symbol,

            "shares": shares,

            "avg_price": avg_price,

            "market_value": market_value

        })

    # =====================================
    # TOTAL EQUITY
    # =====================================
    total_equity = (
        total_market_value
        + cash
    )

    # =====================================
    # INSERT POSITIONS
    # =====================================
    for pos in open_positions:

        allocation_pct = 0

        if total_equity > 0:

            allocation_pct = (

                pos["market_value"]

                / total_equity

            )

        execute("""

            INSERT INTO positions (

                symbol,
                shares,
                entry_price,
                current_price,
                market_value,
                allocation_pct,
                momentum_score,
                volatility,
                rebalance_date

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            pos["symbol"],

            pos["shares"],

            pos["avg_price"],

            pos["avg_price"],

            pos["market_value"],

            allocation_pct,

            0,


            ""

        ))

    # =====================================
    # UPDATE SYSTEM STATE
    # =====================================
    execute("""

        UPDATE system_state

        SET
            current_cash = ?,
            current_equity = ?

        WHERE id = 1

    """, (

        cash,
        total_equity

    ))

    logger.info(
        "Reconciliation complete"
    )

    logger.info(

        f"Cash rebuilt to "
        f"${cash:,.2f}"

    )

    logger.info(

        f"Total equity rebuilt to "
        f"${total_equity:,.2f}"

    )

    logger.info(

        f"Open positions rebuilt: "
        f"{len(open_positions)}"

    )

    return {

        "positions":
            positions,

        "cash":
            cash,

        "equity":
            total_equity

    }