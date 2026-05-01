def calculate_position_size(account_size, entry, stop, atr):
    # Base risk per trade (1%)
    base_risk_pct = 0.01
    risk_dollars = account_size * base_risk_pct

    risk_per_share = entry - stop

    if risk_per_share <= 0:
        return 0, 0

    # Base shares
    shares = risk_dollars / risk_per_share

    # =========================
    # VOLATILITY ADJUSTMENT
    # =========================
    # Lower ATR = larger size
    # Higher ATR = smaller size

    volatility_factor = 1 / (atr / entry)

    # Normalize (prevents crazy sizing)
    volatility_factor = max(0.5, min(volatility_factor, 1.5))

    shares *= volatility_factor

    shares = int(shares)

    position_value = shares * entry

    return shares, round(position_value, 2)