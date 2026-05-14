# app/ranking_engine.py

import pandas as pd
from datetime import datetime

from app.config import (
    UNIVERSE
)

from app.strategy import (
    score_asset
)

from app.logger import logger

from app.market_data_service import (
    get_historical_data
)

from app.db_service import (
    query_df,
    execute
)


# =====================================
# BUILD RANKINGS
# =====================================
def build_rankings():

    logger.info(
        "Building momentum rankings..."
    )

    rankings = []

    # =====================================
    # SCORE EACH SYMBOL
    # =====================================
    for symbol in UNIVERSE:

        df = get_historical_data(
            symbol
        )

        if df is None:

            continue

        result = score_asset(

            df,

            symbol

        )

        if result is None:

            continue

        rankings.append(result)

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if len(rankings) == 0:

        logger.warning(
            "No rankings generated"
        )

        return pd.DataFrame()

    # =====================================
    # DATAFRAME
    # =====================================
    rankings_df = pd.DataFrame(
        rankings
    )

    rankings_df = rankings_df.sort_values(

        "score",

        ascending=False

    ).reset_index(drop=True)

    rankings_df["rank"] = (
        rankings_df.index + 1
    )

    logger.info(

        f"Generated "
        f"{len(rankings_df)} rankings"

    )

    return rankings_df


# =====================================
# SAVE RANKINGS
# =====================================
def save_rankings(rankings_df):

    logger.info(
        "Saving rankings..."
    )

    if rankings_df.empty:

        logger.warning(
            "No rankings to save"
        )

        return

    # =====================================
    # CLEAR OLD RANKINGS
    # =====================================
    execute("""

        DELETE FROM rankings

    """)

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # =====================================
    # INSERT NEW RANKINGS
    # =====================================
    for _, row in rankings_df.iterrows():

        execute("""

            INSERT INTO rankings (

                date,
                rank,
                symbol,
                score,
                close,
                mom_1m,
                mom_3m,
                mom_6m,
                volatility

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            today,

            int(row["rank"]),

            row["symbol"],

            float(row["score"]),

            float(row["close"]),

            float(row["mom_1m"]),

            float(row["mom_3m"]),

            float(row["mom_6m"]),

            float(row["volatility"])

        ))

    logger.info(
        "Rankings saved"
    )


# =====================================
# LOAD RANKINGS
# =====================================
def load_rankings():

    return query_df("""

        SELECT *

        FROM rankings

        ORDER BY rank ASC

    """)


# =====================================
# RUN FULL RANKING PIPELINE
# =====================================
def run_rankings():

    rankings_df = build_rankings()

    if rankings_df.empty:

        return rankings_df

    save_rankings(
        rankings_df
    )

    return rankings_df


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    run_rankings()