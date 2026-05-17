# webapp.py
import pandas as pd
import sqlite3
import json
import plotly.graph_objs as go
import plotly.utils
from app.regime_engine import determine_market_regime
from app.trading_cycle import (
    run_trading_cycle
)
from app.health_engine import (
    get_health_report
)
from app.alert_engine import (
    get_alert_report
)
from app.alert_history import (

    load_alert_history,
    get_alert_stats
)
from app.regime_engine import (

    determine_market_regime,
    get_suggested_exposure
)
from app.alert_engine import (
    get_alert_report
)
from app.drawdown_engine import (
    get_drawdown_report
)
from app.risk_engine import (
    get_risk_report
)
from app.regime_service import (
    load_latest_regime
)
from app.pnl_engine import (
    get_pnl_summary
)
from app.portfolio import (
    get_dashboard_data
)
from app.portfolio_state import refresh_system_state
from app.recommendation_service import (
    build_recommendations_page
)
from app.chart_engine import (
    build_recommendation_chart
)
from app.pnl_engine import (
    get_pnl_summary
)

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
# DASHBOARD
# =====================================
@app.route("/")
def dashboard():

    logger.info(
        "Loading dashboard..."
    )

    data = get_dashboard_data()

    regime = load_latest_regime()

    risk_report = (
        get_risk_report()
    )
    health_report = (
        get_health_report()
    )
    drawdown_report = (
        get_drawdown_report()
    )
    alert_report = (
        get_alert_report()
    )
    suggested_exposure = (
        get_suggested_exposure()
    )


    return render_template(

        "dashboard.html",

        positions=data["positions"],

        rankings=data["rankings"],

        rebalance_history=
            data["rebalance_history"],

        executed_trades=
            data["executed_trades"],

        recommended_portfolio=
            data["recommended_portfolio"],

        equity_curve=
            data["equity_curve"],

        system_state=
            data["system_state"],

        performance=
            data["performance"],

        drawdown=
            data["drawdown"],

        latest_rebalance=
            data["latest_rebalance"],

        pnl_summary=
            data["pnl_summary"],

        regime=
            regime,

        risk_report=
            risk_report,

        health_report=
            health_report,

        suggested_exposure=
            suggested_exposure,
        drawdown_report=
            drawdown_report,
        alert_report=
            alert_report

    )

# =====================================
# RUN SCAN
# =====================================
@app.route(
    "/run_scan",
    methods=["POST"]
)
def run_scan_route():

    logger.info(
        "Running trading cycle..."
    )

    run_trading_cycle()

    return redirect(
        url_for(
            "recommendations"
        )
    )

# =====================================
# P/L ANALYTICS
# =====================================
@app.route("/pnl")

def pnl():

    pnl_data = get_pnl_summary()

    return render_template(

        "pnl.html",

        unrealized_positions=
            pnl_data[
                "unrealized_positions"
            ].to_dict("records"),

        total_unrealized=
            pnl_data[
                "total_unrealized"
            ],

        realized_trades=
            pnl_data[
                "realized_trades"
            ].to_dict("records"),

        total_realized=
            pnl_data[
                "total_realized"
            ]

    )

# =====================================
# ALERT CENTER
# =====================================
@app.route("/alerts")
def alerts():

    logger.info(
        "Loading alerts dashboard..."
    )

    alert_report = (
        get_alert_report()
    )

    alert_history = (
        load_alert_history()
    )

    alert_stats = (
        get_alert_stats()
    )

    return render_template(

        "alerts.html",

        alert_report=
            alert_report,

        alert_history=
            alert_history,

        alert_stats=
            alert_stats

    )


# =====================================
# P/L ANALYTICS
# =====================================
@app.route("/pnl-analytics")

def pnl_analytics():

    pnl_data = get_pnl_summary()

    return render_template(

        "pnl.html",

        unrealized_positions=
            pnl_data[
                "unrealized_positions"
            ].to_dict("records"),

        total_unrealized=
            pnl_data[
                "total_unrealized"
            ],

        realized_trades=
            pnl_data[
                "realized_trades"
            ].to_dict("records"),

        total_realized=
            pnl_data[
                "total_realized"
            ]

    )
 

# =====================================
# BENCHMARKS
# =====================================
@app.route("/benchmarks")
def benchmarks():

    from app.benchmark_engine import (

        get_benchmark_report,
        get_system_curve,
        get_benchmark_curves

    )

    # =====================================
    # LOAD DATA
    # =====================================
    report = (
        get_benchmark_report()
    )

    system_curve = (
        get_system_curve()
    )

    benchmark_curves = (
        get_benchmark_curves()
    )

    # =====================================
    # EQUITY CHART
    # =====================================
    equity_fig = go.Figure()

    # =====================================
    # SYSTEM CURVE
    # =====================================
    if not system_curve.empty:

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

    # =====================================
    # BENCHMARK CURVES
    # =====================================
    for symbol, curve in benchmark_curves.items():

        if curve.empty:

            continue

        equity_fig.add_trace(

            go.Scatter(

                x=curve["date"],

                y=curve[
                    "normalized"
                ],

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

    # =====================================
    # SYSTEM DRAWDOWN
    # =====================================
    if not system_curve.empty:

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

    # =====================================
    # BENCHMARK DRAWDOWNS
    # =====================================
    for symbol, curve in benchmark_curves.items():

        if curve.empty:

            continue

        dd = (

            curve["normalized"]

            / curve["normalized"]
            .cummax()

            - 1

        ) * 100

        dd_fig.add_trace(

            go.Scatter(

                x=curve["date"],

                y=dd,

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
# Recommendations
# =====================================
@app.route("/recommendations")
def recommendations():

    logger.info(
        "Loading recommendations page..."
    )

    page_data = (
        build_recommendations_page()
    )
    regime=determine_market_regime()
    
    return render_template(

        "recommendations.html",

        actions=
            page_data["actions"],

        positions=
            page_data["positions"]
        

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

    from app.execution_engine import (
        execute_buy,
        execute_sell
    )

    symbol = request.form.get(
        "symbol"
    ).upper()

    side = request.form.get(
        "side"
    ).upper()

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
        "notes",
        ""
    )

    logger.info(

        f"MANUAL TRADE | "
        f"{side} "
        f"{shares} "
        f"{symbol} @ "
        f"${fill_price:.2f}"

    )

    # =====================================
    # BUY
    # =====================================
    if side == "BUY":

        execute_buy(

            symbol,
            shares,
            fill_price,
            notes=notes

        )

    # =====================================
    # SELL
    # =====================================
    elif side == "SELL":

        execute_sell(

            symbol,
            shares,
            fill_price,
            notes=notes

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