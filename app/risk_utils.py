import yfinance as yf

SECTOR_LIMIT = 4
sector_cache = {}


# =========================
# VOLATILITY SIZING
# =========================
def calculate_risk_position_size(capital, entry, stop, risk_pct):
    risk_amount = capital * risk_pct
    risk_per_share = abs(entry - stop)

    if risk_per_share == 0:
        return 0, 0

    shares = int(risk_amount / risk_per_share)
    value = shares * entry

    return shares, value


# =========================
# SECTOR LOOKUP
# =========================
def get_sector(symbol):
    if symbol in sector_cache:
        return sector_cache[symbol]

    try:
        info = yf.Ticker(symbol).info
        sector = info.get("sector", "Unknown")
    except:
        sector = "Unknown"

    sector_cache[symbol] = sector
    return sector


# =========================
# CORRELATION CONTROL
# =========================
def sector_allocation_ok(symbol, open_positions):
    sector = get_sector(symbol)

    count = 0
    for pos in open_positions:
        if get_sector(pos["symbol"]) == sector:
            count += 1

    return count < SECTOR_LIMIT