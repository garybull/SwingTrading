# app/action_engine.py

import pandas as pd

from app.logger import logger

from app.regime_engine import (
    determine_market_regime
)


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
    # MARKET REGIME
    # =====================================
    regime_data = (
        determine_market_regime()
    )

    regime = regime_data[
        "regime"
    ]

    logger.info(

        f"Current regime: "
        f"{regime}"

    )

    # =====================================
    # CURRENT POSITIONS MAP
    # =====================================
    current_map = {}

    if (

        current_positions is not None

        and

        len(current_positions) > 0

    ):

        current_map = {

            row["symbol"]: row

            for _, row

            in current_positions.iterrows()

        }

    # =====================================
    # RISK OFF
    # MATCH BACKTEST
    # =====================================
    if regime != "RISK_ON":

        logger.warning(

            "Risk-off regime detected. "
            "Generating liquidation plan."

        )

        for symbol, row in current_map.items():

            current_price = float(

                row.get(
                    "current_price",
                    0
                )

            )

            current_shares = int(

                row.get(
                    "shares",
                    0
                )

            )

            current_market_value = float(

                row.get(
                    "market_value",
                    0
                )

            )

            if current_shares <= 0:

                continue

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

            rr_ratio = round(

                reward_pct / risk_pct,

                2

            ) if risk_pct > 0 else 0

            actions.append({

                "symbol":
                    symbol,

                "action":
                    "SELL",

                "score":
                    0,

                "target_allocation":
                    0,

                "current_allocation":

                    float(

                        row.get(
                            "allocation_pct",
                            0
                        )

                    ),

                "allocation_delta":

                    -float(

                        row.get(
                            "allocation_pct",
                            0
                        )

                    ),

                "current_price":
                    current_price,

                "target_position_value":
                    0,

                "position_size":
                    current_market_value,

                "recommended_shares":
                    0,

                "current_shares":
                    current_shares,

                "current_market_value":
                    current_market_value,

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
            f"{len(actions)} "
            f"risk-off liquidation actions"

        )

        return actions

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if recommended_portfolio is None:

        return []

    if len(recommended_portfolio) == 0:

        return []

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

        target_position_value = float(

            row.get(
                "target_value",
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

            current_market_value = float(

                current_row.get(
                    "market_value",
                    0
                )

            )

        else:

            current_shares = 0

            current_allocation = 0

            current_market_value = 0

        # =====================================
        # ALLOCATION DIFFERENCE
        # =====================================
        allocation_delta = (

            target_allocation

            - current_allocation

        )

        # =====================================
        # POSITION SIZE DIFFERENCE
        # =====================================
        position_size = max(

            target_position_value

            - current_market_value,

            0

        )

        # =====================================
        # SHARES TO BUY
        # =====================================
        recommended_shares = int(

            position_size
            / current_price

        ) if current_price > 0 else 0

        # =====================================
        # DETERMINE ACTION
        # =====================================
        if abs(allocation_delta) < threshold:

            action = "HOLD"

        elif allocation_delta > 0:

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

            "allocation_delta":
                allocation_delta,

            "current_price":
                current_price,

            "target_position_value":
                target_position_value,

            "position_size":
                position_size,

            "recommended_shares":
                recommended_shares,

            "current_shares":
                current_shares,

            "current_market_value":
                current_market_value,

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