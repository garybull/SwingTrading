# production/daily_rebalance.py

from datetime import datetime, timedelta

import json
import sqlite3

import pandas as pd
import yfinance as yf

from app.strategy import score_asset

from app.config import (

    DB_NAME,

    TOP_N,

    CASH_RESERVE,

    SLIPPAGE,

    START_CAPITAL,

    UNIVERSE,

    REBALANCE_DAYS,

    ENABLE_MARKET_FILTER

)

from app.logger import logger


# =====================================
# SAFE SCALAR
# =====================================
def safe_scalar(x):

    if isinstance(x, pd.Series):
        return float(x.iloc[-1])

    return float(x)


# =====================================
# LOAD MARKET DATA
# =====================================
def load_data():

    logger.info(
        "⬇️ Loading market data..."
    )

    data = {}

    for symbol in UNIVERSE:

        try:

            df = yf.download(

                symbol,

                period="2y",

                auto_adjust=True,

                progress=False

            )

            if df is None or len(df) < 200:

                logger.warning(
                    f"{symbol} insufficient data"
                )

                continue

            df.sort_index(inplace=True)

            data[symbol] = df

            logger.info(
                f"Loaded {symbol}"
            )

        except Exception as e:

            logger.error(
                f"Failed loading {symbol}: {e}"
            )

    return data


# =====================================
# MARKET FILTER
# =====================================
def market_is_bullish(spy_df):

    close = safe_scalar(
        spy_df["Close"].iloc[-1]
    )

    ma200 = safe_scalar(

        spy_df["Close"]
        .rolling(200)
        .mean()
        .iloc[-1]

    )

    bullish = close > ma200

    logger.info(

        f"SPY Close: {close:.2f} | "
        f"200 MA: {ma200:.2f} | "
        f"Bullish: {bullish}"

    )

    return bullish


# =====================================
# DB CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# GET CURRENT EQUITY
# =====================================
def get_current_equity(conn):

    cur = conn.cursor()

    cur.execute("""

        SELECT current_equity
        FROM system_state
        WHERE id = 1

    """)

    row = cur.fetchone()

    if row is None:
        return START_CAPITAL

    equity = row[0]

    if equity is None or equity <= 0:
        return START_CAPITAL

    return float(equity)


# =====================================
# CLEAR OLD POSITIONS
# =====================================
def clear_positions(conn):

    cur = conn.cursor()

    cur.execute("""

        DELETE FROM positions

    """)

    conn.commit()


# =====================================
# CLEAR OLD RANKINGS
# =====================================
def clear_rankings(conn):

    cur = conn.cursor()

    cur.execute("""

        DELETE FROM rankings

    """)

    conn.commit()


# =====================================
# SAVE RANKINGS
# =====================================
def save_rankings(

    conn,

    rankings

):

    cur = conn.cursor()

    today = str(
        datetime.now().date()
    )

    for idx, asset in enumerate(rankings):

        cur.execute("""

            INSERT INTO rankings (

                date,
                rank,
                symbol,
                score,
                mom_1m,
                mom_3m,
                mom_6m,
                volatility

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            today,

            idx + 1,

            asset["symbol"],

            asset["score"],

            asset["mom_1m"],

            asset["mom_3m"],

            asset["mom_6m"],

            asset["volatility"]

        ))

    conn.commit()

    logger.info(
        "✅ Rankings saved"
    )


# =====================================
# UPDATE POSITIONS
# =====================================
def update_positions(

    conn,

    leaders,

    capital

):

    cur = conn.cursor()

    clear_positions(conn)

    remaining_cash = capital

    inverse_vols = []

    for asset in leaders:

        inverse_vols.append(
            1 / asset["volatility"]
        )

    total_inverse_vol = sum(
        inverse_vols
    )

    today = str(
        datetime.now().date()
    )

    for idx, asset in enumerate(leaders):

        symbol = asset["symbol"]

        close = asset["close"]

        weight = (

            inverse_vols[idx]
            / total_inverse_vol

        )

        allocation_pct = (
            weight * CASH_RESERVE
        )

        allocation_value = (
            capital * allocation_pct
        )

        shares = int(
            allocation_value / close
        )

        if shares <= 0:
            continue

        cost = (

            shares
            * close
            * (1 + SLIPPAGE)

        )

        remaining_cash -= cost

        market_value = (
            shares * close
        )

        cur.execute("""

            INSERT INTO positions (

                symbol,
                shares,
                entry_price,
                current_price,
                market_value,
                allocation_pct,
                momentum_score,
                volatility,
                rebalance_date

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            symbol,

            shares,

            close,

            close,

            market_value,

            allocation_pct,

            asset["score"],

            asset["volatility"],

            today

        ))

        cur.execute("""

            INSERT INTO rebalance_log (

                date,
                symbol,
                action,
                shares,
                price,
                allocation_pct,
                reason

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

        """, (

            today,

            symbol,

            "BUY",

            shares,

            close,

            allocation_pct,

            "Top momentum ranking"

        ))

        logger.info(

            f"BUY {symbol} | "
            f"Shares: {shares} | "
            f"Allocation: {allocation_pct:.2%}"

        )

    conn.commit()

    return remaining_cash


