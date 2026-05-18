# app/alert_engine.py

from datetime import datetime

from app.logger import logger

from app.health_engine import (
    get_health_report
)

from app.drawdown_engine import (
    get_drawdown_report
)

from app.risk_engine import (
    get_risk_report
)

from app.regime_engine import (
    determine_market_regime
)

from app.live_portfolio import (
    get_live_portfolio
)


# =====================================
# BUILD ALERT REPORT
# =====================================
def get_alert_report(
        health_report=None
):

    logger.info(
        "Building alert report..."
    )

    alerts = []

    # =====================================
    # LOAD ENGINES
    # =====================================
    if health_report is None:

        health_report = (
            get_health_report()
        )

    drawdown_report = (
        get_drawdown_report()
    )

    risk_report = (
        get_risk_report()
    )

    regime_data = (
        determine_market_regime()
    )

    portfolio = (
        get_live_portfolio()
    )

    positions = portfolio[
        "positions"
    ]

    # =====================================
    # HEALTH ALERTS
    # =====================================
    for warning in health_report[
        "warnings"
    ]:

        alerts.append({

            "source":
                "HEALTH",

            "level":
                warning["level"],

            "message":
                warning["message"]

        })

    # =====================================
    # DRAWDOWN ALERTS
    # =====================================
    for warning in drawdown_report[
        "alerts"
    ]:

        alerts.append({

            "source":
                "DRAWDOWN",

            "level":
                warning["level"],

            "message":
                warning["message"]

        })

    # =====================================
    # EXTREME EXPOSURE
    # =====================================
    effective_exposure = float(

        risk_report[
            "effective_exposure"
        ]

    )

    if effective_exposure >= 275:

        alerts.append({

            "source":
                "RISK",

            "level":
                "HIGH",

            "message":

                f"Extreme exposure detected "
                f"({effective_exposure:.1f}%)"

        })

    # =====================================
    # REGIME CONFLICT
    # =====================================
    if (

        regime_data["regime"]

        != "RISK_ON"

        and

        positions is not None

        and

        len(positions) > 0

    ):

        alerts.append({

            "source":
                "REGIME",

            "level":
                "HIGH",

            "message":

                "Portfolio has open "
                "positions during "
                "RISK_OFF regime"

        })

    # =====================================
    # CASH WARNING
    # =====================================
    cash_pct = float(

        risk_report[
            "cash_pct"
        ]

    )

    if cash_pct < 3:

        alerts.append({

            "source":
                "LIQUIDITY",

            "level":
                "MEDIUM",

            "message":

                f"Cash reserves critically "
                f"low ({cash_pct:.1f}%)"

        })

    # =====================================
    # DETERMINE STATUS
    # =====================================
    high_alerts = len([

        a for a in alerts

        if a["level"] == "HIGH"

    ])

    medium_alerts = len([

        a for a in alerts

        if a["level"] == "MEDIUM"

    ])

    if high_alerts > 0:

        overall_status = (
            "CRITICAL"
        )

    elif medium_alerts > 0:

        overall_status = (
            "WARNING"
        )

    else:

        overall_status = (
            "NORMAL"
        )

    logger.info(

        f"Alert report complete | "
        f"{len(alerts)} alerts"

    )

    return {

        "status":
            overall_status,

        "alerts":
            alerts,

        "total_alerts":
            len(alerts),

        "high_alerts":
            high_alerts,

        "medium_alerts":
            medium_alerts,

        "timestamp":

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    }


# =====================================
# PRINT ALERTS
# =====================================
def print_alert_report():

    report = (
        get_alert_report()
    )

    print(
        "\n===== ALERT REPORT =====\n"
    )

    print(
        f"Status: "
        f"{report['status']}"
    )

    print(
        f"Total Alerts: "
        f"{report['total_alerts']}"
    )

    print()

    if report["total_alerts"] == 0:

        print(
            "✅ No active alerts"
        )

    else:

        for alert in report[
            "alerts"
        ]:

            print(

                f"[{alert['level']}] "

                f"{alert['source']} | "

                f"{alert['message']}"

            )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    print_alert_report()