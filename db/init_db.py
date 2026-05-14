# init_db.py

import sqlite3

from app.config import DB_NAME

SCHEMA_VERSION = "1.3"

# =====================================
# INIT DATABASE
# =====================================
def init_db():

    conn = sqlite3.connect(DB_NAME)

    cur = conn.cursor()

    # =====================================
    # POSITIONS
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS positions (

        symbol TEXT PRIMARY KEY,

        shares INTEGER,

        entry_price REAL,

        current_price REAL,

        market_value REAL,

        allocation_pct REAL,

        momentum_score REAL,

        volatility REAL,

        rebalance_date TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =====================================
    # PORTFOLIO HISTORY
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS portfolio_history (

        date TEXT PRIMARY KEY,

        equity REAL,

        cash REAL,

        drawdown REAL,

        positions_json TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =====================================
    # REBALANCE LOG
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS rebalance_log (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        date TEXT,

        symbol TEXT,

        action TEXT,

        shares INTEGER,

        price REAL,

        allocation_pct REAL,

        reason TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =====================================
    # DAILY RANKINGS
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS rankings (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        date TEXT,

        rank INTEGER,

        symbol TEXT,

        score REAL,

        mom_1m REAL,

        mom_3m REAL,

        mom_6m REAL,

        volatility REAL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =====================================
    # RECOMMENDED PORTFOLIO
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS recommended_portfolio (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        date TEXT,

        symbol TEXT,

        target_allocation REAL,

        score REAL,

        action TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =====================================
    # SYSTEM STATE
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS system_state (

        id INTEGER PRIMARY KEY CHECK (id = 1),

        current_equity REAL,

        current_cash REAL,

        market_regime TEXT,

        current_leader TEXT,

        next_rebalance_date TEXT,

        last_rebalance_date TEXT,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =====================================
    # EXECUTED TRADES
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS executed_trades (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        date TEXT,

        symbol TEXT,

        side TEXT,

        shares INTEGER,

        fill_price REAL,

        total_value REAL,

        notes TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)
    # =====================================
    # POSITION LOTS
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS position_lots (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        symbol TEXT,

        shares INTEGER,

        remaining_shares INTEGER,

        entry_price REAL,

        entry_date TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =====================================
    # ALERTS SENT
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS alerts_sent (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        symbol TEXT,

        alert_type TEXT,

        alert_price REAL,

        alert_date TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)
    # =====================================
    # INSERT DEFAULT SYSTEM STATE
    # =====================================
    cur.execute("""

    INSERT OR IGNORE INTO system_state (

        id,
        current_equity,
        current_cash,
        market_regime,
        current_leader,
        next_rebalance_date,
        last_rebalance_date

    )

    VALUES (

        1,
        0,
        0,
        'UNKNOWN',
        '',
        '',
        ''

    )

    """)

    conn.commit()

    conn.close()

    print(
        "✅ Database initialized successfully"
    )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    init_db()