# =====================================
# SAVE PORTFOLIO HISTORY
# =====================================
def save_portfolio_history(

    conn,

    equity,

    cash,

    leaders

):

    cur = conn.cursor()

    today = str(
        datetime.now().date()
    )

    positions_json = json.dumps(

        [x["symbol"] for x in leaders]

    )

    cur.execute("""

        INSERT OR REPLACE INTO portfolio_history (

            date,
            equity,
            cash,
            drawdown,
            positions_json

        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        today,

        equity,

        cash,

        0,

        positions_json

    ))

    conn.commit()

    logger.info(
        "✅ Portfolio history saved"
    )


# =====================================
# UPDATE SYSTEM STATE
# =====================================
def update_system_state(

    conn,

    equity,

    cash,

    leaders

):

    cur = conn.cursor()

    today = datetime.now().date()

    next_rebalance = (
        today
        + timedelta(days=REBALANCE_DAYS)
    )

    current_leader = ""

    if len(leaders) > 0:

        current_leader = (
            leaders[0]["symbol"]
        )

    cur.execute("""

        UPDATE system_state

        SET

            current_equity = ?,
            current_cash = ?,
            market_regime = ?,
            current_leader = ?,
            next_rebalance_date = ?,
            last_rebalance_date = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE id = 1

    """, (

        equity,

        cash,

        "RISK_ON",

        current_leader,

        str(next_rebalance),

        str(today)

    ))

    conn.commit()

    logger.info(
        "✅ System state updated"
    )


# =====================================
# MAIN
# =====================================
def main():

    logger.info(
        "🚀 DAILY REBALANCE STARTED"
    )

    conn = get_connection()

    capital = get_current_equity(
        conn
    )

    logger.info(
        f"Current equity: ${capital:,.2f}"
    )

    data = load_data()

    if "SPY" not in data:

        logger.error(
            "SPY data missing"
        )

        return

    spy_df = data["SPY"]

    # =====================================
    # MARKET FILTER
    # =====================================
    if ENABLE_MARKET_FILTER:

        if not market_is_bullish(
            spy_df
        ):

            logger.warning(
                "❌ Market filter OFF"
            )

            clear_positions(conn)

            conn.close()

            return

    # =====================================
    # SCORE ASSETS
    # =====================================
    rankings = []

    for symbol in UNIVERSE:

        if symbol == "SPY":
            continue

        if symbol not in data:
            continue

        result = score_asset(

            data[symbol],

            symbol

        )

        if result:

            rankings.append(
                result
            )

    rankings.sort(

        key=lambda x: x["score"],

        reverse=True

    )

    leaders = rankings[:TOP_N]

    logger.info(
        "🏆 LEADERS"
    )

    for idx, asset in enumerate(leaders):

        logger.info(

            f"{idx+1}. "
            f"{asset['symbol']} | "
            f"Score: {asset['score']:.2f}"

        )

    # =====================================
    # SAVE RECOMMENDED PORTFOLIO
    # =====================================
    def save_recommended_portfolio(

        conn,

        leaders

    ):

        cur = conn.cursor()

        # =====================================
        # CLEAR OLD RECOMMENDATIONS
        # =====================================
        cur.execute("""

            DELETE FROM recommended_portfolio

        """)

        inverse_vols = []

        for asset in leaders:

            inverse_vols.append(
                1 / asset["volatility"]
            )

        total_inverse_vol = sum(
            inverse_vols
        )

        today = str(
            datetime.now().date()
        )

        for idx, asset in enumerate(leaders):

            symbol = asset["symbol"]

            weight = (

                inverse_vols[idx]
                / total_inverse_vol

            )

            target_allocation = (
                weight * CASH_RESERVE
            )

            cur.execute("""

                INSERT INTO recommended_portfolio (

                    date,
                    symbol,
                    target_allocation,
                    score,
                    action

                )

                VALUES (?, ?, ?, ?, ?)

            """, (

                today,

                symbol,

                target_allocation,

                asset["score"],

                "BUY"

            ))

        conn.commit()

        logger.info(
            "✅ Recommended portfolio saved"
        )
    # =====================================
    # SAVE RANKINGS
    # =====================================
    clear_rankings(conn)

    save_rankings(
        conn,
        rankings
    )

    # =====================================
    # SAVE RECOMMENDED PORTFOLIO
    # =====================================
    save_recommended_portfolio(
        conn,
        leaders
    )


    
    # =====================================
    # UPDATE PORTFOLIO
    # =====================================
    cash = update_positions(

        conn,

        leaders,

        capital

    )

    # =====================================
    # SAVE HISTORY
    # =====================================
    save_portfolio_history(

        conn,

        capital,

        cash,

        leaders

    )

    # =====================================
    # UPDATE SYSTEM STATE
    # =====================================
    update_system_state(

        conn,

        capital,

        cash,

        leaders

    )

    conn.close()

    logger.info(
        "✅ DAILY REBALANCE COMPLETE"
    )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    main()