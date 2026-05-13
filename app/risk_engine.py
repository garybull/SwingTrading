# app/risk_engine.py

from app.live_portfolio import (
    get_live_portfolio
)

from app.logger import logger


# =====================================
# LEVERAGE MAP
# =====================================
LEVERAGE_MAP = {

    "TQQQ": 3,
    "SOXL": 3,
    "TECL": 3,
    "UPRO": 3,
    "SPXL": 3,

    "QLD": 2,
    "USD": 2,

}


# =====================================
# RISK STATUS
# =====================================
def get_risk_status(
    exposure
):

    if exposure < 1.0:

        return "Conservative"

    elif exposure < 1.8:

        return "Moderate"

    elif exposure < 2.5:

        return "Aggressive"

    return "Extreme"


# =====================================
# BUILD RISK REPORT
# =====================================
def get_risk_report():

    logger.info(
        "Building risk report..."
    )

    portfolio = (
        get_live_portfolio()
    )

    positions = portfolio[
        "positions"
    ]

    cash = portfolio[
        "cash"
    ]

    total_equity = portfolio[
        "total_equity"
    ]

    if positions.empty:

        return {

            "effective_exposure": 0,

            "risk_status":
                "No Positions",

            "cash_pct": 0,

            "largest_position": 0,

            "positions": []

        }

    # =====================================
    # EFFECTIVE EXPOSURE
    # =====================================
    effective_exposure = 0

    enriched_positions = []

    for _, row in positions.iterrows():

        symbol = row["symbol"]

        allocation = float(
            row["allocation_pct"]
        )

        leverage = LEVERAGE_MAP.get(
            symbol,
            1
        )

        effective = (
            allocation
            * leverage
        )

        effective_exposure += (
            effective
        )

        enriched_positions.append({

            "symbol": symbol,

            "allocation_pct":
                allocation * 100,

            "effective_exposure":
                effective * 100,

            "leverage":
                leverage,

            "market_value":
                row["market_value"]

        })

    # =====================================
    # LARGEST POSITION
    # =====================================
    largest_position = max(

        [
            p["allocation_pct"]

            for p in enriched_positions
        ]

    )

    # =====================================
    # CASH %
    # =====================================
    if total_equity > 0:

        cash_pct = (
            cash
            / total_equity
        ) * 100

    else:

        cash_pct = 0

    risk_status = (
        get_risk_status(
            effective_exposure
        )
    )

    logger.info(
        "Risk report complete"
    )

    return {

        "effective_exposure":

            round(
                effective_exposure
                * 100,
                2
            ),

        "risk_status":
            risk_status,

        "cash_pct":
            round(cash_pct, 2),

        "largest_position":
            round(largest_position, 2),

        "positions":
            enriched_positions

    }