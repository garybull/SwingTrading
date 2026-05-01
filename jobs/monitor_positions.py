import time
import sqlite3
import pandas as pd
import yfinance as yf

from jobs.send_email import send_email

DB_PATH = "trading_system.db"


def safe_price(df):
    if df is None or df.empty:
        return None

    close = df["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    return float(close.iloc[-1])


def col_or_default(columns, *names, default=None):
    for n in names:
        if n in columns:
            return n
    return default


def check_positions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("PRAGMA table_info(trades)")
    columns = [col[1] for col in c.fetchall()]

    entry_col = col_or_default(columns, "entry_price", "entry")
    stop_col = col_or_default(columns, "stop_price", "stop")
    shares_col = col_or_default(columns, "shares", default=None)

    has_status = "status" in columns
    has_trigger = "stop_triggered" in columns

    if not entry_col or not stop_col:
        print("❌ Missing entry/stop columns")
        return

    select_fields = ["symbol", stop_col]

    if has_trigger:
        select_fields.append("COALESCE(stop_triggered, 0)")
    else:
        select_fields.append("0")

    select_fields.append(entry_col)

    if shares_col:
        select_fields.append(shares_col)
    else:
        select_fields.append("1")

    query = f"SELECT {', '.join(select_fields)} FROM trades"

    if has_status:
        query += " WHERE status = 'OPEN'"

    c.execute(query)
    positions = c.fetchall()

    alerts = []

    for symbol, stop, triggered, entry, shares in positions:

        if has_trigger and triggered == 1:
            continue

        try:
            df = yf.download(symbol, period="1d", interval="1m", progress=False)

            price = safe_price(df)
            if price is None:
                continue

            if price <= float(stop):

                shares = float(shares)
                entry = float(entry)

                pnl = (price - entry) * shares
                pct = ((price / entry) - 1) * 100

                alerts.append({
                    "symbol": symbol,
                    "price": price,
                    "stop": stop,
                    "entry": entry,
                    "shares": shares,
                    "pnl": pnl,
                    "pct": pct
                })

                if has_trigger:
                    c.execute("""
                        UPDATE trades
                        SET stop_triggered = 1
                        WHERE symbol = ?
                    """, (symbol,))
                    conn.commit()

        except Exception as e:
            print(f"Error with {symbol}: {e}")

    conn.close()

    if alerts:
        subject = f"🚨 STOP ALERTS ({len(alerts)})"

        body = "\n\n".join([
            f"""Symbol: {a['symbol']}
Price: {round(a['price'], 2)}
Stop: {round(a['stop'], 2)}
Entry: {round(a['entry'], 2)}
Shares: {a['shares']}
P&L: ${round(a['pnl'], 2)}
Return: {round(a['pct'], 2)}%
"""
            for a in alerts
        ])

        send_email(subject, body)
        print(f"📧 Sent {len(alerts)} alerts")


if __name__ == "__main__":
    print("🚀 Monitoring positions...")

    while True:
        check_positions()
        time.sleep(60)





