import sqlite3

conn = sqlite3.connect("trading_system.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS scan_results (
    symbol TEXT,
    score REAL,
    entry_price REAL,
    stop_price REAL,
    target_price REAL,
    strong INTEGER,
    shares INTEGER,
    weight REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS trades (
    symbol TEXT,
    entry REAL,
    exit REAL,
    stop REAL,
    target REAL,
    shares INTEGER,
    status TEXT,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ DB initialized")