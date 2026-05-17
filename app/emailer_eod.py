# app/emailer_eod.py

import smtplib

from email.mime.multipart import (
    MIMEMultipart
)

from email.mime.text import (
    MIMEText
)

from app.health_engine import (
    get_health_report
)

from app.regime_engine import (
    determine_market_regime
)

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
    # MARKET REGIME
    # =====================================
    regime_data = (
        determine_market_regime()
    )

    # =====================================
    # HEALTH REPORT
    # =====================================
    health_report = (
        get_health_report()
    )

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

    if positions is not None and len(positions) > 0:

        for _, row in positions.iterrows():

            positions_text += (

                f"- {row['symbol']} | "

                f"{row['allocation_pct'] * 100:.1f}% | "

                f"${row['market_value']:,.2f}\n"

            )

    else:

        positions_text = (
            "No open positions."
        )

    # =====================================
    # RECENT TRADES
    # =====================================
    trades_text = ""

    if (

        executed_trades is not None

        and

        len(executed_trades) > 0

    ):

        for _, row in executed_trades.head(10).iterrows():

            trades_text += (

                f"- {row['date']} | "

                f"{row['side']} "

                f"{row['symbol']} | "

                f"{row['shares']} shares @ "

                f"${row['fill_price']:.2f}\n"

            )

    else:

        trades_text = (
            "No recent trades."
        )

    # =====================================
    # REGIME TEXT
    # =====================================
    regime_text = f"""

========================================
MARKET REGIME
========================================

Regime:
{regime_data['regime']}

SPY:
{regime_data['spy_close']}

SPY 200DMA:
{regime_data['spy_200dma']}

SPY Above 200DMA:
{regime_data['spy_above_200dma']}

QQQ:
{regime_data['qqq_close']}

QQQ 200DMA:
{regime_data['qqq_200dma']}

VIX:
{regime_data['vix']}

"""

    # =====================================
    # HEALTH REPORT
    # =====================================
    health_text = f"""

========================================
PORTFOLIO HEALTH
========================================

Status:
{health_report['status']}

Health Score:
{health_report['score']}/100

Effective Exposure:
{health_report['effective_exposure']:.1f}%

Largest Position:
{health_report['largest_position']:.1f}%

Cash:
{health_report['cash_pct']:.1f}%

"""

    # =====================================
    # WARNINGS
    # =====================================
    if health_report["warning_count"] > 0:

        health_text += "\nWarnings:\n\n"

        for w in health_report["warnings"]:

            health_text += (

                f"- {w['level']}: "
                f"{w['message']}\n"

            )

    else:

        health_text += (

            "\n✅ No active "
            "portfolio warnings.\n"

        )

    # =====================================
    # CAGR FORMAT
    # =====================================
    if performance["cagr"] is not None:

        cagr_text = (
            f"{performance['cagr']:.2f}%"
        )

    else:

        cagr_text = (
            "N/A - Not enough history"
        )

    # =====================================
    # EMAIL BODY
    # =====================================
    body = f"""

🌙 End Of Day Momentum Rotation Report

{regime_text}

{health_text}

========================================
PERFORMANCE
========================================

Portfolio Value:
${total_equity:,.2f}

Current Cash:
${current_cash:,.2f}

CAGR:
{cagr_text}

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