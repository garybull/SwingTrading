# production/run_morning.py

from production.daily_rebalance import (
    main as run_rebalance
)

from app.emailer_morning import (
    send_morning_email
)

from app.logger import logger


# =====================================
# RUN
# =====================================
def run():

    logger.info(
        "🌅 MORNING RUN STARTED"
    )

    run_rebalance()

    send_morning_email()

    logger.info(
        "✅ MORNING RUN COMPLETE"
    )


if __name__ == "__main__":

    run()