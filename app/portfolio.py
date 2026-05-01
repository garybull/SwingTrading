def calculate_position_size(entry, stop, account_size=90000, risk_pct=0.01, max_alloc_pct=0.25):
    risk_amount = account_size * risk_pct
    max_position_value = account_size * max_alloc_pct

    risk_per_share = entry - stop

    if risk_per_share <= 0:
        return 0

    # Risk-based shares
    shares_by_risk = risk_amount / risk_per_share

    # Capital cap shares
    shares_by_cap = max_position_value / entry

    # Take the smaller of the two
    shares = min(shares_by_risk, shares_by_cap)

    return int(shares)