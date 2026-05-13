# webapp.py

import sqlite3
import json
import plotly.graph_objs as go
import plotly.utils
from flask import (

    Flask,
    render_template,
    request,
    redirect,
    url_for

)
from production.daily_rebalance import (
    main as run_rebalance
)
from app.portfolio import (
    get_dashboard_data
)

from app.config import (

    WEB_HOST,
    WEB_PORT,
    DB_NAME

)

from app.logger import logger


# =====================================
# APP
# =====================================
app = Flask(__name__)


# =====================================
# DB CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# BUILD EQUITY CHART
# =====================================
def build_equity_chart(equity_curve):

    equity_fig = go.Figure()

    equity_fig.add_trace(

        go.Scatter(

            x=equity_curve["date"],

            y=equity_curve["equity"],

            mode="lines",

            name="Equity"

        )

    )

    equity_fig.update_layout(

        title="Portfolio Equity Curve",

        template="plotly_dark",

        height=500

    )

    return json.dumps(

        equity_fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )


# =====================================
# MAIN DASHBOARD
# =====================================
@app.route("/")
def dashboard():

    data = get_dashboard_data()

    system_state = (
        data["system_state"]
    )

    performance = (
        data["performance"]
    )

    drawdown = (
        data["drawdown"]
    )

    equity_curve = (
        data["equity_curve"]
    )

    equity_chart = build_equity_chart(
        equity_curve
    )

    pnl_summary = (
        data["pnl_summary"]
    )

    return render_template(

        "dashboard.html",

        system_state=system_state,

        performance=performance,

        drawdown=drawdown,

        equity_chart=equity_chart,

        pnl_summary=pnl_summary

    )


# =====================================
# RECOMMENDATIONS PAGE
# =====================================
@app.route("/recommendations")
def recommendations():

    data = get_dashboard_data()

    return render_template(

        "recommendations.html",

        recommended_portfolio=(
            data["recommended_portfolio"]
            .to_dict(orient="records")
        ),

        positions=(
            data["positions"]
            .to_dict(orient="records")
        ),

        rankings=(
            data["rankings"]
            .to_dict(orient="records")
        )

    )

# =====================================
# PNL
# =====================================

@app.route("/pnl")
def pnl():

    data = get_dashboard_data()

    pnl_summary = data[
        "pnl_summary"
    ]

    return render_template(

        "pnl.html",

        unrealized_positions=(
            pnl_summary[
                "unrealized_positions"
            ].to_dict(
                orient="records"
            )
        ),

        realized_trades=(
            pnl_summary[
                "realized_trades"
            ].to_dict(
                orient="records"
            )
        ),

        total_unrealized=(
            pnl_summary[
                "total_unrealized"
            ]
        ),

        total_realized=(
            pnl_summary[
                "total_realized"
            ]
        )

    )
# =====================================
# RUN SCAN
# =====================================
@app.route(

    "/run_scan",

    methods=["POST"]

)
def run_scan():

    logger.info(
        "🚀 Manual scan triggered"
    )

    try:

        run_rebalance()

        logger.info(
            "✅ Manual scan complete"
        )

    except Exception as e:

        logger.error(

            f"❌ Manual scan failed: {e}"

        )

    return redirect(
        url_for("recommendations")
    )


# =====================================
# BENCHMARKS
# =====================================
@app.route("/benchmarks")
def benchmarks():

    from app.benchmark_engine import (
        get_benchmark_report
    )

    benchmark_data = (
        get_benchmark_report()
    )

    report = benchmark_data[
        "report"
    ]

    system_curve = benchmark_data[
        "system_curve"
    ]

    benchmark_curves = benchmark_data[
        "benchmark_curves"
    ]

    # =====================================
    # EQUITY CHART
    # =====================================
    equity_fig = go.Figure()

    # SYSTEM
    equity_fig.add_trace(

        go.Scatter(

            x=system_curve["date"],

            y=system_curve[
                "normalized"
            ],

            mode="lines",

            name="SYSTEM"

        )

    )

    # BENCHMARKS
    for symbol, curve in benchmark_curves.items():

        equity_fig.add_trace(

            go.Scatter(

                x=curve.index,

                y=curve.values,

                mode="lines",

                name=symbol

            )

        )

    equity_fig.update_layout(

        title="Equity Curve Comparison",

        template="plotly_dark",

        height=600

    )

    equity_chart = json.dumps(

        equity_fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )

    # =====================================
    # DRAWDOWN CHART
    # =====================================
    dd_fig = go.Figure()

    # SYSTEM DD
    system_dd = (

        system_curve["normalized"]

        / system_curve["normalized"]
        .cummax()

        - 1

    ) * 100

    dd_fig.add_trace(

        go.Scatter(

            x=system_curve["date"],

            y=system_dd,

            mode="lines",

            name="SYSTEM"

        )

    )

    # BENCHMARK DDS
    for symbol, curve in benchmark_curves.items():

        dd = (

            curve
            / curve.cummax()

            - 1

        ) * 100

        dd_fig.add_trace(

            go.Scatter(

                x=curve.index,

                y=dd.values,

                mode="lines",

                name=symbol

            )

        )

    dd_fig.update_layout(

        title="Drawdown Comparison",

        template="plotly_dark",

        height=600

    )

    drawdown_chart = json.dumps(

        dd_fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )

    return render_template(

        "benchmarks.html",

        report=report,

        equity_chart=equity_chart,

        drawdown_chart=drawdown_chart

    )


# =====================================
# TRADE ENTRY PAGE
# =====================================
@app.route("/trades")
def trades():

    data = get_dashboard_data()

    return render_template(

        "trades.html",

        executed_trades=(
            data["executed_trades"]
            .to_dict(orient="records")
        )

    )

