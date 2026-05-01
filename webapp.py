from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import yfinance as yf
import threading
import time

from app.trade_logger import (
    log_trade_entry,
    log_trade_exit,
    get_open_positions,
    get_trade_history
)

app = Flask(__name__)

DB_PATH = "trading_system.db"

SCAN_STATUS = {
    "running": False,
    "message": "Idle"
}


# =========================
# DB HELPERS
# =========================
def get_scan_results():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT symbol, score, entry_price, stop_price, target_price, strong, shares, weight
        FROM scan_results
        ORDER BY score DESC
    """)

    rows = c.fetchall()
    conn.close()

    return [
        {
            "symbol": r[0],
            "score": float(r[1]),
            "entry": float(r[2]),
            "stop": float(r[3]),
            "target": float(r[4]),
            "strong": bool(r[5]),
            "shares": int(r[6]) if r[6] else 0,
            "weight": float(r[7]) if r[7] else 1.0
        }
        for r in rows
    ]


# =========================
# ROUTES
# =========================
@app.route("/")
def dashboard():
    results = get_scan_results()
    return render_template(
        "dashboard.html",
        top5=results[:5],
        strong=[r for r in results if r["strong"]]
    )


@app.route("/trade_plan")
def trade_plan():
    return render_template("trade_plan.html", trades=get_scan_results())


@app.route("/run_scan")
def run_scan_route():
    from jobs.premarket_scan import run

    if SCAN_STATUS["running"]:
        return redirect("/")

    def background():
        try:
            SCAN_STATUS["running"] = True
            SCAN_STATUS["message"] = "Scanning market..."

            run(return_results=False)

            SCAN_STATUS["message"] = "Scan complete"
            time.sleep(3)
            SCAN_STATUS["message"] = "Idle"

        except Exception as e:
            SCAN_STATUS["message"] = f"Error: {str(e)}"
        finally:
            SCAN_STATUS["running"] = False

    threading.Thread(target=background).start()
    return redirect("/")


@app.route("/scan_status")
def scan_status():
    return jsonify(SCAN_STATUS)


@app.route("/positions")
def positions():
    data = get_open_positions()

    if not data:
        return render_template("positions.html", positions=[])

    symbols = [p["symbol"] for p in data]

    # fetch latest prices
    df = yf.download(
        symbols,
        period="1d",
        interval="1m",
        group_by="ticker",
        auto_adjust=True,
        progress=False
    )

    enriched = []

    for p in data:
        symbol = p["symbol"]
        entry = float(p["entry"])
        shares = int(p["shares"])

        try:
            if len(symbols) == 1:
                price = float(df["Close"].iloc[-1])
            else:
                price = float(df[symbol]["Close"].iloc[-1])
        except:
            price = entry  # fallback

        pnl = (price - entry) * shares
        pnl_pct = ((price - entry) / entry) * 100

        enriched.append({
            **p,
            "price": round(price, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2)
        })

    return render_template("positions.html", positions=enriched)


@app.route("/history")
def history():
    return render_template("history.html", trades=get_trade_history())


@app.route("/add_trade", methods=["POST"])
def add_trade():
    log_trade_entry(
        request.form["symbol"],
        float(request.form["entry"]),
        float(request.form["stop"]),
        float(request.form["target"]),
        int(request.form["shares"])
    )
    return redirect("/positions")


@app.route("/close_trade", methods=["POST"])
def close_trade():
    log_trade_exit(
        request.form["symbol"],
        float(request.form["exit_price"]),
        request.form.get("reason", "MANUAL")
    )
    return redirect("/positions")


@app.route("/chart_data/<symbol>")
def chart_data(symbol):
    df = yf.download(symbol, period="60d", interval="1h", auto_adjust=True)

    if df.empty:
        return jsonify([])

    df = df.sort_index()

    return jsonify([
        {
            "time": int(idx.timestamp()),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"])
        }
        for idx, row in df.iterrows()
    ])


if __name__ == "__main__":
    app.run(debug=True)