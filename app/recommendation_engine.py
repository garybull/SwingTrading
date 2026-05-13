# app/recommendation_engine.py

from app.live_portfolio import (
    get_live_portfolio
)

from app.logger import logger


# =====================================
# BUILD ACTION PLAN
# =====================================
def build_action_plan(

    recommended_portfolio,

    threshold=0.03

):

    logger.info(
        "Building action plan..."
    )

    # =====================================
    # LIVE POSITIONS
    # =====================================
    live_portfolio = (
        get_live_portfolio()
    )

    current_positions = (
        live_portfolio[
            "positions"
        ]
    )

    actions = []

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if recommended_portfolio is None:

        logger.warning(
            "Recommended portfolio is None"
        )

        return []

    if current_positions is None:

        logger.warning(
            "Current positions are None"
        )

        return []

    # =====================================
    # CURRENT HOLDINGS MAP
    # =====================================
    current_map = {}

    for _, row in current_positions.iterrows():

        current_map[
            row["symbol"]
        ] = row[
            "allocation_pct"
        ]

    # =====================================
    # TARGET POSITIONS
    # =====================================
    for _, row in recommended_portfolio.iterrows():

        symbol = row["symbol"]

        target = row[
            "target_allocation"
        ]

        current = current_map.get(

            symbol,

            0

        )

        diff = target - current

        # =====================================
        # ACTION LOGIC
        # =====================================
        if abs(diff) < threshold:

            action = "HOLD"

        elif diff > 0:

            action = "BUY"

        else:

            action = "SELL"

        actions.append({

            "symbol": symbol,

            "target_allocation": target,

            "current_allocation": current,

            "difference": diff,

            "action": action,

            "score": row.get(
                "score",
                0
            )

        })

    # =====================================
    # FULL EXITS
    # =====================================
    recommended_symbols = set(

        recommended_portfolio[
            "symbol"
        ].tolist()

    )

    for _, row in current_positions.iterrows():

        symbol = row["symbol"]

        if symbol not in recommended_symbols:

            actions.append({

                "symbol": symbol,

                "target_allocation": 0,

                "current_allocation": row[
                    "allocation_pct"
                ],

                "difference": -row[
                    "allocation_pct"
                ],

                "action": "SELL",

                "score": 0

            })

    # =====================================
    # SORT ACTIONS
    # =====================================
    action_priority = {

        "SELL": 0,

        "BUY": 1,

        "HOLD": 2

    }

    actions = sorted(

        actions,

        key=lambda x: (

            action_priority[
                x["action"]
            ],

            -abs(
                x["difference"]
            )

        )

    )

    logger.info(

        f"Generated "
        f"{len(actions)} actions"

    )

    return actions