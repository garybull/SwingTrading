# init_db.py

import sqlite3

from app.config import DB_NAME
from app.config import (
    DB_NAME,
    START_CAPITAL
)

SCHEMA_VERSION = "1.4"


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

        close REAL,

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

            current_price REAL,

            target_value REAL,

            recommended_shares INTEGER,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )

    """)

    # =====================================
    # TRADE JOURNAL
    # =====================================
    cur.execute("""

        CREATE TABLE IF NOT EXISTS trade_journal (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,

            entry_date TEXT,

            exit_date TEXT,

            shares INTEGER,

            entry_price REAL,

            exit_price REAL,

            realized_pnl REAL,

            holding_days INTEGER,

            regime_entry TEXT,

            regime_exit TEXT,

            entry_score REAL,

            exit_score REAL,

            entry_rank INTEGER,

            exit_rank INTEGER,

            volatility_entry REAL,

            effective_exposure_entry REAL,

            cash_pct_entry REAL,

            health_score_entry REAL,
                
            remaining_shares INTEGER,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )

    """)

    # =====================================
    # UNIVERSE RANKINGS
    # =====================================
    cur.execute("""

        CREATE TABLE IF NOT EXISTS universe_rankings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            snapshot_date TEXT,

            symbol TEXT,

            price REAL,

            score REAL,

            rank_position INTEGER,

            recommended INTEGER,

            score_gap_to_top REAL,

            score_gap_to_buy_cutoff REAL,

            momentum_20d REAL,

            momentum_acceleration REAL,

            volatility REAL,

            regime TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )

    """)

    # =====================================
    # UNIVERSE RANKINGS INDEXES
    # =====================================
    cur.execute("""

        CREATE INDEX IF NOT EXISTS idx_universe_rankings_date

        ON universe_rankings(snapshot_date)

    """)

    cur.execute("""

        CREATE INDEX IF NOT EXISTS idx_universe_rankings_symbol

        ON universe_rankings(symbol)

    """)

    cur.execute("""

        CREATE INDEX IF NOT EXISTS idx_universe_rankings_symbol_date

        ON universe_rankings(symbol, snapshot_date)

    """)

    # =====================================
    # SYSTEM STATE
    # =====================================
    cur.execute("""

    CREATE TABLE IF NOT EXISTS system_state (

        id INTEGER PRIMARY KEY CHECK (id = 1),

        starting_capital REAL,

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
    # INDEXES
    # =====================================
    cur.execute("""

        CREATE INDEX IF NOT EXISTS idx_universe_rankings_date

        ON universe_rankings(snapshot_date)

    """)

    cur.execute("""

        CREATE INDEX IF NOT EXISTS idx_universe_rankings_symbol

        ON universe_rankings(symbol)

    """)

    cur.execute("""

        CREATE INDEX IF NOT EXISTS idx_universe_rankings_symbol_date

        ON universe_rankings(symbol, snapshot_date)

    """)



    # =====================================
    # ALERT HISTORY
    # =====================================
    cur.execute("""

        CREATE TABLE IF NOT EXISTS alert_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date TEXT NOT NULL,

            timestamp TEXT NOT NULL,

            status TEXT NOT NULL,

            source TEXT NOT NULL,

            level TEXT NOT NULL,

            message TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )

    """)

    
    # =====================================
    # REGIME HISTORY
    # =====================================
    cur.execute("""

        CREATE TABLE IF NOT EXISTS regime_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date TEXT NOT NULL,

            regime TEXT NOT NULL,

            vix REAL,

            spy_close REAL,

            spy_200dma REAL,

            qqq_close REAL,

            qqq_200dma REAL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

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
    # PORTFOLIO HISTORY
    # =====================================
    cur.execute("""

        CREATE TABLE IF NOT EXISTS portfolio_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date TEXT NOT NULL,

            equity REAL NOT NULL,

            cash REAL NOT NULL,

            market_value REAL NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

    """)

    # =====================================
    # PORTFOLIO HISTORY INDEX
    # =====================================
    cur.execute("""

        CREATE INDEX IF NOT EXISTS idx_portfolio_history_date

        ON portfolio_history(date)

    """)


    # =====================================
    # INSERT DEFAULT SYSTEM STATE
    # =====================================
    cur.execute(

        """

        INSERT OR IGNORE INTO system_state (

            id,
            starting_capital,
            current_equity,
            current_cash,
            market_regime,
            current_leader,
            next_rebalance_date,
            last_rebalance_date

        )

        VALUES (

            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?

        )

        """,

        (

            1,
            START_CAPITAL,
            START_CAPITAL,
            START_CAPITAL,
            'UNKNOWN',
            '',
            '',
            ''

        )

    )

    conn.commit()

    conn.close()

    print(

        f"✅ Database initialized successfully "
        f"(Schema v{SCHEMA_VERSION})"

    )
# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    init_db()