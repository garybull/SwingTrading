# production/run_eod.py

from app.emailer_eod import (
    send_eod_email
)

from app.logger import logger


# =====================================
# RUN
# =====================================
def run():

    logger.info(
        "🌙 EOD RUN STARTED"
    )

    send_eod_email()

    logger.info(
        "✅ EOD RUN COMPLETE"
    )


if __name__ == "__main__":

    run()