# app/emailer_eod.py

import smtplib

from email.mime.multipart import (
    MIMEMultipart
)

from email.mime.text import MIMEText

from app.portfolio import (
    get_dashboard_data
)

from app.live_portfolio import (
    get_live_portfolio
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
# BUILD EOD BODY
# =====================================
def build_eod_body():

    data = get_dashboard_data()

    system_state = data[
        "system_state"
    ]

    performance = data[
        "performance"
    ]

    executed_trades = data[
        "executed_trades"
    ]

    # =====================================
    # LIVE PORTFOLIO
    # =====================================
    live_portfolio = (
        get_live_portfolio()
    )

    positions = live_portfolio[
        "positions"
    ]

    total_equity = live_portfolio[
        "total_equity"
    ]

    current_cash = live_portfolio[
        "cash"
    ]

    # =====================================
    # POSITIONS
    # =====================================
    positions_text = ""

    for _, row in positions.iterrows():

        positions_text += (

            f"- {row['symbol']} | "

            f"{row['allocation_pct'] * 100:.1f}% | "

            f"${row['market_value']:,.2f}\n"

        )

    # =====================================
    # RECENT TRADES
    # =====================================
    trades_text = ""

    for _, row in executed_trades.head(10).iterrows():

        trades_text += (

            f"- {row['date']} | "

            f"{row['side']} "

            f"{row['symbol']} | "

            f"{row['shares']} shares @ "

            f"${row['fill_price']:.2f}\n"

        )

    if trades_text == "":

        trades_text = (
            "No recent trades."
        )

    body = f"""

🌙 End Of Day Momentum Rotation Report

========================================
PERFORMANCE
========================================

Portfolio Value:
${total_equity:,.2f}

Current Cash:
${current_cash:,.2f}

CAGR:
{performance['cagr']}%

Max Drawdown:
{performance['max_drawdown']}%

Market Regime:
{system_state['market_regime']}


========================================
CURRENT POSITIONS
========================================

{positions_text}


========================================
RECENT TRADES
========================================

{trades_text}


Generated automatically by the
Momentum Rotation System.

"""

    return body


# =====================================
# SEND EOD EMAIL
# =====================================
def send_eod_email():

    if not ENABLE_EMAILS:

        logger.warning(
            "⚠️ Emails disabled"
        )

        return

    try:

        body = build_eod_body()

        msg = MIMEMultipart()

        msg["Subject"] = (
            "🌙 End Of Day Momentum Report"
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
            "✅ EOD email sent"
        )

    except Exception as e:

        logger.error(

            f"❌ EOD email failed: {e}"

        )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    send_eod_email()