# app/scan_engine.py

from datetime import datetime

from app.config import (
    ENABLE_REBALANCE_LOGGING
)

from app.logger import logger

from app.ranking_engine import (
    run_rankings
)

from app.portfolio_builder import (
    run_portfolio_builder,
    load_recommended_portfolio
)

from app.action_engine import (
    build_action_plan
)

from app.db_service import (
    query_df,
    execute
)


# =====================================
# LOAD CURRENT POSITIONS
# =====================================
def load_positions():

    return query_df("""

        SELECT *

        FROM positions

        ORDER BY market_value DESC

    """)


# =====================================
# SAVE REBALANCE ACTIONS
# =====================================
def save_rebalance_actions(actions):

    if not ENABLE_REBALANCE_LOGGING:

        logger.warning(
            "Rebalance logging disabled"
        )

        return

    if len(actions) == 0:

        logger.warning(
            "No rebalance actions to save"
        )

        return

    logger.info(
        "Saving rebalance actions..."
    )

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    for action in actions:

        execute("""

            INSERT INTO rebalance_log (

                date,
                symbol,
                action,
                shares,
                price,
                allocation_pct,
                reason

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

        """, (

            today,

            action.get(
                "symbol",
                ""
            ),

            action.get(
                "action",
                ""
            ),

            int(

                action.get(
                    "recommended_shares",
                    0
                )

            ),

            float(

                action.get(
                    "current_price",
                    0
                )

            ),

            float(

                action.get(
                    "target_allocation",
                    0
                )

            ),

            f"Momentum Score: "

            f"{round(action.get('score', 0), 2)}"

        ))

    logger.info(

        f"Saved {len(actions)} "
        f"rebalance actions"

    )


# =====================================
# RUN FULL SCAN PIPELINE
# =====================================
def run_scan():

    logger.info(
        "Starting full scan pipeline..."
    )

    # =====================================
    # STEP 1: BUILD RANKINGS
    # =====================================
    rankings = run_rankings()

    if rankings.empty:

        logger.warning(
            "No rankings generated"
        )

        return []

    logger.info(
        f"{len(rankings)} rankings built"
    )

    # =====================================
    # STEP 2: BUILD PORTFOLIO
    # =====================================
    portfolio = (
        run_portfolio_builder()
    )

    if portfolio.empty:

        logger.warning(
            "No portfolio generated"
        )

        return []

    logger.info(

        f"{len(portfolio)} "
        f"portfolio positions built"

    )

    # =====================================
    # STEP 3: LOAD POSITIONS
    # =====================================
    positions = load_positions()

    # =====================================
    # STEP 4: LOAD RECOMMENDATIONS
    # =====================================
    recommended = (
        load_recommended_portfolio()
    )

    # =====================================
    # STEP 5: BUILD ACTION PLAN
    # =====================================
    logger.info(
        "Building action plan..."
    )

    actions = build_action_plan(

        recommended,

        positions

    )

    logger.info(

        f"Generated "
        f"{len(actions)} actions"

    )

    # =====================================
    # STEP 6: SAVE REBALANCE LOG
    # =====================================
    save_rebalance_actions(
        actions
    )

    logger.info(
        "Scan pipeline complete"
    )

    return actions


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    actions = run_scan()

    print("\n===== ACTIONS =====\n")

    for action in actions:

        print(action)