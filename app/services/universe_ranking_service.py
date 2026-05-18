# app/services/universe_ranking_service.py

from datetime import datetime

from app.db_service import (
    execute
)

from app.logger import logger


# =====================================
# SAVE UNIVERSE SNAPSHOT
# =====================================
def save_universe_snapshot(

    rankings,
    regime

):

    logger.info(
        "Saving universe snapshot..."
    )

    snapshot_date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    if len(rankings) == 0:

        logger.warning(
            "No rankings provided"
        )

        return

    top_score = float(
        rankings[0]["score"]
    )

    buy_cutoff_score = float(
        rankings[0]["score"]
    )

    rows = []

    for i, row in enumerate(rankings):

        score = float(
            row["score"]
        )

        rows.append((

            snapshot_date,

            row["symbol"],

            float(
                row.get(
                    "price",
                    0
                )
            ),

            score,

            i + 1,

            1 if i == 0 else 0,

            top_score - score,

            buy_cutoff_score - score,

            float(
                row.get(
                    "momentum",
                    0
                )
            ),

            float(
                row.get(
                    "momentum_acceleration",
                    0
                )
            ),

            float(
                row.get(
                    "volatility",
                    0
                )
            ),

            regime

        ))

    execute("""

        DELETE FROM universe_rankings

        WHERE snapshot_date = ?

    """, (

        snapshot_date,

    ))

    conn_sql = """

        INSERT INTO universe_rankings (

            snapshot_date,
            symbol,
            price,
            score,
            rank_position,
            recommended,
            score_gap_to_top,
            score_gap_to_buy_cutoff,
            momentum_20d,
            momentum_acceleration,
            volatility,
            regime

        )

        VALUES (

            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?

        )

    """

    from app.db_service import (
        executemany
    )

    executemany(
        conn_sql,
        rows
    )

    logger.info(

        f"Saved "
        f"{len(rows)} "
        f"universe ranking snapshots"

    )