import sqlite3
from jobs.send_email import send_email

def build_report():
    conn = sqlite3.connect("trading_system.db")
    c = conn.cursor()

    c.execute("SELECT symbol, score FROM scan_results ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()

    lines = ["Morning Scan Results:\n"]
    for r in rows:
        lines.append(f"{r[0]} | Score: {round(r[1], 2)}")

    return "\n".join(lines)

if __name__ == "__main__":
    send_email("📈 Morning Trading Plan", build_report())