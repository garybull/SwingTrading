# app/recommendation_service.py
import pandas as pd

from app.config import (
    DB_NAME
)
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

    positions = load_positions()

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

            logger.info(

                f"Building chart for "
                f"{action['symbol']}"

            )

            action["chart"] = (

                build_recommendation_chart(

                    symbol=action[
                        "symbol"
                    ],

                    entry=action[
                        "entry_price"
                    ],

                    stop=action[
                        "stop"
                    ],

                    target_1=action[
                        "target_1"
                    ],

                    target_2=action[
                        "target_2"
                    ]

                )

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

        "actions": actions

    }