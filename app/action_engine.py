# app/action_engine.py

import pandas as pd

from app.logger import logger


# =====================================
# BUILD ACTION PLAN
# =====================================
def build_action_plan(

    recommended_portfolio,

    current_positions,

    threshold=0.01

):

    logger.info(
        "Building action plan..."
    )

    actions = []

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if recommended_portfolio is None:

        return []

    if len(recommended_portfolio) == 0:

        return []

    # =====================================
    # CURRENT POSITIONS MAP
    # =====================================
    current_map = {}

    if current_positions is not None:

        if len(current_positions) > 0:

            current_map = {

                row["symbol"]: row

                for _, row

                in current_positions.iterrows()

            }

    # =====================================
    # BUILD TARGET ACTIONS
    # =====================================
    for _, row in recommended_portfolio.iterrows():

        symbol = row["symbol"]

        target_allocation = float(

            row.get(
                "target_allocation",
                0
            )

        )

        current_price = float(

            row.get(
                "current_price",
                0
            )

        )

        target_value = float(

            row.get(
                "target_value",
                0
            )

        )

        recommended_shares = int(

            row.get(
                "recommended_shares",
                0
            )

        )

        score = float(

            row.get(
                "score",
                0
            )

        )

        # =====================================
        # CURRENT POSITION
        # =====================================
        if symbol in current_map:

            current_row = current_map[
                symbol
            ]

            current_shares = int(

                current_row.get(
                    "shares",
                    0
                )

            )

            current_allocation = float(

                current_row.get(
                    "allocation_pct",
                    0
                )

            )

        else:

            current_shares = 0

            current_allocation = 0

        # =====================================
        # ALLOCATION DIFFERENCE
        # =====================================
        diff = abs(

            target_allocation

            - current_allocation

        )

        # =====================================
        # SKIP SMALL CHANGES
        # =====================================
        if diff < threshold:

            action = "HOLD"

        elif target_allocation > current_allocation:

            action = "BUY"

        else:

            action = "SELL"

        # =====================================
        # RISK MODEL
        # =====================================
        stop = round(

            current_price * 0.92,

            2

        )

        target_1 = round(

            current_price * 1.12,

            2

        )

        target_2 = round(

            current_price * 1.20,

            2

        )

        risk_pct = round(

            (

                (current_price - stop)

                / current_price

            ) * 100,

            2

        )

        reward_pct = round(

            (

                (target_1 - current_price)

                / current_price

            ) * 100,

            2

        )

        rr_ratio = round(

            reward_pct / risk_pct,

            2

        ) if risk_pct > 0 else 0

        # =====================================
        # ACTION OBJECT
        # =====================================
        actions.append({

            "symbol":
                symbol,

            "action":
                action,

            "score":
                score,

            "target_allocation":
                target_allocation,

            "current_allocation":
                current_allocation,

            "current_price":
                current_price,

            "position_size":
                target_value,

            "recommended_shares":
                recommended_shares,

            "current_shares":
                current_shares,

            "entry_price":
                current_price,

            "stop":
                stop,

            "target_1":
                target_1,

            "target_2":
                target_2,

            "risk_pct":
                risk_pct,

            "reward_pct":
                reward_pct,

            "rr_ratio":
                rr_ratio

        })

    logger.info(

        f"Generated "
        f"{len(actions)} actions"

    )

    return actions