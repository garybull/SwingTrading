# app/pnl_engine.py

import sqlite3
import pandas as pd

from app.config import DB_NAME

from app.live_portfolio import (
    get_live_portfolio
)

from app.logger import logger


# =====================================
# DB CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# UNREALIZED PNL
# =====================================
def calculate_unrealized_pnl():

    live_portfolio = (
        get_live_portfolio()
    )

    positions = live_portfolio[
        "positions"
    ]

    pnl_rows = []

    total_unrealized = 0

    for _, row in positions.iterrows():

        symbol = row["symbol"]

        shares = row["shares"]

        entry_price = row[
            "entry_price"
        ]

        current_price = row[
            "current_price"
        ]

        unrealized = (

            current_price
            - entry_price

        ) * shares

        unrealized_pct = (

            (
                current_price
                / entry_price
            ) - 1

        ) * 100

        total_unrealized += (
            unrealized
        )

        pnl_rows.append({

            "symbol": symbol,

            "shares": shares,

            "entry_price": entry_price,

            "current_price": current_price,

            "unrealized_pnl": unrealized,

            "unrealized_pct":
                unrealized_pct

        })

    df = pd.DataFrame(
        pnl_rows
    )

    return {

        "positions": df,

        "total_unrealized":
            total_unrealized

    }


# =====================================
# REALIZED PNL
# =====================================
def calculate_realized_pnl():

    conn = get_connection()

    trades = pd.read_sql_query(

        """

        SELECT *

        FROM executed_trades

        ORDER BY date ASC, id ASC

        """,

        conn

    )

    conn.close()

    realized_rows = []

    total_realized = 0

    inventory = {}

    for _, trade in trades.iterrows():

        symbol = trade["symbol"]

        side = trade["side"]

        shares = trade["shares"]

        fill_price = trade[
            "fill_price"
        ]

        if symbol not in inventory:

            inventory[symbol] = []

        # =====================================
        # BUY
        # =====================================
        if side == "BUY":

            inventory[symbol].append({

                "shares": shares,

                "price": fill_price

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

                if lot["shares"] <= 0:

                    inventory[
                        symbol
                    ].pop(0)

            realized_rows.append({

                "symbol": symbol,

                "shares": shares,

                "sell_price":
                    fill_price,

                "realized_pnl":
                    realized_trade

            })

    realized_df = pd.DataFrame(
        realized_rows
    )

    return {

        "trades": realized_df,

        "total_realized":
            total_realized

    }


# =====================================
# COMBINED PNL
# =====================================
def get_pnl_summary():

    unrealized = (
        calculate_unrealized_pnl()
    )

    realized = (
        calculate_realized_pnl()
    )

    return {

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