# app/recommendation_engine.py

import pandas as pd

from app.logger import logger


# =====================================
# BUILD ACTION PLAN
# =====================================
def build_action_plan(

    recommended_portfolio,
    positions,
    threshold=0.02

):

    logger.info(
        "Building action plan..."
    )

    actions = []

    # =====================================
    # EMPTY CHECKS
    # =====================================
    if recommended_portfolio is None:

        return actions

    if len(recommended_portfolio) == 0:

        return actions

    # =====================================
    # LOOP RECOMMENDATIONS
    # =====================================
    for _, row in recommended_portfolio.iterrows():

        symbol = row["symbol"]

        target_allocation = float(

            row.get(
                "target_allocation",
                0
            )

        )

        score = float(

            row.get(
                "score",
                0
            )

        )

        current_price = float(

            row.get(
                "current_price",
                0
            )

        )

        position_size = float(

            row.get(
                "position_size",
                0
            )

        )

        recommended_shares = int(

            row.get(
                "recommended_shares",
                0
            )

        )

        # =====================================
        # LOOKUP CURRENT POSITION
        # =====================================
        matching_position = positions[

            positions["symbol"]
            == symbol

        ]

        if not matching_position.empty:

            current_allocation = float(

                matching_position.iloc[0]
                .get(
                    "allocation_pct",
                    0
                )

            )

            current_shares = int(

                matching_position.iloc[0]
                .get(
                    "shares",
                    0
                )

            )

            entry_price = float(

                matching_position.iloc[0]
                .get(
                    "entry_price",
                    current_price
                )

            )

        else:

            current_allocation = 0

            current_shares = 0

            entry_price = current_price

        # =====================================
        # ALLOCATION DIFFERENCE
        # =====================================
        diff = (

            target_allocation
            - current_allocation

        )

        # =====================================
        # DETERMINE ACTION
        # =====================================
        if abs(diff) < threshold:

            action = "HOLD"

        elif diff > 0:

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

        # =====================================
        # RISK / REWARD %
        # =====================================
        if current_price > 0:

            risk_pct = round(

                (
                    (
                        current_price
                        - stop
                    )
                    / current_price
                ) * 100,

                2

            )

            reward_pct = round(

                (
                    (
                        target_1
                        - current_price
                    )
                    / current_price
                ) * 100,

                2

            )

        else:

            risk_pct = 0

            reward_pct = 0

        # =====================================
        # R/R RATIO
        # =====================================
        if risk_pct > 0:

            rr_ratio = round(

                reward_pct
                / risk_pct,

                2

            )

        else:

            rr_ratio = 0

        # =====================================
        # BUILD ACTION OBJECT
        # =====================================
        action_item = {

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
                round(
                    current_price,
                    2
                ),

            "position_size":
                round(
                    position_size,
                    2
                ),

            "recommended_shares":
                recommended_shares,

            "current_shares":
                current_shares,

            "entry_price":
                round(
                    entry_price,
                    2
                ),

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

        }

        actions.append(
            action_item
        )

    logger.info(

        f"Generated "
        f"{len(actions)} actions"

    )

    return actions