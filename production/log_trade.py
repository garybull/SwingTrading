# production/log_trade.py

from datetime import datetime

from app.db_service import (
    execute_query
)

from app.logger import logger

from app.reconciliation import (
    rebuild_positions_from_trades
)

from app.portfolio_state import (
    refresh_system_state
)


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

    today = str(
        datetime.now().date()
    )

    symbol = symbol.upper()
    side = side.upper()

    total_value = (
        shares * fill_price
    )

    # =====================================
    # SAVE TRADE
    # =====================================
    execute_query("""

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

        symbol,

        side,

        shares,

        fill_price,

        total_value,

        notes

    ))

    logger.info(

        f"TRADE LOGGED | "
        f"{side} "
        f"{shares} "
        f"{symbol} @ "
        f"${fill_price:.2f}"

    )

    # =====================================
    # REBUILD POSITIONS
    # =====================================
    logger.info(
        "Rebuilding positions..."
    )

    rebuild_positions_from_trades()

    # =====================================
    # REFRESH SYSTEM STATE
    # =====================================
    logger.info(
        "Refreshing system state..."
    )

    refresh_system_state()

    print("\n✅ TRADE LOGGED")

    print(

        f"{side} "
        f"{shares} "
        f"{symbol} @ "
        f"${fill_price:.2f}"

    )

    print(
        "\n✅ POSITIONS UPDATED"
    )

    print(
        "✅ SYSTEM STATE REFRESHED"
    )


# =====================================
# CLI
# =====================================
if __name__ == "__main__":

    print(
        "\n🚀 MANUAL TRADE LOGGER\n"
    )

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