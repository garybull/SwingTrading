import sqlite3

DB_PATH = "trading_system.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# =========================
# SIGNALS TABLE (scanner output)
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    score REAL,
    entry REAL,
    stop REAL,
    target REAL,
    shares INTEGER,
    weight REAL,
    status TEXT DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# =========================
# POSITIONS (SOURCE OF TRUTH)
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    entry_price REAL NOT NULL,
    stop_price REAL NOT NULL,
    shares INTEGER NOT NULL,
    status TEXT NOT NULL, -- OPEN, CLOSED
    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME
)
""")

# =========================
# TRADES (HISTORY ONLY)
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    shares INTEGER NOT NULL,
    pnl REAL,
    r_multiple REAL,
    opened_at DATETIME,
    closed_at DATETIME
)
""")

# =========================
# ORDERS (FUTURE USE)
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    side TEXT,
    qty INTEGER,
    price REAL,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# =========================
# INDEXES (CRITICAL FOR SAFETY)
# =========================
c.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_open_position
ON positions(symbol)
WHERE status = 'OPEN'
""")

conn.commit()
conn.close()

print("✅ Clean DB initialized successfully")