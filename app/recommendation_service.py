# app/recommendation_service.py

from app.db_service import (
    query_df
)

from app.logger import logger

from app.action_engine import (
    build_action_plan
)

from app.chart_engine import (
    build_recommendation_chart
)
from app.live_portfolio import (
    get_live_portfolio
)
# =====================================
# LOAD POSITIONS
# =====================================
def load_positions():

    return query_df("""

        SELECT *

        FROM positions

        ORDER BY market_value DESC

    """)


# =====================================
# LOAD RECOMMENDED PORTFOLIO
# =====================================
def load_recommended_portfolio():

    return query_df("""

        SELECT *

        FROM recommended_portfolio

        ORDER BY score DESC

    """)


# =====================================
# BUILD RECOMMENDATIONS PAGE
# =====================================
def build_recommendations_page():

    logger.info(
        "Building recommendations page..."
    )

    # =====================================
    # LOAD DATA
    # =====================================
    recommended = (
        load_recommended_portfolio()
    )

    live_portfolio = (
        get_live_portfolio()
    )

    positions = (
        live_portfolio[
            "positions"
        ]
    )

    # =====================================
    # BUILD ACTIONS
    # =====================================
    actions = build_action_plan(

        recommended,

        positions

    )

    logger.info(

        f"Generated "
        f"{len(actions)} actions"

    )

    # =====================================
    # BUILD CHARTS
    # =====================================
    for action in actions:

        try:

            symbol = action[
                "symbol"
            ]

            logger.info(

                f"Building chart for "
                f"{symbol}"

            )

            chart_data = (
                build_recommendation_chart(
                    symbol
                )
            )

            # =====================================
            # EMBED CHART
            # =====================================
            action["chart"] = (
                chart_data["chart"]
            )

            # =====================================
            # OPTIONAL OVERRIDES
            # =====================================
            action["entry_price"] = (

                chart_data.get(

                    "entry",

                    action.get(
                        "entry_price",
                        0
                    )

                )

            )

            action["stop"] = (

                chart_data.get(

                    "stop",

                    action.get(
                        "stop",
                        0
                    )

                )

            )

            action["target_1"] = (

                chart_data.get(

                    "target_1",

                    action.get(
                        "target_1",
                        0
                    )

                )

            )

            action["target_2"] = (

                chart_data.get(

                    "target_2",

                    action.get(
                        "target_2",
                        0
                    )

                )

            )

            action["risk_pct"] = (

                chart_data.get(

                    "risk_pct",

                    action.get(
                        "risk_pct",
                        0
                    )

                )

            )

            action["reward_pct"] = (

                chart_data.get(

                    "reward_pct",

                    action.get(
                        "reward_pct",
                        0
                    )

                )

            )

            action["rr_ratio"] = (

                chart_data.get(

                    "rr_ratio",

                    action.get(
                        "rr_ratio",
                        0
                    )

                )

            )

            logger.info(

                f"Chart complete for "
                f"{symbol}"

            )

        except Exception as e:

            logger.error(

                f"Chart failed for "
                f"{action['symbol']}: {e}"

            )

            action["chart"] = None

    logger.info(
        "Recommendations page built"
    )

    return {

        "actions":
            actions,

        "positions":
            positions.to_dict(
                "records"
            )

    }