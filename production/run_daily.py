# production/run_daily.py

import traceback

from production.daily_rebalance import (
    main as rebalance_main
)

from app.emailer import (
    send_daily_email
)

from app.logger import logger


# =====================================
# RUN DAILY PROCESS
# =====================================
def run():

    logger.info(
        "🚀 DAILY SYSTEM RUN STARTED"
    )

    try:

        # =====================================
        # REBALANCE ENGINE
        # =====================================
        logger.info(
            "Running rebalance engine..."
        )

        rebalance_main()

        logger.info(
            "✅ Rebalance complete"
        )

        # =====================================
        # EMAIL
        # =====================================
        logger.info(
            "Sending email update..."
        )

        send_daily_email()

        logger.info(
            "✅ Email complete"
        )

        logger.info(
            "🎉 DAILY SYSTEM RUN COMPLETE"
        )

    except Exception as e:

        logger.error(
            "❌ DAILY RUN FAILED"
        )

        logger.error(str(e))

        logger.error(

            traceback.format_exc()

        )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    run()