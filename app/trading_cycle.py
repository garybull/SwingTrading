# app/trading_cycle.py

from datetime import datetime

from app.logger import logger

from app.scan_engine import (
    run_scan
)

from app.execution_engine import (
    execute_action_plan
)

from app.portfolio_state import (
    refresh_system_state
)

from app.emailer import (
    send_email
)
from app.config import (
    AUTO_EXECUTE,
    SEND_SUMMARY_EMAIL
 )


# =====================================
# VALIDATE ACTIONS
# =====================================
def validate_actions(actions):

    logger.info(
        "Validating actions..."
    )

    valid = []

    for action in actions:

        symbol = action.get(
            "symbol"
        )

        side = action.get(
            "action"
        )

        shares = int(

            action.get(
                "recommended_shares",
                0
            )

        )

        price = float(

            action.get(
                "current_price",
                0
            )

        )

        # =====================================
        # BASIC VALIDATION
        # =====================================
        if not symbol:

            continue

        if side not in [

            "BUY",
            "SELL",
            "HOLD"

        ]:

            continue

        if shares <= 0:

            continue

        if price <= 0:

            continue

        valid.append(action)

    logger.info(

        f"Validated "
        f"{len(valid)} actions"

    )

    return valid


# =====================================
# BUILD SUMMARY EMAIL
# =====================================
def build_summary_email(

    actions,
    execution_results

):

    lines = []

    lines.append(
        "TRADING CYCLE COMPLETE"
    )

    lines.append("")

    lines.append(

        f"Timestamp: "
        f"{datetime.now()}"

    )

    lines.append("")

    lines.append(
        "ACTIONS"
    )

    lines.append(
        "===================="
    )

    if len(actions) == 0:

        lines.append(
            "No actions generated"
        )

    else:

        for action in actions:

            lines.append(

                f"{action['action']} "

                f"{action['recommended_shares']} "

                f"{action['symbol']} "

                f"@ "

                f"${round(action['current_price'], 2)}"

            )

    lines.append("")
    lines.append(
        "EXECUTION RESULTS"
    )

    lines.append(
        "===================="
    )

    if len(execution_results) == 0:

        lines.append(
            "No executions"
        )

    else:

        for result in execution_results:

            status = (

                "SUCCESS"

                if result["success"]

                else "FAILED"

            )

            lines.append(

                f"{result['action']} "

                f"{result['symbol']} "

                f"{status}"

            )

    return "\n".join(lines)


# =====================================
# SEND SUMMARY
# =====================================
def send_cycle_summary(

    actions,
    execution_results

):

    try:

        subject = (
            "Trading Cycle Summary"
        )

        body = build_summary_email(

            actions,

            execution_results

        )

        send_email(
            subject,
            body
        )

        logger.info(
            "Summary email sent"
        )

    except Exception as e:

        logger.error(

            f"Summary email failed: "
            f"{e}"

        )


# =====================================
# RUN TRADING CYCLE
# =====================================
def run_trading_cycle():

    logger.info(
        "Starting trading cycle..."
    )

    # =====================================
    # STEP 1: SCAN
    # =====================================
    actions = run_scan()

    logger.info(

        f"Generated "
        f"{len(actions)} actions"

    )

    # =====================================
    # STEP 2: VALIDATE
    # =====================================
    valid_actions = validate_actions(
        actions
    )

    # =====================================
    # STEP 3: EXECUTION
    # =====================================
    execution_results = []

    if AUTO_EXECUTE:

        logger.info(
            "Executing actions..."
        )

        execution_results = (

            execute_action_plan(
                valid_actions
            )

        )

    else:

        logger.info(
            "AUTO_EXECUTE disabled"
        )

    # =====================================
    # STEP 4: REFRESH STATE
    # =====================================
    refresh_system_state()

    # =====================================
    # STEP 5: EMAIL SUMMARY
    # =====================================
    if SEND_SUMMARY_EMAIL:

        send_cycle_summary(

            valid_actions,

            execution_results

        )

    logger.info(
        "Trading cycle complete"
    )

    return {

        "actions":
            valid_actions,

        "execution_results":
            execution_results

    }


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    results = run_trading_cycle()

    print(
        "\n===== TRADING CYCLE COMPLETE =====\n"
    )

    print(
        f"Actions: "
        f"{len(results['actions'])}"
    )

    print(
        f"Executions: "
        f"{len(results['execution_results'])}"
    )