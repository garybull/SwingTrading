# app/emailer_morning.py

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

from app.recommendation_engine import (
    build_action_plan
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
# BUILD EMAIL BODY
# =====================================
def build_email_body():

    data = get_dashboard_data()

    system_state = data[
        "system_state"
    ]

    performance = data[
        "performance"
    ]

    recommended = data[
        "recommended_portfolio"
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
    # ACTION PLAN
    # =====================================
    actions = build_action_plan(
        recommended
    )

    # =====================================
    # ACTION SECTION
    # =====================================
    action_lines = []

    for a in actions:

        if a["action"] != "HOLD":

            action_lines.append(

                f"- {a['action']} "
                f"{a['symbol']} | "
                f"Target "
                f"{a['target_allocation'] * 100:.1f}%"

            )

    if len(action_lines) == 0:

        action_text = (
            "No action required."
        )

    else:

        action_text = "\n".join(
            action_lines
        )

    # =====================================
    # RECOMMENDED PORTFOLIO
    # =====================================
    recommended_text = ""

    for _, row in recommended.iterrows():

        recommended_text += (

            f"- {row['symbol']} | "

            f"{row['target_allocation'] * 100:.1f}% | "

            f"Score: {row['score']:.2f}\n"

        )

    # =====================================
    # CURRENT POSITIONS
    # =====================================
    positions_text = ""

    for _, row in positions.iterrows():

        positions_text += (

            f"- {row['symbol']} | "

            f"{row['allocation_pct'] * 100:.1f}% | "

            f"${row['market_value']:,.2f}\n"

        )

    body = f"""

🌅 Morning Momentum Rotation Update

========================================
MARKET STATUS
========================================

Market Regime:
{system_state['market_regime']}

Current Leader:
{system_state['current_leader']}

Portfolio Value:
${total_equity:,.2f}

Current Cash:
${current_cash:,.2f}

CAGR:
{performance['cagr']}%

Max Drawdown:
{performance['max_drawdown']}%

Next Rebalance:
{system_state['next_rebalance_date']}


========================================
ACTION REQUIRED
========================================

{action_text}


========================================
RECOMMENDED PORTFOLIO
========================================

{recommended_text}


========================================
CURRENT POSITIONS
========================================

{positions_text}


Generated automatically by the
Momentum Rotation System.

"""

    return body


# =====================================
# SEND MORNING EMAIL
# =====================================
def send_morning_email():

    if not ENABLE_EMAILS:

        logger.warning(
            "⚠️ Emails disabled"
        )

        return

    try:

        body = build_email_body()

        msg = MIMEMultipart()

        msg["Subject"] = (
            "🌅 Morning Momentum Update"
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
            "✅ Morning email sent"
        )

    except Exception as e:

        logger.error(

            f"❌ Morning email failed: {e}"

        )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    send_morning_email()