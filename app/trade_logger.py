import sqlite3
from datetime import datetime

DB_PATH = "trading_system.db"
MAX_POSITIONS = 10


# =========================
# INTERNAL HELPERS
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


def can_open_new_position():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM positions")
    count = c.fetchone()[0]

    conn.close()

    return count < MAX_POSITIONS


def position_exists(symbol):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT 1 FROM positions WHERE symbol = ?", (symbol,))
    exists = c.fetchone() is not None

    conn.close()
    return exists


# =========================
# OPEN TRADE (MANUAL ENTRY)
# =========================
def log_trade_entry(symbol, entry_price, stop_price, target_price, shares):
    symbol = symbol.upper()

    if position_exists(symbol):
        return {
            "status": "error",
            "message": f"Position already exists for {symbol}"
        }

    if not can_open_new_position():
        return {
            "status": "error",
            "message": "Max positions reached"
        }

    conn = get_connection()
    c = conn.cursor()

    entry_date = datetime.now().isoformat()

    # Insert into trades (history)
    c.execute("""
        INSERT INTO trades (
            symbol, entry_price, stop_price, target_price,
            position_size, entry_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        float(entry_price),
        float(stop_price),
        float(target_price),
        int(shares),
        entry_date
    ))

    trade_id = c.lastrowid

    # Insert into positions (active)
    c.execute("""
        INSERT INTO positions (
            symbol, entry_price, stop_price, target_price,
            position_size, entry_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        float(entry_price),
        float(stop_price),
        float(target_price),
        int(shares),
        entry_date
    ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "trade_id": trade_id,
        "symbol": symbol
    }


# =========================
# CLOSE TRADE
# =========================
def log_trade_exit(symbol, exit_price, exit_reason="MANUAL"):
    symbol = symbol.upper()

    conn = get_connection()
    c = conn.cursor()

    exit_date = datetime.now().isoformat()

    # Find latest open trade
    c.execute("""
        SELECT id, entry_price, position_size, stop_price
        FROM trades
        WHERE symbol = ? AND exit_date IS NULL
        ORDER BY entry_date DESC
        LIMIT 1
    """, (symbol,))

    row = c.fetchone()

    if not row:
        conn.close()
        return {
            "status": "error",
            "message": f"No open trade found for {symbol}"
        }

    trade_id, entry_price, shares, stop_price = row

    # Calculate PnL
    pnl = (exit_price - entry_price) * shares

    # Calculate R multiple
    risk_per_share = entry_price - stop_price
    r_multiple = (exit_price - entry_price) / risk_per_share if risk_per_share > 0 else 0

    # Update trade
    c.execute("""
        UPDATE trades
        SET exit_price = ?, exit_date = ?, exit_reason = ?, pnl = ?, r_multiple = ?
        WHERE id = ?
    """, (
        float(exit_price),
        exit_date,
        exit_reason,
        float(pnl),
        float(r_multiple),
        trade_id
    ))

    # Remove from positions
    c.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "symbol": symbol,
        "pnl": round(pnl, 2),
        "r_multiple": round(r_multiple, 2)
    }


# =========================
# GET OPEN POSITIONS
# =========================
def get_open_positions():
    conn = sqlite3.connect("trading_system.db")
    c = conn.cursor()

    # Detect schema dynamically
    c.execute("PRAGMA table_info(trades)")
    columns = [col[1] for col in c.fetchall()]

    entry_col = "entry_price" if "entry_price" in columns else "entry"
    stop_col = "stop_price" if "stop_price" in columns else "stop"

    shares_col = "shares" if "shares" in columns else None
    status_col = "status" if "status" in columns else None

    query = f"SELECT symbol, {entry_col}, {stop_col}"

    if shares_col:
        query += f", {shares_col}"
    else:
        query += ", 1"

    query += " FROM trades"

    if status_col:
        query += " WHERE status = 'OPEN'"

    c.execute(query)
    rows = c.fetchall()
    conn.close()

    positions = []

    for row in rows:
        symbol, entry, stop, shares = row

        positions.append({
            "symbol": symbol,
            "entry": float(entry),
            "stop": float(stop),
            "shares": float(shares)
        })

    return positions

# =========================
# GET TRADE HISTORY
# =========================
def get_trade_history():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT symbol, entry_price, exit_price, pnl, r_multiple,
               entry_date, exit_date
        FROM trades
        ORDER BY entry_date DESC
    """)

    rows = c.fetchall()
    conn.close()

    return [
        {
            "symbol": r[0],
            "entry": r[1],
            "exit": r[2],
            "pnl": r[3],
            "r": r[4],
            "entry_date": r[5],
            "exit_date": r[6]
        }
        for r in rows
    ]