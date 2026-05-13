# app/emailer_midday.py

from app.emailer_morning import (
    send_morning_email
)

from app.logger import logger


# =====================================
# SEND MIDDAY EMAIL
# =====================================
def send_midday_email():

    logger.info(
        "☀️ Sending midday update"
    )

    send_morning_email()

    logger.info(
        "✅ Midday email sent"
    )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    send_midday_email()