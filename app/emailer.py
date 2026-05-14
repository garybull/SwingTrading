# app/emailer.py

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.portfolio import (
    get_dashboard_data
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
# BUILD EMAIL HTML
# =====================================
def build_email_html(data):

    system_state = data["system_state"]

    positions = data["positions"]

    rankings = data["rankings"]

    performance = data["performance"]

    drawdown = data["drawdown"]

    latest_rebalance = (
        data["latest_rebalance"]
    )

    portfolio_summary = (
        data["portfolio_summary"]
    )

    html = f"""

    <html>

    <body style="

        font-family: Arial;
        background-color: #111827;
        color: #f3f4f6;
        padding: 20px;

    ">

    <h1>
        🚀 Momentum Rotation Update
    </h1>

    <h2>
        System Status
    </h2>

    <ul>

        <li>
            <b>Market Regime:</b>
            {system_state.get('market_regime')}
        </li>

        <li>
            <b>Current Leader:</b>
            {system_state.get('current_leader')}
        </li>

        <li>
            <b>Current Equity:</b>
            ${system_state.get('current_equity'):,.2f}
        </li>

        <li>
            <b>Current Cash:</b>
            ${system_state.get('current_cash'):,.2f}
        </li>

        <li>
            <b>Current Drawdown:</b>
            {drawdown:.2f}%
        </li>

        <li>
            <b>CAGR:</b>
            {performance.get('cagr')}%
        </li>

        <li>
            <b>Max Drawdown:</b>
            {performance.get('max_drawdown')}%
        </li>

        <li>
            <b>Total Return:</b>
            {performance.get('total_return')}%
        </li>

        <li>
            <b>Positions:</b>
            {portfolio_summary.get('position_count')}
        </li>

        <li>
            <b>Total Market Value:</b>
            ${portfolio_summary.get('total_market_value'):,.2f}
        </li>

        <li>
            <b>Next Rebalance:</b>
            {system_state.get('next_rebalance_date')}
        </li>

        <li>
            <b>Last Rebalance:</b>
            {system_state.get('last_rebalance_date')}
        </li>

    </ul>

    <hr>

    <h2>
        Current Positions
    </h2>

    """

    # =====================================
    # POSITIONS TABLE
    # =====================================
    if len(positions) > 0:

        html += """

        <table
            border="1"
            cellpadding="8"
            cellspacing="0"
            style="
                border-collapse: collapse;
                width: 100%;
                background-color: #1f2937;
            "
        >

            <tr>

                <th>Symbol</th>
                <th>Shares</th>
                <th>Allocation</th>
                <th>Market Value</th>
                <th>Momentum Score</th>
                <th>Volatility</th>

            </tr>

        """

        for _, row in positions.iterrows():

            html += f"""

            <tr>

                <td>{row['symbol']}</td>

                <td>{row['shares']}</td>

                <td>
                    {row['allocation_pct'] * 100:.2f}%
                </td>

                <td>
                    ${row['market_value']:,.2f}
                </td>

                <td>
                    {row['momentum_score']:.2f}
                </td>

                <td>
                    {row['volatility']:.4f}
                </td>

            </tr>

            """

        html += """

        </table>

        """

    else:

        html += """

        <p>
            No current positions.
        </p>

        """

    html += """

    <hr>

    <h2>
        Momentum Rankings
    </h2>

    """

    # =====================================
    # RANKINGS TABLE
    # =====================================
    if len(rankings) > 0:

        html += """

        <table
            border="1"
            cellpadding="8"
            cellspacing="0"
            style="
                border-collapse: collapse;
                width: 100%;
                background-color: #1f2937;
            "
        >

            <tr>

                <th>Rank</th>
                <th>Symbol</th>
                <th>Score</th>
                <th>1M</th>
                <th>3M</th>
                <th>6M</th>
                <th>Volatility</th>

            </tr>

        """

        for _, row in rankings.iterrows():

            html += f"""

            <tr>

                <td>{row['rank']}</td>

                <td>{row['symbol']}</td>

                <td>{row['score']:.2f}</td>

                <td>
                    {row['mom_1m'] * 100:.2f}%
                </td>

                <td>
                    {row['mom_3m'] * 100:.2f}%
                </td>

                <td>
                    {row['mom_6m'] * 100:.2f}%
                </td>

                <td>
                    {row['volatility']:.4f}
                </td>

            </tr>

            """

        html += """

        </table>

        """

    else:

        html += """

        <p>
            No rankings available.
        </p>

        """

    # =====================================
    # LATEST REBALANCE
    # =====================================
    html += """

    <hr>

    <h2>
        Latest Rebalance
    </h2>

    """

    if latest_rebalance:

        html += f"""

        <ul>

            <li>
                <b>Date:</b>
                {latest_rebalance.get('date')}
            </li>

            <li>
                <b>Symbol:</b>
                {latest_rebalance.get('symbol')}
            </li>

            <li>
                <b>Action:</b>
                {latest_rebalance.get('action')}
            </li>

            <li>
                <b>Shares:</b>
                {latest_rebalance.get('shares')}
            </li>

            <li>
                <b>Price:</b>
                ${latest_rebalance.get('price'):,.2f}
            </li>

            <li>
                <b>Allocation:</b>
                {latest_rebalance.get('allocation_pct', 0) * 100:.2f}%
            </li>

            <li>
                <b>Reason:</b>
                {latest_rebalance.get('reason')}
            </li>

        </ul>

        """

    else:

        html += """

        <p>
            No rebalance history yet.
        </p>

        """

    html += """

    <hr>

    <p>
        Generated automatically by the
        Momentum Rotation System
    </p>

    </body>

    </html>

    """

    return html

# =====================================
# GENERIC EMAIL SENDER
# =====================================
def send_email(
    subject,
    body
):

    if not ENABLE_EMAILS:

        logger.warning(
            "⚠️ Emails disabled"
        )

        return

    msg = MIMEMultipart()

    msg["Subject"] = subject

    msg["From"] = EMAIL_ADDRESS

    msg["To"] = TO_EMAIL

    msg.attach(

        MIMEText(
            body,
            "plain"
        )

    )

    try:

        logger.info(
            f"Sending email: {subject}"
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
            "✅ Alert email sent"
        )

    except Exception as e:

        logger.error(
            f"❌ Alert email failed: {e}"
        )
        
# =====================================
# SEND Daily EMAIL
# =====================================
def send_daily_email():

    if not ENABLE_EMAILS:

        logger.warning(
            "⚠️ Emails disabled"
        )

        return

    if not EMAIL_ADDRESS:

        logger.error(
            "❌ EMAIL_ADD missing"
        )

        return

    if not EMAIL_PASSWORD:

        logger.error(
            "❌ EMAIL_PASS missing"
        )

        return

    data = get_dashboard_data()

    html = build_email_html(
        data
    )

    msg = MIMEMultipart(
        "alternative"
    )

    msg["Subject"] = (
        "🚀 Momentum Rotation Update"
    )

    msg["From"] = EMAIL_ADDRESS

    msg["To"] = TO_EMAIL

    msg.attach(

        MIMEText(
            html,
            "html"
        )

    )

    try:

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
            "✅ Email sent successfully"
        )

    except Exception as e:

        logger.error(
            f"❌ Email failed: {e}"
        )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    send_daily_email()