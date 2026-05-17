# app/execution_engine.py

from datetime import datetime

from app.logger import logger

from app.config import (
    SLIPPAGE
)

from app.db_service import (
    query_df,
    execute
)
from app.db_service import (
    query_df,
    execute,
    get_connection
)


# =====================================
# GET CURRENT CASH
# =====================================
def get_current_cash():

    state = query_df("""

        SELECT

            current_cash

        FROM system_state

        WHERE id = 1

    """)

    if state.empty:

        return 0

    return float(

        state.iloc[0][
            "current_cash"
        ]

    )


# =====================================
# UPDATE CASH
# =====================================
def update_cash(new_cash):

    logger.info(
        f"NEW CASH SHOULD BE: "
        f"${new_cash:,.2f}"
    )

    verify = query_df("""

        SELECT current_cash

        FROM system_state

        WHERE id = 1

    """)

    logger.info(
        f"DB CASH AFTER UPDATE: "
        f"${float(verify.iloc[0]['current_cash']):,.2f}"
    )

    logger.info(
        f"Updating cash to "
        f"${new_cash:,.2f}"
    )

    conn = get_connection()

    cur = conn.cursor()

    try:

        cur.execute("""

            UPDATE system_state

            SET current_cash = ?

            WHERE id = 1

        """, (

            float(new_cash),

        ))

        conn.commit()

        logger.info(

            f"Rows updated: "
            f"{cur.rowcount}"

        )

    finally:

        conn.close()

    verify = query_df("""

        SELECT current_cash

        FROM system_state

        WHERE id = 1

    """)

    logger.info(

        f"Verified cash: "
        f"${float(verify.iloc[0]['current_cash']):,.2f}"

    )
# =====================================
# GET POSITION
# =====================================
def get_position(symbol):

    position = query_df("""

        SELECT *

        FROM positions

        WHERE symbol = ?

    """, (

        symbol,

    ))

    if position.empty:

        return None

    return position.iloc[0].to_dict()


# =====================================
# INSERT EXECUTED TRADE
# =====================================
def log_trade(

    symbol,
    side,
    shares,
    fill_price,
    notes=""

):

    total_value = (
        shares * fill_price
    )

    execute("""

        INSERT INTO executed_trades (

            date,
            symbol,
            side,
            shares,
            fill_price,
            total_value,
            notes

        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

    """, (

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        symbol,

        side,

        shares,

        fill_price,

        total_value,

        notes

    ))

    logger.info(

        f"Trade logged: "
        f"{side} {shares} "
        f"{symbol}"

    )


