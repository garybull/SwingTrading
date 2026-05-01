from app.data import get_data
from app.strategy import generate_signal


def scan_universe(symbols):
    results = []

    print(f"Scanning {len(symbols)} symbols...")

    for symbol in symbols:
        try:
            df = get_data(symbol)

            if df is None or len(df) < 50:
                continue

            signal = generate_signal(df, symbol)

            if signal:
                results.append(signal)

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

    # =========================
    # SORT RESULTS BY SCORE
    # =========================
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    print(f"\nScan complete. Evaluated {len(symbols)} stocks.")

    # =========================
    # DEFINE STRONG BY RANK
    # =========================
    TOP_N = 8  # 🔥 adjust if needed

    for i, r in enumerate(results):
        if i < TOP_N:
            r["strong"] = True
        else:
            r["strong"] = False

    # =========================
    # TOP 5 OUTPUT
    # =========================
    top5 = results[:5]

    print("\n=== TOP 5 CANDIDATES ===")
    for r in top5:
        print(r)

    # =========================
    # STRONG SIGNALS OUTPUT
    # =========================
    strong_signals = [r for r in results if r["strong"]]

    print(f"\nStrong signals: {len(strong_signals)}")

    if strong_signals:
        print("\n=== STRONG SIGNALS (TRADE THESE) ===")
        for r in strong_signals:
            print(r)

    return results