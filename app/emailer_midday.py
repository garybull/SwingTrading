# app/emailer_midday.py

import smtplib

from email.mime.multipart import (
    MIMEMultipart
)

from email.mime.text import (
    MIMEText
)

from app.emailer_morning import (
    build_email_body
)

from app.config import (

    SMTP_SERVER,
    SMTP_PORT,

    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    TO_EMAIL,

    ENABLE_EMAILS

)

from app.logger import logger


# =====================================
# SEND MIDDAY EMAIL
# =====================================
def send_midday_email():

    logger.info(
        "☀️ Sending midday update"
    )

    if not ENABLE_EMAILS:

        logger.warning(
            "⚠️ Emails disabled"
        )

        return

    try:

        body = build_email_body()

        msg = MIMEMultipart()

        msg["Subject"] = (
            "☀️ Midday Momentum Update"
        )

        msg["From"] = EMAIL_ADDRESS

        msg["To"] = TO_EMAIL

        msg.attach(

            MIMEText(
                body,
                "plain"
            )

        )

        logger.info(
            "Connecting to SMTP server..."
        )

        server = smtplib.SMTP(

            SMTP_SERVER,
            SMTP_PORT

        )

        server.starttls()

        server.login(

            EMAIL_ADDRESS,
            EMAIL_PASSWORD

        )

        server.sendmail(

            EMAIL_ADDRESS,

            TO_EMAIL,

            msg.as_string()

        )

        server.quit()

        logger.info(
            "✅ Midday email sent"
        )

    except Exception as e:

        logger.error(

            f"❌ Midday email failed: {e}"

        )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    send_midday_email()