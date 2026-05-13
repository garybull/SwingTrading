# production/log_trade.py

from datetime import datetime
import sqlite3

from app.config import DB_NAME
from app.logger import logger


# =====================================
# DB CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# LOG TRADE
# =====================================
def log_trade(

    symbol,
    side,
    shares,
    fill_price,
    notes=""

):

    conn = get_connection()

    cur = conn.cursor()

    today = str(
        datetime.now().date()
    )

    total_value = (
        shares * fill_price
    )

    # =====================================
    # SAVE TRADE
    # =====================================
    cur.execute("""

        INSERT INTO executed_trades (

            date,
            symbol,
            side,
            shares,
            fill_price,
            total_value,
            notes

        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

    """, (

        today,

        symbol.upper(),

        side.upper(),

        shares,

        fill_price,

        total_value,

        notes

    ))

    conn.commit()

    conn.close()

    logger.info(

        f"TRADE LOGGED | "
        f"{side.upper()} "
        f"{shares} "
        f"{symbol.upper()} @ "
        f"${fill_price:.2f}"

    )

    print("\n✅ TRADE LOGGED")

    print(

        f"{side.upper()} "
        f"{shares} "
        f"{symbol.upper()} @ "
        f"${fill_price:.2f}"

    )


# =====================================
# CLI
# =====================================
if __name__ == "__main__":

    print("\n🚀 MANUAL TRADE LOGGER\n")

    symbol = input(
        "Symbol: "
    ).strip()

    side = input(
        "BUY or SELL: "
    ).strip().upper()

    shares = int(

        input(
            "Shares: "
        )

    )

    fill_price = float(

        input(
            "Fill Price: "
        )

    )

    notes = input(
        "Notes (optional): "
    ).strip()

    log_trade(

        symbol=symbol,

        side=side,

        shares=shares,

        fill_price=fill_price,

        notes=notes

    )