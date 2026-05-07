from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import json
import yfinance as yf
import threading


from app.services.trade_service import (
    open_position,
    close_position,
    get_open_positions,
    get_trade_history
)

app = Flask(__name__)

DB_PATH = "trading_system.db"

SCAN_PROGRESS = {
    "running": False,
    "current": 0,
    "total": 0,
    "message": "Idle"
}

# =========================
# SCAN RESULTS
# =========================
import json

import json

def get_scan_results():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT 
            symbol,
            score,
            entry,
            stop,
            target,
            shares,
            weight,
            setup,
            reasons
        FROM signals
        WHERE status = 'PENDING'
        ORDER BY score DESC
    """)

    rows = c.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "symbol": r[0],
            "score": float(r[1]),
            "entry": float(r[2]),
            "stop": float(r[3]),
            "target": float(r[4]) if r[4] else None,
            "shares": int(r[5]),
            "weight": float(r[6]),
            "setup": r[7] or "Unknown",
            "reasons": json.loads(r[8]) if r[8] else []
        })

    return results

# =========================
# PERFORMANCE
# =========================
def get_performance_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT pnl, r_multiple
        FROM trades
        WHERE pnl IS NOT NULL
    """)

    rows = c.fetchall()
    conn.close()

    if not rows:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "avg_r": 0,
            "expectancy": 0,
            "total_pnl": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "equity_curve": []
        }

    total = len(rows)

    wins = [r for r in rows if r[0] > 0]
    losses = [r for r in rows if r[0] <= 0]

    win_rate = len(wins) / total if total else 0

    avg_r = sum(r[1] for r in rows) / total

    avg_win_r = sum(r[1] for r in wins) / len(wins) if wins else 0
    avg_loss_r = sum(r[1] for r in losses) / len(losses) if losses else 0

    expectancy = (win_rate * avg_win_r) + ((1 - win_rate) * avg_loss_r)

    total_pnl = sum(r[0] for r in rows)

    # PROFIT FACTOR
    gross_win = sum(r[0] for r in wins)
    gross_loss = abs(sum(r[0] for r in losses))
    profit_factor = gross_win / gross_loss if gross_loss > 0 else 0

    # EQUITY + DRAWDOWN
    equity = []
    running = 0
    peak = 0
    max_dd = 0

    for pnl, _ in rows:
        running += pnl
        equity.append(running)

        peak = max(peak, running)
        dd = running - peak
        max_dd = min(max_dd, dd)

    return {
        "total_trades": total,
        "win_rate": round(win_rate * 100, 2),
        "avg_r": round(avg_r, 2),
        "expectancy": round(expectancy, 2),
        "total_pnl": round(total_pnl, 2),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown": round(max_dd, 2),
        "equity_curve": equity
    }

# =========================
# Setup Performance 
# =========================
def get_setup_performance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT setup, pnl, r_multiple
        FROM trades
        WHERE closed_at IS NOT NULL
        AND setup IS NOT NULL
    """)

    rows = c.fetchall()
    conn.close()

    stats = {}

    for setup, pnl, r in rows:

        if setup not in stats:
            stats[setup] = {
                "trades": 0,
                "wins": 0,
                "total_pnl": 0,
                "total_r": 0
            }

        stats[setup]["trades"] += 1
        stats[setup]["total_pnl"] += pnl
        stats[setup]["total_r"] += r

        if pnl > 0:
            stats[setup]["wins"] += 1

    results = []

    for setup, s in stats.items():
        trades = s["trades"]

        results.append({
            "setup": setup,
            "trades": trades,
            "win_rate": round((s["wins"] / trades) * 100, 2),
            "avg_r": round(s["total_r"] / trades, 2),
            "total_pnl": round(s["total_pnl"], 2)
        })

    return sorted(results, key=lambda x: x["avg_r"], reverse=True)

# =========================
# Scanner
# =========================

def run_scan_background():
    from jobs.premarket_scan import run, UNIVERSE

    SCAN_PROGRESS["running"] = True
    SCAN_PROGRESS["current"] = 0
    SCAN_PROGRESS["total"] = len(UNIVERSE)
    SCAN_PROGRESS["message"] = "Starting..."

    def progress_callback(symbol, idx, total):
        SCAN_PROGRESS["current"] = idx
        SCAN_PROGRESS["total"] = total
        SCAN_PROGRESS["message"] = f"Scanning {symbol} ({idx}/{total})"

    run(progress_callback=progress_callback)

    SCAN_PROGRESS["running"] = False
    SCAN_PROGRESS["message"] = "✅ Scan complete"


# =========================
# ROUTES
# =========================
@app.route("/")
def dashboard():
    results = get_scan_results()
    return render_template("dashboard.html", top5=results[:5])


@app.route("/trade_plan")
def trade_plan():
    results = get_scan_results()
    return render_template("trade_plan.html", trades=results)


@app.route("/run_scan")
def run_scan_route():
    if not SCAN_PROGRESS["running"]:
        threading.Thread(target=run_scan_background).start()

    return jsonify({"status": "started"})

@app.route("/scan_status")
def scan_status():
    return jsonify(SCAN_PROGRESS)


@app.route("/positions")
def positions():
    data = get_open_positions()
    return render_template("positions.html", positions=data)


@app.route("/history")
def history():
    data = get_trade_history()
    return render_template("history.html", trades=data)


@app.route("/performance")
def performance():
    stats = get_performance_stats()
    return render_template("performance.html", stats=stats)


# =========================
# EXECUTION
# =========================
@app.route("/add_trade", methods=["POST"])
def add_trade():
    open_position(
        request.form["symbol"],
        float(request.form["entry"]),
        float(request.form["stop"]),
        int(request.form["shares"]),
        setup=request.form.get("setup")  # 🔥 NEW
    )
    return redirect("/positions")


@app.route("/close_trade", methods=["POST"])
def close_trade():
    symbol = request.form["symbol"]
    exit_price = float(request.form["exit_price"])
    shares = int(request.form["shares"])
    grade = request.form.get("grade")
    notes = request.form.get("notes")

    close_position(symbol, exit_price, shares, grade, notes)

    return redirect("/positions")

@app.route("/setup_performance")
def setup_performance():
    data = get_setup_performance()
    return render_template("setup_performance.html", data=data)

# =========================
# CHART DATA
# =========================
@app.route("/chart_data/<symbol>")
def chart_data(symbol):
    df = yf.download(symbol, period="60d", interval="1h", auto_adjust=True)

    if df is None or df.empty:
        return jsonify([])

    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    df = df.sort_index()

    data = []

    for idx, row in df.iterrows():
        try:
            data.append({
                "time": int(idx.timestamp()),  # 🔥 seconds (correct)
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"])
            })
        except:
            continue

    return jsonify(data)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)