# =====================================
# INSERT POSITION LOT
# =====================================
def insert_position_lot(

    symbol,
    shares,
    fill_price

):

    execute("""

        INSERT INTO position_lots (

            symbol,
            shares,
            remaining_shares,
            entry_price,
            entry_date

        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        symbol,

        shares,

        shares,

        fill_price,

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    ))


# =====================================
# UPDATE POSITION
# =====================================
def update_position(

    symbol,
    shares_delta,
    fill_price

):

    current = get_position(
        symbol
    )

    # =====================================
    # NEW POSITION
    # =====================================
    if current is None:

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

            symbol,

            shares_delta,

            fill_price,

            fill_price,

            shares_delta * fill_price,

            0,

            0,

            0,

            datetime.now().strftime(
                "%Y-%m-%d"
            )

        ))

        logger.info(

            f"New position created: "
            f"{symbol}"

        )

        return

    # =====================================
    # EXISTING POSITION
    # =====================================
    current_shares = int(
        current["shares"]
    )

    current_entry = float(
        current["entry_price"]
    )

    new_shares = (
        current_shares
        + shares_delta
    )

    # =====================================
    # POSITION CLOSED
    # =====================================
    if new_shares <= 0:

        execute("""

            DELETE FROM positions

            WHERE symbol = ?

        """, (

            symbol,

        ))

        logger.info(
            f"Position closed: {symbol}"
        )

        return

    # =====================================
    # WEIGHTED AVERAGE
    # =====================================
    if shares_delta > 0:

        new_entry = (

            (
                current_shares
                * current_entry
            )

            +

            (
                shares_delta
                * fill_price
            )

        ) / new_shares

    else:

        new_entry = current_entry

    market_value = (
        new_shares
        * fill_price
    )

    execute("""

        UPDATE positions

        SET

            shares = ?,
            entry_price = ?,
            current_price = ?,
            market_value = ?

        WHERE symbol = ?

    """, (

        new_shares,

        new_entry,

        fill_price,

        market_value,

        symbol

    ))

    logger.info(

        f"Updated position: "
        f"{symbol}"

    )


# =====================================
# EXECUTE BUY
# =====================================
def execute_buy(

    symbol,
    shares,
    market_price,
    notes=""

):

    logger.info(

        f"Executing BUY "
        f"{shares} {symbol}"

    )

    # =====================================
    # SLIPPAGE
    # =====================================
    fill_price = round(

        market_price
        * (1 + SLIPPAGE),

        2

    )

    total_cost = (
        shares * fill_price
    )

    current_cash = (
        get_current_cash()
    )

    # =====================================
    # CASH CHECK
    # =====================================
    if total_cost > current_cash:

        logger.warning(
            "Insufficient cash"
        )

        return False

    # =====================================
    # UPDATE CASH
    # =====================================
    new_cash = (
        current_cash
        - total_cost
    )

    update_cash(
        new_cash
    )

    # =====================================
    # UPDATE POSITION
    # =====================================
    update_position(

        symbol,

        shares,

        fill_price

    )

    # =====================================
    # INSERT LOT
    # =====================================
    insert_position_lot(

        symbol,

        shares,

        fill_price

    )

    # =====================================
    # LOG TRADE
    # =====================================
    log_trade(

        symbol,

        "BUY",

        shares,

        fill_price,

        notes

    )

    # =====================================
    # REFRESH EQUITY
    # =====================================
    from app.portfolio_state import (
        refresh_system_state
    )
    refresh_system_state()

    logger.info(
        "BUY execution complete"
    )

    return True


# =====================================
# EXECUTE SELL
# =====================================
def execute_sell(

    symbol,
    shares,
    market_price,
    notes=""

):

    logger.info(

        f"Executing SELL "
        f"{shares} {symbol}"

    )

    current = get_position(
        symbol
    )

    # =====================================
    # POSITION CHECK
    # =====================================
    if current is None:

        logger.warning(
            "Position not found"
        )

        return False

    current_shares = int(
        current["shares"]
    )

    if shares > current_shares:

        logger.warning(
            "Insufficient shares"
        )

        return False

    # =====================================
    # SLIPPAGE
    # =====================================
    fill_price = round(

        market_price
        * (1 - SLIPPAGE),

        2

    )

    total_value = (
        shares * fill_price
    )

    current_cash = (
        get_current_cash()
    )

    new_cash = (
        current_cash
        + total_value
    )

    # =====================================
    # UPDATE CASH
    # =====================================
    update_cash(
        new_cash
    )

    # =====================================
    # UPDATE POSITION
    # =====================================
    update_position(

        symbol,

        -shares,

        fill_price

    )

    # =====================================
    # LOG TRADE
    # =====================================
    log_trade(

        symbol,

        "SELL",

        shares,

        fill_price,

        notes

    )

    # =====================================
    # UPDATE FIFO LOTS
    # =====================================
    update_position_lots_after_sell(

        symbol,

        shares

    )

    # =====================================
    # REFRESH EQUITY
    # =====================================
    refresh_system_state()

    logger.info(
        "SELL execution complete"
    )

    return True


# =====================================
# FIFO LOT REDUCTION
# =====================================
def update_position_lots_after_sell(

    symbol,
    shares_to_sell

):

    lots = query_df("""

        SELECT *

        FROM position_lots

        WHERE symbol = ?
        AND remaining_shares > 0

        ORDER BY entry_date ASC, id ASC

    """, (

        symbol,

    ))

    remaining = shares_to_sell

    for _, lot in lots.iterrows():

        if remaining <= 0:

            break

        lot_id = int(
            lot["id"]
        )

        lot_remaining = int(
            lot["remaining_shares"]
        )

        reduction = min(

            remaining,

            lot_remaining

        )

        new_remaining = (
            lot_remaining
            - reduction
        )

        execute("""

            UPDATE position_lots

            SET remaining_shares = ?

            WHERE id = ?

        """, (

            new_remaining,

            lot_id

        ))

        remaining -= reduction


# =====================================
# EXECUTE ACTION PLAN
# =====================================
def execute_action_plan(actions):

    logger.info(
        "Executing action plan..."
    )

    results = []

    for action in actions:

        symbol = action["symbol"]

        side = action["action"]

        shares = int(

            action.get(
                "recommended_shares",
                0
            )

        )

        price = float(

            action.get(
                "current_price",
                0
            )

        )

        if shares <= 0:

            continue

        if price <= 0:

            continue

        # =====================================
        # BUY
        # =====================================
        if side == "BUY":

            success = execute_buy(

                symbol,

                shares,

                price,

                notes="Action plan"

            )

        # =====================================
        # SELL
        # =====================================
        elif side == "SELL":

            success = execute_sell(

                symbol,

                shares,

                price,

                notes="Action plan"

            )

        else:

            success = False

        results.append({

            "symbol":
                symbol,

            "action":
                side,

            "success":
                success

        })

    logger.info(
        "Action plan execution complete"
    )

    return results