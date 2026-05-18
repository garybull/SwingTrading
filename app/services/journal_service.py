# app/services/journal_service.py

from datetime import datetime

from app.db_service import (
    execute,
    query_df
)

from app.logger import logger

from app.regime_engine import (
    determine_market_regime
)

from app.risk_engine import (
    get_risk_report
)

from app.health_engine import (
    get_health_report
)


# =====================================
# CREATE JOURNAL ENTRY
# =====================================
def create_journal_entry(

    symbol,
    shares,
    entry_price,
    ranking_row=None

):

    logger.info(

        f"Creating trade journal entry "
        f"for {symbol}"

    )

    # =====================================
    # MARKET CONTEXT
    # =====================================
    regime = (
        determine_market_regime()
    )

    risk_report = (
        get_risk_report()
    )

    health_report = (

        get_health_report(

            regime=regime,

            risk_report=risk_report

        )

    )

    # =====================================
    # RANKING DATA
    # =====================================
    entry_score = None

    entry_rank = None

    volatility = None

    if ranking_row is not None:

        entry_score = float(

            ranking_row.get(
                "score",
                0
            )

        )

        entry_rank = int(

            ranking_row.get(
                "rank",
                0
            )

        )

        volatility = float(

            ranking_row.get(
                "volatility",
                0
            )

        )

    # =====================================
    # INSERT JOURNAL ENTRY
    # =====================================
    execute("""

        INSERT INTO trade_journal (

            symbol,

            entry_date,

            shares,

            remaining_shares,

            entry_price,

            regime_entry,

            entry_score,

            entry_rank,

            volatility_entry,

            effective_exposure_entry,

            cash_pct_entry,

            health_score_entry

        )

        VALUES (

            ?, DATE('now'), ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?

        )

    """, (

        symbol,

        shares,

        shares,

        entry_price,

        regime["regime"],

        entry_score,

        entry_rank,

        volatility,

        risk_report.get(
            "effective_exposure",
            0
        ),

        risk_report.get(
            "cash_pct",
            0
        ),

        health_report.get(
            "score",
            0
        )

    ))

    logger.info(
        "Trade journal entry created"
    )


# =====================================
# CLOSE JOURNAL ENTRY
# =====================================
def close_journal_entry(

    symbol,
    shares_sold,
    exit_price

):

    logger.info(

        f"Closing trade journal entry "
        f"for {symbol}"

    )

    # =====================================
    # FIND OPEN TRADE
    # =====================================
    open_trade = query_df("""

        SELECT *

        FROM trade_journal

        WHERE symbol = ?
        AND remaining_shares > 0

        ORDER BY id DESC

        LIMIT 1

    """, (

        symbol,

    ))

    if open_trade.empty:

        logger.warning(

            f"No open journal entry "
            f"found for {symbol}"

        )

        return

    trade = open_trade.iloc[0]

    # =====================================
    # CURRENT REGIME
    # =====================================
    regime = (
        determine_market_regime()
    )

    # =====================================
    # CALCULATE RESULTS
    # =====================================
    entry_price = float(
        trade["entry_price"]
    )

    remaining_shares = int(
        trade["remaining_shares"]
    )

    realized_pnl = (

        exit_price
        - entry_price

    ) * shares_sold

    new_remaining = (
        remaining_shares
        - shares_sold
    )

    entry_date = datetime.strptime(

        trade["entry_date"],

        "%Y-%m-%d"

    )

    holding_days = (

        datetime.now()
        - entry_date

    ).days

    # =====================================
    # CURRENT RANKING
    # =====================================
    rankings = query_df("""

        SELECT
            rank,
            score

        FROM rankings

        WHERE symbol = ?

        LIMIT 1

    """, (

        symbol,

    ))

    exit_rank = None

    exit_score = None

    if not rankings.empty:

        exit_rank = int(
            rankings.iloc[0]["rank"]
        )

        exit_score = float(
            rankings.iloc[0]["score"]
        )

    # =====================================
    # UPDATE JOURNAL
    # =====================================
    execute("""

        UPDATE trade_journal

        SET

            remaining_shares = ?,

            exit_date = CASE

                WHEN ? <= 0

                THEN DATE('now')

                ELSE NULL

            END,

            exit_price = ?,

            realized_pnl = COALESCE(
                realized_pnl,
                0
            ) + ?,

            holding_days = ?,

            regime_exit = ?,

            exit_score = ?,

            exit_rank = ?

        WHERE id = ?

    """, (

        new_remaining,

        new_remaining,

        exit_price,

        realized_pnl,

        holding_days,

        regime["regime"],

        exit_score,

        exit_rank,

        int(trade["id"])

    ))

    logger.info(
        "Trade journal entry closed"
    )