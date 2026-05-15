# app/action_engine.py

import pandas as pd
from app.config import (START_CAPITAL)
from app.logger import logger
from app.db_service import (
    query_df
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

    total_equity = 0

    if current_positions is not None:

        if len(current_positions) > 0:

            current_map = {

                row["symbol"]: row

                for _, row

                in current_positions.iterrows()

            }

            # =====================================
            # TOTAL EQUITY
            # =====================================
            # =====================================
            # LOAD TOTAL SYSTEM EQUITY
            # =====================================
            state = query_df("""

                SELECT
                    current_equity

                FROM system_state

                WHERE id = 1

            """)

            if not state.empty:

                total_equity = float(

                    state.iloc[0][
                        "current_equity"
                    ]

                )

            else:

                total_equity = START_CAPITAL

    # =====================================
    # FALLBACK
    # =====================================
    if total_equity <= 0:

        total_equity = START_CAPITAL

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
        # REQUIRED REBALANCE DELTA
        # =====================================
        allocation_delta = (

            target_allocation

            - current_allocation

        )

        # =====================================
        # ACTION TYPE
        # =====================================
        if abs(allocation_delta) < threshold:

            action = "HOLD"

        elif allocation_delta > 0:

            action = "BUY"

        else:

            action = "SELL"

        # =====================================
        # REQUIRED POSITION VALUE
        # =====================================
        # =====================================
        # TARGET POSITION VALUE
        # =====================================
        target_position_value = (

            total_equity

            * target_allocation

        )

        # =====================================
        # REQUIRED TRADE VALUE
        # =====================================
        required_value = abs(

            target_position_value

            - current_market_value

        )

        # =====================================
        # REQUIRED SHARES
        # =====================================
        required_shares = 0

        if current_price > 0:

            required_shares = int(

                required_value

                / current_price

            )


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

            "allocation_delta":
                allocation_delta,

            "current_price":
                current_price,

            # FINAL TARGET POSITION
            "target_position_value":
                target_position_value,

            # REQUIRED TRADE SIZE
            "position_size":
                required_value,

            "recommended_shares":
                required_shares,

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