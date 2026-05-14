# app/pnl_engine.py

import pandas as pd

from app.live_portfolio import (
    get_live_portfolio
)

from app.logger import logger

from app.db_service import (
    query_df
)


# =====================================
# UNREALIZED PNL
# =====================================
def calculate_unrealized_pnl():

    logger.info(
        "Calculating unrealized PnL..."
    )

    live_portfolio = (
        get_live_portfolio()
    )

    positions = live_portfolio[
        "positions"
    ]

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if positions.empty:

        return {

            "positions":
                pd.DataFrame(),

            "total_unrealized":
                0

        }

    pnl_rows = []

    total_unrealized = 0

    # =====================================
    # POSITION LOOP
    # =====================================
    for _, row in positions.iterrows():

        symbol = row["symbol"]

        shares = float(
            row["shares"]
        )

        entry_price = float(
            row["entry_price"]
        )

        current_price = float(
            row["current_price"]
        )

        # =====================================
        # PNL
        # =====================================
        unrealized = (

            current_price
            - entry_price

        ) * shares

        # =====================================
        # PNL %
        # =====================================
        if entry_price > 0:

            unrealized_pct = (

                (
                    current_price
                    / entry_price
                ) - 1

            ) * 100

        else:

            unrealized_pct = 0

        total_unrealized += (
            unrealized
        )

        pnl_rows.append({

            "symbol":
                symbol,

            "shares":
                shares,

            "entry_price":
                entry_price,

            "current_price":
                current_price,

            "unrealized_pnl":
                unrealized,

            "unrealized_pct":
                unrealized_pct

        })

    pnl_df = pd.DataFrame(
        pnl_rows
    )

    logger.info(

        f"Calculated unrealized "
        f"PnL for "
        f"{len(pnl_df)} positions"

    )

    return {

        "positions":
            pnl_df,

        "total_unrealized":
            total_unrealized

    }


# =====================================
# REALIZED PNL
# =====================================
def calculate_realized_pnl():

    logger.info(
        "Calculating realized PnL..."
    )

    trades = query_df("""

        SELECT *

        FROM executed_trades

        ORDER BY date ASC, id ASC

    """)

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if trades.empty:

        return {

            "trades":
                pd.DataFrame(),

            "total_realized":
                0

        }

    realized_rows = []

    total_realized = 0

    inventory = {}

    # =====================================
    # FIFO MATCHING
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

        if symbol not in inventory:

            inventory[symbol] = []

        # =====================================
        # BUY
        # =====================================
        if side == "BUY":

            inventory[symbol].append({

                "shares":
                    shares,

                "price":
                    fill_price

            })

        # =====================================
        # SELL
        # =====================================
        elif side == "SELL":

            remaining = shares

            realized_trade = 0

            while (

                remaining > 0

                and len(
                    inventory[symbol]
                ) > 0

            ):

                lot = inventory[
                    symbol
                ][0]

                matched = min(

                    remaining,

                    lot["shares"]

                )

                pnl = (

                    fill_price
                    - lot["price"]

                ) * matched

                realized_trade += pnl

                total_realized += pnl

                lot["shares"] -= matched

                remaining -= matched

                # =====================================
                # REMOVE EMPTY LOT
                # =====================================
                if lot["shares"] <= 0:

                    inventory[
                        symbol
                    ].pop(0)

            realized_rows.append({

                "symbol":
                    symbol,

                "shares":
                    shares,

                "sell_price":
                    fill_price,

                "realized_pnl":
                    realized_trade

            })

    realized_df = pd.DataFrame(
        realized_rows
    )

    logger.info(

        f"Calculated realized "
        f"PnL for "
        f"{len(realized_df)} trades"

    )

    return {

        "trades":
            realized_df,

        "total_realized":
            total_realized

    }


# =====================================
# COMBINED PNL SUMMARY
# =====================================
def get_pnl_summary():

    logger.info(
        "Building PnL summary..."
    )

    unrealized = (
        calculate_unrealized_pnl()
    )

    realized = (
        calculate_realized_pnl()
    )

    summary = {

        "unrealized_positions":

            unrealized[
                "positions"
            ],

        "total_unrealized":

            unrealized[
                "total_unrealized"
            ],

        "realized_trades":

            realized[
                "trades"
            ],

        "total_realized":

            realized[
                "total_realized"
            ]

    }

    logger.info(
        "PnL summary complete"
    )

    return summary