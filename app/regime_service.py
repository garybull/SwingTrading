# app/regime_service.py

from datetime import datetime

from app.regime_engine import (
    determine_market_regime
)

from app.db_service import (
    execute
)

from app.logger import logger


# =====================================
# SAVE REGIME SNAPSHOT
# =====================================
def save_regime_snapshot():

    regime = determine_market_regime()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # =====================================
    # REMOVE EXISTING DAILY ENTRY
    # =====================================
    execute("""

        DELETE FROM regime_history

        WHERE date = ?

    """, (

        today,

    ))

    # =====================================
    # INSERT SNAPSHOT
    # =====================================
    execute("""

        INSERT INTO regime_history (

            date,
            regime,
            vix,
            spy_close,
            spy_200dma,
            qqq_close,
            qqq_200dma

        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

    """, (

        today,

        regime["regime"],

        regime["vix"],

        regime["spy_close"],

        regime["spy_200dma"],

        regime["qqq_close"],

        regime["qqq_200dma"]

    ))

    logger.info(

        f"Regime snapshot saved | "
        f"{regime['regime']}"

    )

    return regime

# =====================================
# LOAD LATEST REGIME
# =====================================
def load_latest_regime():

    from app.db_service import (
        query_df
    )

    df = query_df("""

        SELECT *

        FROM regime_history

        ORDER BY date DESC

        LIMIT 1

    """)

    if df.empty:

        return {

            "regime": "UNKNOWN"

        }

    return df.iloc[0].to_dict()

# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    save_regime_snapshot()