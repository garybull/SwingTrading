# app/position_monitor.py

import time
import pandas as pd
from datetime import datetime

from app.logger import logger

from app.emailer import (
    send_email
)

from app.db_service import (
    query_df,
    execute
)

from app.market_data_service import (
    get_live_price,
    get_historical_data
)


# =====================================
# INITIALIZE ALERT TABLE
# =====================================
def initialize_alert_table():

    logger.info(
        "Initializing alerts table..."
    )

    execute("""

        CREATE TABLE IF NOT EXISTS alerts_sent (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,

            alert_type TEXT,

            alert_price REAL,

            alert_date TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

    """)

    logger.info(
        "Alerts table ready"
    )


# =====================================
# GET POSITIONS
# =====================================
def get_positions():

    logger.info(
        "Loading active positions..."
    )

    positions = query_df("""

        SELECT

            symbol,
            shares,
            entry_price

        FROM positions

        WHERE shares > 0

    """)

    logger.info(

        f"Loaded "
        f"{len(positions)} positions"

    )

    return positions


# =====================================
# CALCULATE ATR LEVELS
# =====================================
def calculate_levels(

    symbol,
    entry_price

):

    try:

        df = get_historical_data(
            symbol
        )

        if df is None:

            return None

        if len(df) < 20:

            return None

        # =====================================
        # TRUE RANGE
        # =====================================
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

        # =====================================
        # ATR
        # =====================================
        atr = (

            true_range

            .rolling(14)

            .mean()

            .iloc[-1]

        )

        atr = float(atr)

        # =====================================
        # STOP / TARGET
        # =====================================
        stop_price = round(

            entry_price
            - (2 * atr),

            2

        )

        target_price = round(

            entry_price
            + (4 * atr),

            2

        )

        return {

            "stop":
                stop_price,

            "target":
                target_price

        }

    except Exception as e:

        logger.error(

            f"Level calculation failed "
            f"for {symbol}: {e}"

        )

        return None


# =====================================
# CHECK DUPLICATE ALERT
# =====================================
def alert_already_sent(

    symbol,
    alert_type

):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    df = query_df("""

        SELECT *

        FROM alerts_sent

        WHERE symbol = ?
        AND alert_type = ?
        AND alert_date = ?

    """, (

        symbol,
        alert_type,
        today

    ))

    return not df.empty


# =====================================
# RECORD ALERT
# =====================================
def record_alert(

    symbol,
    alert_type,
    price

):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    execute("""

        INSERT INTO alerts_sent (

            symbol,
            alert_type,
            alert_price,
            alert_date

        )

        VALUES (?, ?, ?, ?)

    """, (

        symbol,
        alert_type,
        price,
        today

    ))

    logger.info(

        f"Recorded alert for "
        f"{symbol}"

    )


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
${round(current_price, 2)}

TRIGGER LEVEL:
${round(trigger_price, 2)}

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
# MONITOR POSITIONS
# =====================================
def monitor_positions():

    logger.info(
        "Starting position monitor..."
    )

    positions = get_positions()

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if positions.empty:

        logger.info(
            "No positions found"
        )

        return

    # =====================================
    # POSITION LOOP
    # =====================================
    for _, row in positions.iterrows():

        symbol = row["symbol"]

        logger.info(
            f"Checking {symbol}"
        )

        current_price = (
            get_live_price(symbol)
        )

        if current_price <= 0:

            logger.warning(

                f"No live price for "
                f"{symbol}"

            )

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

        # =====================================
        # STOP ALERT
        # =====================================
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

        # =====================================
        # TARGET ALERT
        # =====================================
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

                f"Monitor loop failed: "
                f"{e}"

            )

        logger.info(
            "Sleeping 5 minutes..."
        )

        time.sleep(300)