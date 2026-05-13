# app/reconciliation.py

import sqlite3
import pandas as pd

from app.config import (
    DB_NAME,
    START_CAPITAL
)

from app.logger import logger


# =====================================
# DB CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# REBUILD POSITIONS
# =====================================
def rebuild_positions_from_trades():

    logger.info(
        "🔧 Starting reconciliation..."
    )

    conn = get_connection()

    trades = pd.read_sql_query(

        """

        SELECT *

        FROM executed_trades

        ORDER BY date ASC, id ASC

        """,

        conn

    )

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
    cur = conn.cursor()

    cur.execute("""

        DELETE FROM positions

    """)

    # =====================================
    # REBUILD POSITIONS TABLE
    # =====================================
    for symbol, pos in positions.items():

        shares = pos["shares"]

        avg_price = pos["avg_price"]

        if shares <= 0:

            continue

        market_value = (
            shares * avg_price
        )

        cur.execute("""

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

            symbol,

            shares,

            avg_price,

            avg_price,

            market_value,

            0,

            0,

            0,

            ""

        ))

    # =====================================
    # UPDATE CASH
    # =====================================
    cur.execute("""

        UPDATE system_state

        SET current_cash = ?

        WHERE id = 1

    """, (

        cash,

    ))

    conn.commit()

    conn.close()

    logger.info(
        "✅ Reconciliation complete"
    )

    logger.info(
        f"Cash: ${cash:,.2f}"
    )