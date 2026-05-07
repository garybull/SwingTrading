import sqlite3
from datetime import datetime

DB_PATH = "trading_system.db"
START_CAPITAL = 90000


def reset_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("⚠️ Resetting trading system...")

    # -------------------------
    # DROP DATA (KEEP TABLES)
    # -------------------------
    c.execute("DELETE FROM signals")
    c.execute("DELETE FROM positions")
    c.execute("DELETE FROM trades")

    # -------------------------
    # OPTIONAL: RESET SQLITE AUTOINCREMENT
    # -------------------------
    c.execute("DELETE FROM sqlite_sequence WHERE name='signals'")
    c.execute("DELETE FROM sqlite_sequence WHERE name='positions'")
    c.execute("DELETE FROM sqlite_sequence WHERE name='trades'")

    # -------------------------
    # RESET ACCOUNT / CAPITAL
    # -------------------------
    # Create account table if it doesn't exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY,
            capital REAL,
            updated_at TEXT
        )
    """)

    c.execute("DELETE FROM account")

    c.execute("""
        INSERT INTO account (id, capital, updated_at)
        VALUES (1, ?, ?)
    """, (START_CAPITAL, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()

    print("✅ System reset complete")
    print(f"💰 Capital reset to ${START_CAPITAL:,}")


if __name__ == "__main__":
    confirm = input("Type 'RESET' to confirm: ")

    if confirm == "RESET":
        reset_database()
    else:
        print("❌ Reset cancelled")