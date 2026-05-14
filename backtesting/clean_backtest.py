# backtesting/clean_backtest.py

# =========================
# IMPORTS
# =========================
import pandas as pd
import numpy as np
import yfinance as yf

from app.strategy import score_asset


# =========================
# CONFIG
# =========================
START_CAPITAL = 90000
REBALANCE_OFFSET = 0

TOP_N = 1

REBALANCE_DAYS = 10

UNIVERSE = [

    "TQQQ",
    "SOXL",
    "TECL",
    "UPRO",
    "USD",
    "SPY",
    "QQQ"

]


# =========================
# SAFE SCALAR
# =========================
def safe_scalar(x):

    if isinstance(x, pd.Series):
        return float(x.iloc[-1])

    return float(x)


# =========================
# LOAD DATA
# =========================
def load_data():

    print("⬇️ Downloading data...")

    data = {}

    for symbol in UNIVERSE:

        df = yf.download(

            symbol,

            start="2010-01-01",

            auto_adjust=True,

            progress=False

        )

        if df is None or len(df) < 250:
            continue

        df.sort_index(inplace=True)

        data[symbol] = df

    return data


# =========================
# MARKET REGIME FILTER
# =========================
def market_is_bullish(spy_df, date):

    hist = spy_df.loc[:date]

    if len(hist) < 200:
        return False

    close = safe_scalar(
        hist["Close"].iloc[-1]
    )

    ma200 = safe_scalar(
        hist["Close"]
        .rolling(200)
        .mean()
        .iloc[-1]
    )

    return close > ma200


# =========================
# MAIN BACKTEST
# =========================
def run_backtest():

    print("🚀 STARTING MOMENTUM ROTATION BACKTEST")

    data = load_data()

    spy_df = data["SPY"]

    dates = spy_df.index

    capital = START_CAPITAL

    equity_curve = []

    positions = {}

    trades = []

    for i in range(200, len(dates)):

        date = dates[i]

        # =========================
        # MARK TO MARKET
        # =========================
        equity = capital

        for symbol, shares in positions.items():

            df = data[symbol]

            if date not in df.index:
                continue

            close = safe_scalar(
                df.loc[date]["Close"]
            )

            equity += (
                shares
                * close
                * (1 - SLIPPAGE)
            )

        equity_curve.append(equity)

        # =========================
        # REBALANCE ONLY WEEKLY
        # =========================
        if (i + REBALANCE_OFFSET) % REBALANCE_DAYS != 0:
            continue

        # =========================
        # MARKET FILTER
        # =========================
        if not market_is_bullish(
            spy_df,
            date
        ):

            # Liquidate everything
            positions = {}

            capital = equity

            continue

        # =========================
        # SCORE ASSETS
        # =========================
        scores = []

        for symbol in UNIVERSE:

            if symbol == "SPY":
                continue

            df = data[symbol]

            hist = df.loc[:date]

            result = score_asset(
                hist,
                symbol
            )

            if result:
                scores.append(result)

        # =========================
        # SORT BY SCORE
        # =========================
        scores.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        leaders = scores[:TOP_N]

        if len(leaders) == 0:
            continue

        # =========================
        # RESET PORTFOLIO
        # =========================
        positions = {}

        capital = equity

        # =========================
        # VOLATILITY-WEIGHTED
        # =========================
        inverse_vols = []

        for asset in leaders:

            inverse_vol = (
                1 / asset["volatility"]
            )

            inverse_vols.append(
                inverse_vol
            )

        total_inverse_vol = sum(
            inverse_vols
        )

        # =========================
        # BUILD NEW PORTFOLIO
        # =========================
        for idx, asset in enumerate(leaders):

            symbol = asset["symbol"]

            df = data[symbol]

            if date not in df.index:
                continue

            close = safe_scalar(
                df.loc[date]["Close"]
            )

            weight = (
                inverse_vols[idx]
                / total_inverse_vol
            )

            allocation = (
                capital * weight *.85
            )

            shares = int(
                allocation / close
            )

            if shares <= 0:
                continue

            # Cost of position
            SLIPPAGE = 0.001

            cost = (
                shares
                * close
                * (1 + SLIPPAGE)
            )

            # Deduct cash
            capital -= cost

            positions[symbol] = shares

        # =========================
        # TRACK REBALANCES
        # =========================
        trades.append(
            len(leaders)
        )

        # =========================
        # DEBUG
        # =========================
        if i % 100 == 0:

            print(
                f"{date.date()} | "
                f"Equity: {round(equity,2)} | "
                f"Positions: {list(positions.keys())}"
            )

    # =========================
    # FINAL STATS
    # =========================
    final_equity = equity_curve[-1]

    years = (
        len(equity_curve)
        / 252
    )

    cagr = (
        (
            final_equity
            / START_CAPITAL
        ) ** (1 / years)
        - 1
    ) * 100

    peak = -np.inf

    max_dd = 0

    for x in equity_curve:

        peak = max(
            peak,
            x
        )

        dd = (
            peak - x
        ) / peak

        max_dd = max(
            max_dd,
            dd
        )

    # =========================
    # RESULTS
    # =========================
    print("\n===== RESULTS =====")

    print(
        f"Final Equity: "
        f"{round(final_equity,2)}"
    )

    print(
        f"CAGR: "
        f"{round(cagr,2)}%"
    )

    print(
        f"Max Drawdown: "
        f"{round(max_dd * 100,2)}%"
    )

    print(
        f"Rebalances: "
        f"{len(trades)}"
    )


# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_backtest()