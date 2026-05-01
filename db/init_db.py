import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "trading_system.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Signals table
    c.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        signal_date TEXT,
        score REAL,
        entry_price REAL,
        stop_price REAL,
        target_price REAL
    )
    """)

    # Trades table
    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        entry_price REAL,
        stop_price REAL,
        target_price REAL,
        position_size REAL,
        entry_date TEXT,
        exit_date TEXT,
        exit_price REAL,
        exit_reason TEXT,
        pnl REAL,
        r_multiple REAL
    )
    """)

    # Positions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        symbol TEXT PRIMARY KEY,
        entry_price REAL,
        stop_price REAL,
        target_price REAL,
        position_size REAL,
        entry_date TEXT
    )
    """)

    # Wash sale tracking
    c.execute("""
    CREATE TABLE IF NOT EXISTS wash_sales (
        symbol TEXT PRIMARY KEY,
        last_loss_date TEXT
    )
    """)

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully")


if __name__ == "__main__":
    init_db()