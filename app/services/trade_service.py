import sqlite3
from datetime import datetime

DB_PATH = "trading_system.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


# =========================
# CHECK IF OPEN POSITION EXISTS
# =========================
def open_position_exists(symbol):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT 1 FROM positions
        WHERE symbol = ? AND status = 'OPEN'
    """, (symbol,))

    exists = c.fetchone() is not None
    conn.close()
    return exists


# =========================
# OPEN POSITION
# =========================
def open_position(symbol, entry_price, stop_price, shares):

    symbol = symbol.upper()

    if open_position_exists(symbol):
        return {"status": "error", "message": f"{symbol} already open"}

    conn = get_conn()
    c = conn.cursor()

    now = datetime.utcnow().isoformat()

    # Insert into positions
    c.execute("""
        INSERT INTO positions (
            symbol, entry_price, stop_price, shares, status, opened_at
        )
        VALUES (?, ?, ?, ?, 'OPEN', ?)
    """, (
        symbol,
        float(entry_price),
        float(stop_price),
        int(shares),
        now
    ))

    # Insert into trades (open record)
    c.execute("""
        INSERT INTO trades (
            symbol, entry_price, shares, opened_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        symbol,
        float(entry_price),
        int(shares),
        now
    ))

    # 🔥 MARK SIGNAL AS EXECUTED
    c.execute("""
        UPDATE signals
        SET status = 'EXECUTED'
        WHERE symbol = ? AND status = 'PENDING'
    """, (symbol,))

    conn.commit()
    conn.close()

    return {"status": "success", "symbol": symbol}


# =========================
# CLOSE POSITION
# =========================
def close_position(symbol, exit_price):

    symbol = symbol.upper()

    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT id, entry_price, shares, stop_price
        FROM positions
        WHERE symbol = ? AND status = 'OPEN'
    """, (symbol,))

    row = c.fetchone()

    if not row:
        conn.close()
        return {"status": "error", "message": f"No open position for {symbol}"}

    pos_id, entry_price, shares, stop_price = row

    now = datetime.utcnow().isoformat()

    pnl = (float(exit_price) - entry_price) * shares

    risk_per_share = entry_price - stop_price
    r_multiple = (float(exit_price) - entry_price) / risk_per_share if risk_per_share > 0 else 0

    # Close position
    c.execute("""
        UPDATE positions
        SET status = 'CLOSED', closed_at = ?
        WHERE id = ?
    """, (now, pos_id))

    # Update trade
    c.execute("""
        UPDATE trades
        SET exit_price = ?, pnl = ?, r_multiple = ?, closed_at = ?
        WHERE symbol = ? AND closed_at IS NULL
    """, (
        float(exit_price),
        float(pnl),
        float(r_multiple),
        now,
        symbol
    ))

    # 🔥 MARK SIGNAL AS CLOSED
    c.execute("""
        UPDATE signals
        SET status = 'CLOSED'
        WHERE symbol = ?
    """, (symbol,))

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

    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT symbol, entry_price, stop_price, shares
        FROM positions
        WHERE status = 'OPEN'
    """)

    rows = c.fetchall()
    conn.close()

    return [
        {
            "symbol": r[0],
            "entry": float(r[1]),
            "stop": float(r[2]),
            "shares": int(r[3])
        }
        for r in rows
    ]


# =========================
# GET TRADE HISTORY
# =========================
def get_trade_history():

    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT symbol, entry_price, exit_price, pnl, r_multiple
        FROM trades
        WHERE closed_at IS NOT NULL
        ORDER BY closed_at DESC
    """)

    rows = c.fetchall()
    conn.close()

    return [
        {
            "symbol": r[0],
            "entry": float(r[1]),
            "exit": float(r[2]) if r[2] else None,
            "pnl": float(r[3]) if r[3] else 0,
            "r": float(r[4]) if r[4] else 0
        }
        for r in rows
    ]