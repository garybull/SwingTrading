# app/system_snapshot.py

from app.logger import logger

from app.portfolio import (
    get_dashboard_data
)

from app.regime_engine import (
    load_latest_regime,
    get_suggested_exposure
)

from app.risk_engine import (
    get_risk_report
)

from app.health_engine import (
    get_health_report
)

from app.drawdown_engine import (
    get_drawdown_report
)

from app.alert_engine import (
    get_alert_report
)


# =====================================
# BUILD SYSTEM SNAPSHOT
# =====================================
def get_system_snapshot():

    logger.info(
        "Building system snapshot..."
    )

    # =====================================
    # CORE DASHBOARD DATA
    # =====================================
    dashboard_data = (
        get_dashboard_data()
    )

    # =====================================
    # REGIME
    # =====================================
    regime = (
        load_latest_regime()
    )

    suggested_exposure = (
        get_suggested_exposure()
    )

    # =====================================
    # RISK
    # =====================================
    risk_report = (
        get_risk_report()
    )

    # =====================================
    # HEALTH
    # =====================================
    health_report = (
        get_health_report()
    )

    # =====================================
    # DRAWDOWN
    # =====================================
    drawdown_report = (
        get_drawdown_report()
    )

    # =====================================
    # ALERTS
    # =====================================
    alert_report = (
        get_alert_report()
    )

    snapshot = {

        # CORE
        "dashboard_data":
            dashboard_data,

        # REGIME
        "regime":
            regime,

        "suggested_exposure":
            suggested_exposure,

        # RISK
        "risk_report":
            risk_report,

        # HEALTH
        "health_report":
            health_report,

        # DRAWDOWN
        "drawdown_report":
            drawdown_report,

        # ALERTS
        "alert_report":
            alert_report

    }

    logger.info(
        "System snapshot complete"
    )

    return snapshot


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    snapshot = (
        get_system_snapshot()
    )

    print(
        "\n===== SYSTEM SNAPSHOT =====\n"
    )

    for k in snapshot.keys():

        print(k)