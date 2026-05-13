# app/trade_analytics.py

import sqlite3
import pandas as pd

from app.config import DB_NAME

from app.logger import logger


# =====================================
# DB CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# LOAD TRADES
# =====================================
def load_trades():

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

    return trades


# =====================================
# BUILD CLOSED TRADES
# FIFO MATCHING
# =====================================
def build_closed_trades(trades):

    inventory = {}

    closed = []

    for _, trade in trades.iterrows():

        symbol = trade["symbol"]

        side = trade["side"]

        shares = int(
            trade["shares"]
        )

        fill_price = float(
            trade["fill_price"]
        )

        trade_date = trade["date"]

        if symbol not in inventory:

            inventory[symbol] = []

        # =====================================
        # BUY
        # =====================================
        if side == "BUY":

            inventory[symbol].append({

                "shares": shares,

                "price": fill_price,

                "date": trade_date

            })

        # =====================================
        # SELL
        # =====================================
        elif side == "SELL":

            remaining = shares

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

                closed.append({

                    "symbol": symbol,

                    "entry_price":
                        lot["price"],

                    "exit_price":
                        fill_price,

                    "shares":
                        matched,

                    "entry_date":
                        lot["date"],

                    "exit_date":
                        trade_date,

                    "pnl": pnl

                })

                lot["shares"] -= matched

                remaining -= matched

                if lot["shares"] <= 0:

                    inventory[
                        symbol
                    ].pop(0)

    return pd.DataFrame(closed)


# =====================================
# MAIN ANALYTICS
# =====================================
def get_trade_analytics():

    logger.info(
        "Building trade analytics..."
    )

    trades = load_trades()

    if trades.empty:

        return {

            "win_rate": 0,

            "profit_factor": 0,

            "expectancy": 0,

            "avg_win": 0,

            "avg_loss": 0,

            "largest_win": 0,

            "largest_loss": 0,

            "symbol_stats": []

        }

    closed = build_closed_trades(
        trades
    )

    if closed.empty:

        return {

            "win_rate": 0,

            "profit_factor": 0,

            "expectancy": 0,

            "avg_win": 0,

            "avg_loss": 0,

            "largest_win": 0,

            "largest_loss": 0,

            "symbol_stats": []

        }

    # =====================================
    # WINNERS / LOSERS
    # =====================================
    winners = closed[
        closed["pnl"] > 0
    ]

    losers = closed[
        closed["pnl"] < 0
    ]

    total_trades = len(closed)

    total_wins = len(winners)

    total_losses = len(losers)

    # =====================================
    # WIN RATE
    # =====================================
    if total_trades > 0:

        win_rate = (

            total_wins
            / total_trades

        ) * 100

    else:

        win_rate = 0

    # =====================================
    # AVERAGES
    # =====================================
    avg_win = (

        winners["pnl"].mean()

        if total_wins > 0

        else 0

    )

    avg_loss = (

        losers["pnl"].mean()

        if total_losses > 0

        else 0

    )

    # =====================================
    # PROFIT FACTOR
    # =====================================
    gross_profit = (
        winners["pnl"].sum()
    )

    gross_loss = abs(
        losers["pnl"].sum()
    )

    if gross_loss > 0:

        profit_factor = (
            gross_profit
            / gross_loss
        )

    else:

        profit_factor = 0

    # =====================================
    # EXPECTANCY
    # =====================================
    win_prob = (
        total_wins
        / total_trades
    )

    loss_prob = (
        total_losses
        / total_trades
    )

    expectancy = (

        (win_prob * avg_win)

        +

        (loss_prob * avg_loss)

    )

    # =====================================
    # EXTREMES
    # =====================================
    largest_win = (
        closed["pnl"].max()
    )

    largest_loss = (
        closed["pnl"].min()
    )

    # =====================================
    # SYMBOL ATTRIBUTION
    # =====================================
    symbol_stats = (

        closed.groupby(
            "symbol"
        )

        .agg({

            "pnl": ["sum", "count"]

        })

        .reset_index()

    )

    symbol_stats.columns = [

        "symbol",

        "total_pnl",

        "trade_count"

    ]

    symbol_stats = (

        symbol_stats

        .sort_values(

            "total_pnl",

            ascending=False

        )

    )

    logger.info(
        "Trade analytics complete"
    )

    return {

        "win_rate":
            round(win_rate, 2),

        "profit_factor":
            round(profit_factor, 2),

        "expectancy":
            round(expectancy, 2),

        "avg_win":
            round(avg_win, 2),

        "avg_loss":
            round(avg_loss, 2),

        "largest_win":
            round(largest_win, 2),

        "largest_loss":
            round(largest_loss, 2),

        "symbol_stats":
            symbol_stats.to_dict(
                orient="records"
            )

    }