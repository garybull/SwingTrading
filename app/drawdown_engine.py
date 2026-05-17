# app/drawdown_engine.py

import pandas as pd

from app.logger import logger

from app.db_service import (
    query_df
)


# =====================================
# LOAD EQUITY CURVE
# =====================================
def load_equity_curve():

    df = query_df("""

        SELECT
            date,
            equity

        FROM portfolio_history

        ORDER BY date ASC

    """)

    if df is None or df.empty:

        return pd.DataFrame()

    return df


# =====================================
# CALCULATE DRAWDOWN SERIES
# =====================================
def calculate_drawdowns(

    equity_curve

):

    if equity_curve.empty:

        return equity_curve

    equity_curve = (
        equity_curve.copy()
    )

    equity_curve[
        "rolling_peak"
    ] = equity_curve[
        "equity"
    ].cummax()

    equity_curve[
        "drawdown_pct"
    ] = (

        (
            equity_curve["equity"]

            / equity_curve[
                "rolling_peak"
            ]

        ) - 1

    ) * 100

    return equity_curve


# =====================================
# BUILD DRAWDOWN REPORT
# =====================================
def get_drawdown_report():

    logger.info(
        "Building drawdown report..."
    )

    equity_curve = (
        load_equity_curve()
    )

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if equity_curve.empty:

        return {

            "current_drawdown": 0,

            "max_drawdown": 0,

            "drawdown_change_5d": 0,

            "drawdown_change_30d": 0,

            "days_underwater": 0,

            "status": "No Data",

            "alerts": []

        }

    # =====================================
    # CALCULATE DRAWDOWNS
    # =====================================
    equity_curve = (
        calculate_drawdowns(
            equity_curve
        )
    )

    current_drawdown = float(

        equity_curve[
            "drawdown_pct"
        ].iloc[-1]

    )

    max_drawdown = float(

        equity_curve[
            "drawdown_pct"
        ].min()

    )

    # =====================================
    # ROLLING CHANGES
    # =====================================
    drawdown_change_5d = 0

    drawdown_change_30d = 0

    if len(equity_curve) >= 5:

        drawdown_change_5d = (

            current_drawdown

            - float(

                equity_curve[
                    "drawdown_pct"
                ].iloc[-5]

            )

        )

    if len(equity_curve) >= 30:

        drawdown_change_30d = (

            current_drawdown

            - float(

                equity_curve[
                    "drawdown_pct"
                ].iloc[-30]

            )

        )

    # =====================================
    # DAYS UNDERWATER
    # =====================================
    underwater = equity_curve[

        equity_curve[
            "drawdown_pct"
        ] < 0

    ]

    days_underwater = len(
        underwater
    )

    # =====================================
    # ALERTS
    # =====================================
    alerts = []

    # Severe DD
    if current_drawdown <= -15:

        alerts.append({

            "level": "HIGH",

            "message":

                f"Severe drawdown: "
                f"{current_drawdown:.2f}%"

        })

    # Rapid deterioration
    if drawdown_change_5d <= -5:

        alerts.append({

            "level": "HIGH",

            "message":

                f"Drawdown worsening "
                f"rapidly over 5 days "
                f"({drawdown_change_5d:.2f}%)"

        })

    # Medium DD
    elif current_drawdown <= -8:

        alerts.append({

            "level": "MEDIUM",

            "message":

                f"Elevated drawdown: "
                f"{current_drawdown:.2f}%"

        })

    # =====================================
    # STATUS
    # =====================================
    if current_drawdown >= -3:

        status = "Healthy"

    elif current_drawdown >= -8:

        status = "Moderate Stress"

    elif current_drawdown >= -15:

        status = "Elevated Risk"

    else:

        status = "Critical"

    logger.info(
        "Drawdown report complete"
    )

    return {

    "current_drawdown":

        round(
            current_drawdown,
            2
        ),

    "max_drawdown":

        round(
            abs(max_drawdown),
            2
        ),

    "drawdown_change_5d":

        round(
            drawdown_change_5d,
            2
        ),

    "drawdown_change_30d":

        round(
            drawdown_change_30d,
            2
        ),

    "days_underwater":
        days_underwater,

    "status":
        status,

    "alerts":
        alerts,

    "alert_count":
        len(alerts)

}


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    report = (
        get_drawdown_report()
    )

    print(
        "\n===== DRAWDOWN REPORT =====\n"
    )

    for k, v in report.items():

        print(f"{k}: {v}")