# app/position_monitor.py

import time
import sqlite3
import pandas as pd
import yfinance as yf

from datetime import datetime

from app.logger import logger
from app.emailer import send_email


DB_PATH = "DB_PATH = "/home/ubuntu/SwingTrading/trading_system.db"


# =====================================
# CREATE ALERT TABLE
# =====================================
def initialize_alert_table():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """

        CREATE TABLE IF NOT EXISTS alerts_sent (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,

            alert_type TEXT,

            alert_price REAL,

            alert_date TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """
    )

    conn.commit()

    conn.close()


# =====================================
# GET POSITIONS
# =====================================
def get_positions():

    conn = sqlite3.connect(DB_PATH)

    query = """

        SELECT
            symbol,
            shares,
            entry_price

        FROM positions

        WHERE shares > 0

    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df


# =====================================
# GET CURRENT PRICE
# =====================================
def get_current_price(symbol):

    try:

        ticker = yf.Ticker(symbol)

        price = (

            ticker.fast_info

            .get("lastPrice")

        )

        if price is None:

            hist = ticker.history(
                period="1d",
                interval="1m"
            )

            if hist.empty:

                return None

            price = hist["Close"].iloc[-1]

        return float(price)

    except Exception as e:

        logger.error(
            f"Price fetch failed for {symbol}: {e}"
        )

        return None


# =====================================
# CALCULATE LEVELS
# =====================================
def calculate_levels(
    symbol,
    entry_price
):

    try:

        df = yf.download(

            symbol,

            period="30d",

            interval="1d",

            auto_adjust=False,

            progress=False

        )

        if df.empty:

            return None

        # ==============================
        # TRUE RANGE
        # ==============================
        high_low = (

            df["High"]
            - df["Low"]

        )

        high_close = abs(

            df["High"]
            - df["Close"].shift()

        )

        low_close = abs(

            df["Low"]
            - df["Close"].shift()

        )

        ranges = pd.concat(

            [

                high_low,
                high_close,
                low_close

            ],

            axis=1

        )

        true_range = ranges.max(
            axis=1
        )

        # ==============================
        # ATR
        # ==============================
        atr = (

            true_range

            .rolling(14)

            .mean()

            .iloc[-1]

        )

        atr = float(atr)

        # ==============================
        # FIXED LEVELS
        # BASED ON ENTRY
        # ==============================
        stop_price = 999999
        # stop_price = round(

        #     entry_price
        #     - (2 * atr),

        #     2

        # )

        target_price = round(

            entry_price
            + (4 * atr),

            2

        )

        return {

            "stop": stop_price,

            "target": target_price

        }

    except Exception as e:

        logger.error(
            f"Level calculation failed for {symbol}: {e}"
        )

        return None

# =====================================
# CHECK DUPLICATE ALERT
# =====================================
def alert_already_sent(
    symbol,
    alert_type
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cursor.execute(
        """

        SELECT COUNT(*)

        FROM alerts_sent

        WHERE symbol = ?
        AND alert_type = ?
        AND alert_date = ?

        """,

        (
            symbol,
            alert_type,
            today
        )

    )

    count = cursor.fetchone()[0]

    conn.close()

    return count > 0


# =====================================
# RECORD ALERT
# =====================================
def record_alert(
    symbol,
    alert_type,
    price
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cursor.execute(
        """

        INSERT INTO alerts_sent (

            symbol,
            alert_type,
            alert_price,
            alert_date

        )

        VALUES (?, ?, ?, ?)

        """,

        (
            symbol,
            alert_type,
            price,
            today
        )

    )

    conn.commit()

    conn.close()


# =====================================
# SEND ALERT EMAIL
# =====================================
def send_alert_email(
    symbol,
    alert_type,
    current_price,
    trigger_price
):

    subject = (
        f"{alert_type}: {symbol}"
    )

    body = f"""

    ALERT TYPE:
    {alert_type}

    SYMBOL:
    {symbol}

    CURRENT PRICE:
    ${round(current_price,2)}

    TRIGGER LEVEL:
    ${round(trigger_price,2)}

    TIME:
    {datetime.now()}

    """

    send_email(
        subject,
        body
    )

    logger.info(
        f"Alert sent for {symbol}"
    )


# =====================================
# CHECK POSITIONS
# =====================================
def monitor_positions():

    logger.info(
        "Starting position monitor..."
    )

    positions = get_positions()

    if positions.empty:

        logger.info(
            "No positions found"
        )

        return

    for _, row in positions.iterrows():

        symbol = row["symbol"]

        logger.info(
            f"Checking {symbol}"
        )

        current_price = get_current_price(
            symbol
        )

        if current_price is None:

            continue

        entry_price = float(
            row["entry_price"]
        )

        levels = calculate_levels(

            symbol,

            entry_price

        )

        if levels is None:

            continue

        stop_price = levels["stop"]

        target_price = levels["target"]

        # ==============================
        # STOP ALERT
        # ==============================
        if current_price <= stop_price:

            if not alert_already_sent(

                symbol,

                "STOP HIT"

            ):

                send_alert_email(

                    symbol,

                    "STOP HIT",

                    current_price,

                    stop_price

                )

                record_alert(

                    symbol,

                    "STOP HIT",

                    current_price

                )

        # ==============================
        # TARGET ALERT
        # ==============================
        if current_price >= target_price:

            if not alert_already_sent(

                symbol,

                "TARGET HIT"

            ):

                send_alert_email(

                    symbol,

                    "TARGET HIT",

                    current_price,

                    target_price

                )

                record_alert(

                    symbol,

                    "TARGET HIT",

                    current_price

                )

    logger.info(
        "Position monitor complete"
    )


# =====================================
# MAIN LOOP
# =====================================
if __name__ == "__main__":

    logger.info(
        "Initializing position monitor..."
    )

    initialize_alert_table()

    while True:

        try:

            monitor_positions()

        except Exception as e:

            logger.error(
                f"Monitor loop failed: {e}"
            )

        logger.info(
            "Sleeping 5 minutes..."
        )

        time.sleep(300)