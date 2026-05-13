# app/live_portfolio.py

import sqlite3
import pandas as pd
import yfinance as yf

from app.config import DB_NAME

from app.logger import logger


# =====================================
# DB CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# GET LIVE PORTFOLIO
# =====================================
def get_live_portfolio():

    conn = get_connection()

    positions = pd.read_sql_query(

        """

        SELECT *

        FROM positions

        """,

        conn

    )

    system_state = pd.read_sql_query(

        """

        SELECT *

        FROM system_state

        LIMIT 1

        """,

        conn

    )

    conn.close()

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if positions.empty:

        return {

            "positions": pd.DataFrame(),

            "equity": 0,

            "cash": 0,

            "total_equity": 0

        }

    # =====================================
    # GET LIVE PRICES
    # =====================================
    tickers = positions[
        "symbol"
    ].tolist()

    logger.info(
        f"Pulling live prices for {tickers}"
    )

    try:

        data = yf.download(

            tickers,

            period="1d",

            interval="1m",

            progress=False,

            auto_adjust=True

        )

    except Exception as e:

        logger.error(

            f"Live pricing failed: {e}"

        )

        return {

            "positions": positions,

            "equity": 0,

            "cash": 0,

            "total_equity": 0

        }

    # =====================================
    # EXTRACT LIVE PRICES
    # =====================================
    live_prices = {}

    try:

        # MULTI-TICKER FORMAT
        if isinstance(

            data.columns,

            pd.MultiIndex

        ):

            for symbol in tickers:

                try:

                    price = float(

                        data["Close"][
                            symbol
                        ].dropna().iloc[-1]

                    )

                    live_prices[
                        symbol
                    ] = price

                except:

                    logger.warning(

                        f"No live price "
                        f"for {symbol}"

                    )

        # SINGLE TICKER FORMAT
        else:

            symbol = tickers[0]

            price = float(

                data["Close"]
                .dropna()
                .iloc[-1]

            )

            live_prices[
                symbol
            ] = price

    except Exception as e:

        logger.error(

            f"Price parsing failed: {e}"

        )

    # =====================================
    # UPDATE LIVE VALUES
    # =====================================
    total_market_value = 0

    updated_positions = []

    for _, row in positions.iterrows():

        symbol = row["symbol"]

        shares = row["shares"]

        entry_price = row[
            "entry_price"
        ]

        price = live_prices.get(

            symbol,

            row.get(
                "current_price",
                0
            )

        )

        market_value = (
            shares * price
        )

        pnl = (
            market_value
            - (shares * entry_price)
        )

        total_market_value += (
            market_value
        )

        updated_positions.append({

            "symbol": symbol,

            "shares": shares,

            "entry_price": entry_price,

            "current_price": price,

            "market_value": market_value,

            "pnl": pnl,

            "momentum_score": row.get(
                "momentum_score",
                0
            ),

            "volatility": row.get(
                "volatility",
                0
            )

        })

    positions_df = pd.DataFrame(
        updated_positions
    )

    # =====================================
    # CASH
    # =====================================
    current_cash = float(

        system_state.iloc[0].get(

            "current_cash",

            0

        )

    )

    total_equity = (
        total_market_value
        + current_cash
    )

    # =====================================
    # ALLOCATION %
    # =====================================
    if total_equity > 0:

        positions_df[
            "allocation_pct"
        ] = (

            positions_df[
                "market_value"
            ]

            / total_equity

        )

    else:

        positions_df[
            "allocation_pct"
        ] = 0

    logger.info(

        f"Live portfolio updated | "
        f"Equity: ${total_equity:,.2f}"

    )

    return {

        "positions": positions_df,

        "equity": total_market_value,

        "cash": current_cash,

        "total_equity": total_equity

    }