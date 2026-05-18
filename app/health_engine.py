# app/health_engine.py

from app.logger import logger

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
# HEALTH THRESHOLDS
# =====================================
MAX_EFFECTIVE_EXPOSURE = 250

MAX_POSITION_SIZE = 50

MIN_CASH_PCT = 5


# =====================================
# BUILD HEALTH REPORT
# =====================================
def get_health_report(

    regime=None,
    risk_report=None

):

    logger.info(
        "Building health report..."
    )

    # =====================================
    # REUSE PRECOMPUTED DEPENDENCIES
    # =====================================
    if risk_report is None:

        risk_report = (
            get_risk_report()
        )

    if regime is None:

        regime_data = (
            determine_market_regime()
        )

    else:

        regime_data = regime

    # =====================================
    # LIVE PORTFOLIO
    # =====================================
    live_portfolio = (
        get_live_portfolio()
    )

    positions = live_portfolio[
        "positions"
    ]

    warnings = []

    health_score = 100

    # =====================================
    # EFFECTIVE EXPOSURE
    # =====================================
    effective_exposure = float(

        risk_report.get(
            "effective_exposure",
            0
        )

    )

    if effective_exposure > MAX_EFFECTIVE_EXPOSURE:

        warnings.append({

            "level": "HIGH",

            "message":

                f"Effective exposure "
                f"is very high "
                f"({effective_exposure:.1f}%)"

        })

        health_score -= 30

    # =====================================
    # CONCENTRATION RISK
    # =====================================
    largest_position = float(

        risk_report.get(
            "largest_position",
            0
        )

    )

    if largest_position > MAX_POSITION_SIZE:

        warnings.append({

            "level": "MEDIUM",

            "message":

                f"Largest position "
                f"exceeds "
                f"{MAX_POSITION_SIZE}% "

                f"({largest_position:.1f}%)"

        })

        health_score -= 20

    # =====================================
    # CASH RISK
    # =====================================
    cash_pct = float(

        risk_report.get(
            "cash_pct",
            0
        )

    )

    if cash_pct < MIN_CASH_PCT:

        warnings.append({

            "level": "MEDIUM",

            "message":

                f"Cash reserves are low "
                f"({cash_pct:.1f}%)"

        })

        health_score -= 15

    # =====================================
    # REGIME CONFLICT
    # =====================================
    current_regime = regime_data.get(

        "regime",

        "UNKNOWN"

    )

    if current_regime != "RISK_ON":

        leveraged_symbols = [

            "TQQQ",
            "SOXL",
            "TECL",
            "UPRO",
            "SPXL",
            "USD",
            "QLD"

        ]

        conflict_positions = []

        if not positions.empty:

            for _, row in positions.iterrows():

                symbol = row["symbol"]

                shares = int(
                    row["shares"]
                )

                if (

                    symbol
                    in leveraged_symbols

                    and

                    shares > 0

                ):

                    conflict_positions.append(
                        symbol
                    )

        if len(conflict_positions) > 0:

            warnings.append({

                "level": "HIGH",

                "message":

                    "Leveraged long exposure "
                    "during RISK_OFF regime: "

                    + ", ".join(
                        conflict_positions
                    )

            })

            health_score -= 40

    # =====================================
    # DETERMINE STATUS
    # =====================================
    if health_score >= 90:

        overall_status = (
            "Excellent"
        )

    elif health_score >= 75:

        overall_status = (
            "Healthy"
        )

    elif health_score >= 50:

        overall_status = (
            "Elevated Risk"
        )

    else:

        overall_status = (
            "Danger"
        )

    logger.info(
        "Health report complete"
    )

    return {

        "status":
            overall_status,

        "score":
            max(
                health_score,
                0
            ),

        "warnings":
            warnings,

        "warning_count":
            len(warnings),

        "effective_exposure":
            effective_exposure,

        "largest_position":
            largest_position,

        "cash_pct":
            cash_pct,

        "regime":
            current_regime

    }
# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    report = (
        get_health_report()
    )

    print(
        "\n===== PORTFOLIO HEALTH =====\n"
    )

    print(
        f"Status: "
        f"{report['status']}"
    )

    print(
        f"Score: "
        f"{report['score']}"
    )

    print(
        f"Warnings: "
        f"{report['warning_count']}"
    )

    print()

    for w in report["warnings"]:

        print(

            f"[{w['level']}] "
            f"{w['message']}"

        )