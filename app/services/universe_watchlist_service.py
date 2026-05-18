# app/services/universe_watchlist_service.py

import pandas as pd

from app.db_service import (
    query_df
)

from app.logger import logger


# =====================================
# GET UNIVERSE WATCHLIST
# =====================================
def get_universe_watchlist():

    logger.info(
        "Building universe watchlist..."
    )

    df = query_df("""

        SELECT *

        FROM universe_rankings

        ORDER BY
            snapshot_date ASC,
            rank_position ASC

    """)

    if df.empty:

        logger.warning(
            "No universe ranking history found"
        )

        return []

    latest_date = df[
        "snapshot_date"
    ].max()

    latest = df[

        df["snapshot_date"]
        == latest_date

    ].copy()

    rows = []

    for _, row in latest.iterrows():

        symbol = row["symbol"]

        history = df[

            df["symbol"] == symbol

        ].sort_values(
            "snapshot_date"
        )

        # =====================================
        # PREVIOUS DAY
        # =====================================
        previous = (

            history.iloc[-2]

            if len(history) >= 2

            else None

        )

        # =====================================
        # RANK DELTA
        # =====================================
        rank_delta = 0

        if previous is not None:

            rank_delta = int(

                previous[
                    "rank_position"
                ]

            ) - int(

                row[
                    "rank_position"
                ]

            )

        # =====================================
        # SCORE ACCELERATION
        # =====================================
        acceleration = 0

        if previous is not None:

            acceleration = round(

                float(
                    row["score"]
                )

                -

                float(
                    previous["score"]
                ),

                2

            )

        # =====================================
        # DAYS IN TOP 3
        # =====================================
        top3_days = len(

            history[

                history[
                    "rank_position"
                ] <= 3

            ]

        )

        # =====================================
        # TREND ARROW
        # =====================================
        if acceleration > 0.5:

            trend_arrow = "↑"

        elif acceleration < -0.5:

            trend_arrow = "↓"

        else:

            trend_arrow = "→"

        rows.append({

            "symbol":
                symbol,

            "price":
                round(

                    float(
                        row["price"]
                    ),

                    2

                ),

            "score":
                round(

                    float(
                        row["score"]
                    ),

                    2

                ),

            "rank_position":
                int(

                    row[
                        "rank_position"
                    ]

                ),

            "recommended":
                int(

                    row[
                        "recommended"
                    ]

                ),

            "score_gap_to_top":
                round(

                    float(

                        row[
                            "score_gap_to_top"
                        ]

                    ),

                    2

                ),

            "rank_delta":
                rank_delta,

            "acceleration":
                acceleration,

            "top3_days":
                top3_days,

            "trend_arrow":
                trend_arrow

        })

    rows = sorted(

        rows,

        key=lambda x:
            x["rank_position"]

    )

    logger.info(

        f"Built universe watchlist | "
        f"{len(rows)} symbols"

    )

    return rows