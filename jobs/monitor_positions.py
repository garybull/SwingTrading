import time
import sqlite3
import yfinance as yf

from jobs.send_email import send_email

DB_PATH = "trading_system.db"


def get_open_positions():
    conn = sqlite3.connect(DB_PATH)
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


def get_price(symbol):
    try:
        df = yf.download(
            symbol,
            period="1d",
            interval="1m",
            progress=False
        )

        if df.empty:
            return None

        return float(df["Close"].iloc[-1])

    except:
        return None


def mark_stop_triggered(symbol):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Prevent duplicate alerts
    c.execute("""
        UPDATE positions
        SET status = 'CLOSING'
        WHERE symbol = ? AND status = 'OPEN'
    """, (symbol,))

    conn.commit()
    conn.close()


def check_positions():

    positions = get_open_positions()

    if not positions:
        return

    alerts = []

    for p in positions:
        symbol = p["symbol"]
        entry = p["entry"]
        stop = p["stop"]
        shares = p["shares"]

        price = get_price(symbol)

        if price is None:
            continue

        if price <= stop:

            pnl = (price - entry) * shares
            pct = ((price / entry) - 1) * 100

            alerts.append({
                "symbol": symbol,
                "price": price,
                "stop": stop,
                "pnl": pnl,
                "pct": pct
            })

            mark_stop_triggered(symbol)

    if alerts:
        body = "\n\n".join([
            f"""
🚨 STOP HIT

Symbol: {a['symbol']}
Price: {round(a['price'], 2)}
Stop: {round(a['stop'], 2)}
P&L: ${round(a['pnl'], 2)}
Return: {round(a['pct'], 2)}%
"""
            for a in alerts
        ])

        send_email(f"🚨 STOP ALERT ({len(alerts)})", body)
        print("📧 Stop alert sent")


if __name__ == "__main__":
    print("🚀 Monitoring positions...")

    while True:
        check_positions()
        time.sleep(60)