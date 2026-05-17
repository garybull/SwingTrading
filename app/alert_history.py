# app/alert_history.py

from datetime import datetime

from app.logger import logger

from app.db_service import (

    execute,
    query_df

)

from app.alert_engine import (
    get_alert_report
)


# =====================================
# SAVE ALERT SNAPSHOT
# =====================================
def save_alert_snapshot():

    logger.info(
        "Saving alert snapshot..."
    )

    report = (
        get_alert_report()
    )

    alerts = report[
        "alerts"
    ]

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # =====================================
    # SAVE EMPTY STATE
    # =====================================
    if len(alerts) == 0:

        execute("""

            INSERT INTO alert_history (

                date,
                timestamp,
                status,
                source,
                level,
                message

            )

            VALUES (?, ?, ?, ?, ?, ?)

        """, (

            today,

            timestamp,

            report["status"],

            "SYSTEM",

            "NORMAL",

            "No active alerts"

        ))

        logger.info(
            "Saved normal alert state"
        )

        return

    # =====================================
    # SAVE ALERTS
    # =====================================
    for alert in alerts:

        execute("""

            INSERT INTO alert_history (

                date,
                timestamp,
                status,
                source,
                level,
                message

            )

            VALUES (?, ?, ?, ?, ?, ?)

        """, (

            today,

            timestamp,

            report["status"],

            alert["source"],

            alert["level"],

            alert["message"]

        ))

    logger.info(

        f"Saved "
        f"{len(alerts)} alerts"

    )


# =====================================
# LOAD RECENT ALERT HISTORY
# =====================================
def load_alert_history(

    limit=100

):

    logger.info(
        "Loading alert history..."
    )

    return query_df("""

        SELECT *

        FROM alert_history

        ORDER BY timestamp DESC

        LIMIT ?

    """, (

        limit,

    ))


# =====================================
# LOAD ALERT STATS
# =====================================
def get_alert_stats():

    logger.info(
        "Building alert stats..."
    )

    df = query_df("""

        SELECT *

        FROM alert_history

    """)

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if df is None or df.empty:

        return {

            "total_alerts": 0,

            "high_alerts": 0,

            "medium_alerts": 0,

            "normal_states": 0,

            "most_common_source":
                "N/A"

        }

    total_alerts = len(df)

    high_alerts = len(

        df[
            df["level"] == "HIGH"
        ]

    )

    medium_alerts = len(

        df[
            df["level"] == "MEDIUM"
        ]

    )

    normal_states = len(

        df[
            df["level"] == "NORMAL"
        ]

    )

    # =====================================
    # MOST COMMON SOURCE
    # =====================================
    if "source" in df.columns:

        most_common_source = (

            df["source"]
            .value_counts()

            .idxmax()

        )

    else:

        most_common_source = (
            "N/A"
        )

    return {

        "total_alerts":
            total_alerts,

        "high_alerts":
            high_alerts,

        "medium_alerts":
            medium_alerts,

        "normal_states":
            normal_states,

        "most_common_source":
            most_common_source

    }


# =====================================
# PRINT ALERT HISTORY
# =====================================
def print_alert_history():

    history = (
        load_alert_history()
    )

    print(
        "\n===== ALERT HISTORY =====\n"
    )

    if history.empty:

        print(
            "No alert history found."
        )

        return

    for _, row in history.iterrows():

        print(

            f"{row['timestamp']} | "

            f"{row['level']} | "

            f"{row['source']} | "

            f"{row['message']}"

        )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    save_alert_snapshot()

    print_alert_history()