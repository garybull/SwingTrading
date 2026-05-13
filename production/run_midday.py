# production/run_midday.py

from app.emailer_midday import (
    send_midday_email
)

from app.logger import logger


# =====================================
# RUN
# =====================================
def run():

    logger.info(
        "☀️ MIDDAY RUN STARTED"
    )

    send_midday_email()

    logger.info(
        "✅ MIDDAY RUN COMPLETE"
    )


if __name__ == "__main__":

    run()