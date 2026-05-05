import sqlite3
from jobs.send_email import send_email

DB_PATH = "trading_system.db"


def build_report():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT symbol, score, entry, stop, shares, weight
        FROM signals
        WHERE status = 'PENDING'
        ORDER BY score DESC
    """)

    rows = c.fetchall()
    conn.close()

    if not rows:
        return "No trade signals for today."

    lines = []
    lines.append("📈 MORNING TRADE PLAN\n")
    lines.append("=" * 40)

    total_capital = 0

    for r in rows:
        symbol, score, entry, stop, shares, weight = r

        position_value = entry * shares
        total_capital += position_value

        lines.append(f"""
Symbol: {symbol}
Score: {round(score, 2)}
Entry: ${round(entry, 2)}
Stop: ${round(stop, 2)}
Shares: {shares}
Position Size: ${round(position_value, 2)}
Weight: {round(weight, 2)}
------------------------------
""")

    lines.append("=" * 40)
    lines.append(f"Total Capital Deployed: ${round(total_capital, 2)}")

    return "\n".join(lines)


if __name__ == "__main__":
    send_email("📈 Morning Trading Plan", build_report())