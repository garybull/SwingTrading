# =========================
# IMPORTS
# =========================
import pandas as pd
import numpy as np
import pickle

from app.strategy import generate_signal


# =========================
# CONFIG
# =========================
START_CAPITAL = 90000

MAX_POSITIONS = 8
MAX_NEW = 3   # ↑ increased from 2

BASE_RISK = 0.025
EXPOSURE_MULT = 1.05   # 🔥 mild boost

ENTRY_SLIPPAGE = 0.0005
EXIT_SLIPPAGE = 0.0005

CACHE_FILE = "backtest_cache.pkl"


# =========================
# LOAD DATA
# =========================
def load_data():
    with open(CACHE_FILE, "rb") as f:
        data = pickle.load(f)
        print(f"Loaded data: {len(data)} symbols")
        return data


# =========================
# INDICATORS
# =========================
def precompute_indicators(data):
    for df in data.values():

        df["ma50"] = df["Close"].rolling(50).mean()

        tr = pd.concat([
            df["High"] - df["Low"],
            (df["High"] - df["Close"].shift()).abs(),
            (df["Low"] - df["Close"].shift()).abs()
        ], axis=1).max(axis=1)

        df["atr"] = tr.rolling(14).mean()

    return data


# =========================
# POSITION SIZE
# =========================
def calc_size(capital, entry, stop, risk_pct):
    risk_amount = capital * risk_pct
    risk_per_share = abs(entry - stop)

    if risk_per_share == 0:
        return 0

    return int(risk_amount / risk_per_share)


# =========================
# BACKTEST
# =========================
def run_backtest():

    print("🚀 STARTING BACKTEST")

    data = load_data()
    data = precompute_indicators(data)

    spy_df = data["SPY"]

    all_dates = sorted(set().union(*[df.index for df in data.values()]))

    capital = START_CAPITAL
    positions = []
    equity_curve = []
    trades = []

    for i in range(200, len(all_dates) - 1):

        date = all_dates[i]
        next_date = all_dates[i + 1]

        still_open = []

        # =========================
        # EXIT LOGIC
        # =========================
        for pos in positions:

            df = data[pos["symbol"]]

            if date not in df.index:
                still_open.append(pos)
                continue

            close = df.loc[date]["Close"]

            pos["highest"] = max(pos["highest"], close)

            profit_atr = (pos["highest"] - pos["entry"]) / pos["atr"]

            if profit_atr < 1:
                new_stop = pos["stop"]
            elif profit_atr < 2:
                new_stop = pos["highest"] - 3 * pos["atr"]
            elif profit_atr < 4:
                new_stop = pos["highest"] - 2 * pos["atr"]
            else:
                new_stop = pos["highest"] - 2.5 * pos["atr"]

            pos["stop"] = max(pos["stop"], new_stop)

            if close <= pos["stop"]:
                exit_price = close * (1 - EXIT_SLIPPAGE)
                pnl = (exit_price - pos["entry"]) * pos["shares"]

                capital += pos["shares"] * exit_price
                trades.append(pnl)
            else:
                still_open.append(pos)

        positions = still_open

        # =========================
        # EQUITY
        # =========================
        equity = capital
        for pos in positions:
            df = data[pos["symbol"]]
            if date in df.index:
                equity += pos["shares"] * df.loc[date]["Close"]

        equity_curve.append(equity)

        # =========================
        # MARKET REGIME
        # =========================
        if date not in spy_df.index:
            continue

        spy_close = spy_df.loc[date]["Close"]
        spy_ma50 = spy_df["Close"].rolling(50).mean().loc[date]
        spy_ma200 = spy_df["Close"].rolling(200).mean().loc[date]

        if pd.isna(spy_ma50) or pd.isna(spy_ma200):
            continue

        if spy_close > spy_ma50 > spy_ma200:
            base_exposure = 1.6
        elif spy_close > spy_ma50:
            base_exposure = 1.1
        else:
            base_exposure = 0.4

        exposure = base_exposure * EXPOSURE_MULT

        # =========================
        # SIGNAL GENERATION
        # =========================
        signals = []

        for symbol, df in data.items():

            if symbol == "SPY" or date not in df.index:
                continue

            idx = df.index.get_loc(date)
            if idx < 200:
                continue

            hist = df.iloc[:idx]

            sig = generate_signal(hist, symbol, spy_df)
            if sig:
                sig["index"] = idx
                signals.append(sig)

        signals.sort(key=lambda x: x["score"], reverse=True)

        open_count = len(positions)

        # =========================
        # ENTRY LOGIC
        # =========================
        for sig in signals[:MAX_NEW]:

            if open_count >= MAX_POSITIONS:
                break

            df = data[sig["symbol"]]
            idx = sig["index"]

            if idx + 1 >= len(df):
                continue

            next_row = df.iloc[idx + 1]
            if next_row.name != next_date:
                continue

            entry = next_row["Open"] * (1 + ENTRY_SLIPPAGE)
            stop = sig["stop"]

            # 🔥 KEEP VOL SCALING (CRITICAL)
            atr_pct = sig["atr"] / entry

            if atr_pct < 0.02:
                vol = 1.2
            elif atr_pct < 0.04:
                vol = 1.0
            else:
                vol = 0.7

            risk = BASE_RISK * exposure * vol

            shares = calc_size(capital, entry, stop, risk)
            cost = shares * entry

            if shares <= 0 or cost > capital:
                continue

            capital -= cost

            positions.append({
                "symbol": sig["symbol"],
                "entry": entry,
                "stop": stop,
                "shares": shares,
                "highest": entry,
                "atr": sig["atr"]
            })

            open_count += 1

    # =========================
    # RESULTS
    # =========================
    final = equity_curve[-1]
    years = len(equity_curve) / 252
    cagr = ((final / START_CAPITAL) ** (1 / years) - 1) * 100

    wins = [t for t in trades if t > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0

    peak = -np.inf
    max_dd = 0

    for x in equity_curve:
        peak = max(peak, x)
        dd = (peak - x) / peak
        max_dd = max(max_dd, dd)

    print("\n===== BACKTEST RESULTS =====")
    print(f"Final Equity: {round(final, 2)}")
    print(f"CAGR: {round(cagr, 2)}%")
    print(f"Trades: {len(trades)}")
    print(f"Win Rate: {round(win_rate, 2)}%")
    print(f"Max Drawdown: {round(max_dd * 100, 2)}%")


if __name__ == "__main__":
    run_backtest()