# =====================================
# RECONCILE
# =====================================
@app.route("/reconcile")
def reconcile():

    from app.reconciliation import (
        rebuild_positions_from_trades
    )

    rebuild_positions_from_trades()

    return redirect("/")


# =====================================
# TRADE ANALYTICS
# =====================================
@app.route("/trade-analytics")
def trade_analytics():

    from app.trade_analytics import (
        get_trade_analytics
    )

    analytics = (
        get_trade_analytics()
    )

    return render_template(

        "trade_analytics.html",

        analytics=analytics

    )


# =====================================
# HISTORY PAGE
# =====================================
@app.route("/history")
def history():

    data = get_dashboard_data()

    return render_template(

        "history.html",

        rebalance_history=(
            data["rebalance_history"]
            .to_dict(orient="records")
        ),

        executed_trades=(
            data["executed_trades"]
            .to_dict(orient="records")
        )

    )

# =====================================
# RISK DASHBOARD
# =====================================
@app.route("/risk")
def risk():

    from app.risk_engine import (
        get_risk_report
    )

    risk_data = (
        get_risk_report()
    )

    return render_template(

        "risk.html",

        risk=risk_data

    )


# =====================================
# ROLLING ANALYTICS
# =====================================
@app.route("/rolling-analytics")
def rolling_analytics():

    from app.rolling_analytics import (
        get_rolling_analytics
    )

    rolling = (
        get_rolling_analytics()
    )

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if rolling.empty:

        return render_template(

            "rolling_analytics.html",

            rolling_metrics=[],

            return_chart="{}",

            sharpe_chart="{}",

            drawdown_chart="{}",

            volatility_chart="{}"

        )

    # =====================================
    # RETURN CHART
    # =====================================
    return_fig = go.Figure()

    return_fig.add_trace(

        go.Scatter(

            x=rolling["date"],

            y=rolling[
                "rolling_30d_return"
            ],

            mode="lines",

            name="30D Return"

        )

    )

    return_fig.update_layout(

        title="Rolling 30-Day Return",

        template="plotly_dark",

        height=500

    )

    return_chart = json.dumps(

        return_fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )

    # =====================================
    # SHARPE CHART
    # =====================================
    sharpe_fig = go.Figure()

    sharpe_fig.add_trace(

        go.Scatter(

            x=rolling["date"],

            y=rolling[
                "rolling_sharpe"
            ],

            mode="lines",

            name="Rolling Sharpe"

        )

    )

    sharpe_fig.update_layout(

        title="Rolling Sharpe Ratio",

        template="plotly_dark",

        height=500

    )

    sharpe_chart = json.dumps(

        sharpe_fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )

    # =====================================
    # DRAWDOWN CHART
    # =====================================
    drawdown_fig = go.Figure()

    drawdown_fig.add_trace(

        go.Scatter(

            x=rolling["date"],

            y=rolling[
                "rolling_drawdown"
            ],

            mode="lines",

            name="Drawdown"

        )

    )

    drawdown_fig.update_layout(

        title="Rolling Drawdown",

        template="plotly_dark",

        height=500

    )

    drawdown_chart = json.dumps(

        drawdown_fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )

    # =====================================
    # VOLATILITY CHART
    # =====================================
    volatility_fig = go.Figure()

    volatility_fig.add_trace(

        go.Scatter(

            x=rolling["date"],

            y=rolling[
                "rolling_volatility"
            ],

            mode="lines",

            name="Volatility"

        )

    )

    volatility_fig.update_layout(

        title="Rolling Volatility",

        template="plotly_dark",

        height=500

    )

    volatility_chart = json.dumps(

        volatility_fig,

        cls=plotly.utils.PlotlyJSONEncoder

    )

    # =====================================
    # LATEST METRICS
    # =====================================
    latest = rolling.iloc[-1]

    metrics = {

        "rolling_30d_return":

            round(

                latest[
                    "rolling_30d_return"
                ],

                2

            ),

        "rolling_sharpe":

            round(

                latest[
                    "rolling_sharpe"
                ],

                2

            ),

        "rolling_drawdown":

            round(

                latest[
                    "rolling_drawdown"
                ],

                2

            ),

        "rolling_volatility":

            round(

                latest[
                    "rolling_volatility"
                ],

                2

            )

    }

    return render_template(

        "rolling_analytics.html",

        rolling_metrics=metrics,

        return_chart=return_chart,

        sharpe_chart=sharpe_chart,

        drawdown_chart=drawdown_chart,

        volatility_chart=volatility_chart

    )


# =====================================
# LOG TRADE
# =====================================
@app.route(

    "/log_trade",

    methods=["POST"]

)
def log_trade():

    symbol = request.form.get(
        "symbol"
    )

    side = request.form.get(
        "side"
    )

    shares = int(

        request.form.get(
            "shares"
        )

    )

    fill_price = float(

        request.form.get(
            "fill_price"
        )

    )

    notes = request.form.get(
        "notes"
    )

    total_value = (
        shares * fill_price
    )

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

        INSERT INTO executed_trades (

            date,
            symbol,
            side,
            shares,
            fill_price,
            total_value,
            notes

        )

        VALUES (

            DATE('now'),

            ?, ?, ?, ?, ?, ?

        )

    """, (

        symbol.upper(),

        side.upper(),

        shares,

        fill_price,

        total_value,

        notes

    ))

    conn.commit()

    conn.close()

    logger.info(

        f"MANUAL TRADE | "
        f"{side.upper()} "
        f"{shares} "
        f"{symbol.upper()} @ "
        f"${fill_price:.2f}"

    )

    return redirect(
        url_for("trades")
    )


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    app.run(

        host=WEB_HOST,

        port=WEB_PORT,

        debug=True

    )