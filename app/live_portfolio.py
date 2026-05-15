# app/live_portfolio.py
import pandas as pd

from app.config import DB_NAME

from app.price_cache import (
    get_live_prices
)

from app.logger import logger
from app.db_service import (
    query_df
)

# =====================================
# GET LIVE PORTFOLIO
# =====================================
def get_live_portfolio():

    positions = query_df("""

        SELECT *

        FROM positions

    """)

    system_state = query_df("""

        SELECT *

        FROM system_state

        LIMIT 1

    """)

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

        f"Getting live prices for "
        f"{tickers}"

    )

    live_prices = get_live_prices(
        tickers
    )

    # =====================================
    # UPDATE LIVE VALUES
    # =====================================
    total_market_value = 0

    updated_positions = []

    for _, row in positions.iterrows():

        symbol = row["symbol"]

        shares = float(
            row["shares"]
        )

        entry_price = float(
            row["entry_price"]
        )

        # =====================================
        # LIVE PRICE
        # =====================================
        price = live_prices.get(

            symbol,

            float(
                row.get(
                    "current_price",
                    0
                )
            )

        )

        market_value = (
            shares * price
        )

        pnl = (

            market_value

            - (
                shares
                * entry_price
            )

        )

        total_market_value += (
            market_value
        )

        updated_positions.append({

            "symbol": symbol,

            "shares": shares,

            "entry_price":
                entry_price,

            "current_price":
                price,

            "market_value":
                market_value,

            "pnl": pnl,

            "momentum_score":

                row.get(
                    "momentum_score",
                    0
                ),

            "volatility":

                row.get(
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
        # =====================================
        # PERCENT FORMAT
        # =====================================
        positions_df[
            "allocation_pct"
        ] = positions_df[
            "allocation_pct"
        ].astype(float)

    else:

        positions_df[
            "allocation_pct"
        ] = 0

    logger.info(

        f"Live portfolio updated | "

        f"Equity: "
        f"${total_equity:,.2f}"

    )

    return {

        "positions":
            positions_df,

        "equity":
            total_market_value,

        "cash":
            current_cash,

        "total_equity":
            total_equity

    }