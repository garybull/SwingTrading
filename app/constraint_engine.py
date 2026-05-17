# app/constraint_engine.py

from app.logger import logger

from app.risk_engine import (
    LEVERAGE_MAP
)


# =====================================
# CONSTRAINTS
# =====================================
MAX_EFFECTIVE_EXPOSURE = 300

MAX_SINGLE_POSITION = 0.90

MIN_CASH_RESERVE = 0.05


# =====================================
# VALIDATE PORTFOLIO
# =====================================
def validate_portfolio(

    portfolio_df

):

    logger.info(
        "Validating portfolio constraints..."
    )

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if portfolio_df is None:

        return {

            "valid": False,

            "warnings": [

                "Portfolio is None"

            ],

            "effective_exposure": 0,

            "cash_reserve": 1

        }

    if len(portfolio_df) == 0:

        return {

            "valid": True,

            "warnings": [],

            "effective_exposure": 0,

            "cash_reserve": 1

        }

    warnings = []

    # =====================================
    # TOTAL ALLOCATION
    # =====================================
    total_allocation = float(

        portfolio_df[
            "target_allocation"
        ].sum()

    )

    cash_reserve = (

        1
        - total_allocation

    )

    # =====================================
    # EFFECTIVE EXPOSURE
    # =====================================
    effective_exposure = 0

    for _, row in portfolio_df.iterrows():

        symbol = row["symbol"]

        allocation = float(

            row[
                "target_allocation"
            ]

        )

        leverage = LEVERAGE_MAP.get(
            symbol,
            1
        )

        effective_exposure += (

            allocation
            * leverage

        )

    effective_exposure_pct = (
        effective_exposure * 100
    )

    # =====================================
    # MAX EXPOSURE
    # =====================================
    if (

        effective_exposure_pct

        > MAX_EFFECTIVE_EXPOSURE

    ):

        warnings.append(

            f"Effective exposure "
            f"too high: "
            f"{effective_exposure_pct:.1f}%"

        )

    # =====================================
    # POSITION LIMITS
    # =====================================
    for _, row in portfolio_df.iterrows():

        symbol = row["symbol"]

        allocation = float(

            row[
                "target_allocation"
            ]

        )

        if allocation > MAX_SINGLE_POSITION:

            warnings.append(

                f"{symbol} exceeds "
                f"max position size "
                f"({allocation * 100:.1f}%)"

            )

    # =====================================
    # CASH RESERVE
    # =====================================
    if cash_reserve < MIN_CASH_RESERVE:

        warnings.append(

            f"Cash reserve below "
            f"minimum "
            f"({cash_reserve * 100:.1f}%)"

        )

    # =====================================
    # FINAL STATUS
    # =====================================
    valid = (
        len(warnings) == 0
    )

    if valid:

        logger.info(
            "Portfolio constraints passed"
        )

    else:

        logger.warning(

            "Portfolio constraint "
            "violations detected"

        )

        for w in warnings:

            logger.warning(w)

    return {

        "valid":
            valid,

        "warnings":
            warnings,

        "effective_exposure":

            round(
                effective_exposure_pct,
                2
            ),

        "cash_reserve":

            round(
                cash_reserve * 100,
                2
            )

    }


# =====================================
# APPLY CONSTRAINTS
# =====================================
def apply_constraints(

    portfolio_df

):

    logger.info(
        "Applying portfolio constraints..."
    )

    if (

        portfolio_df is None

        or

        len(portfolio_df) == 0

    ):

        return portfolio_df

    portfolio_df = (
        portfolio_df.copy()
    )

    # =====================================
    # POSITION CAPS
    # =====================================
    portfolio_df[
        "target_allocation"
    ] = portfolio_df[
        "target_allocation"
    ].clip(

        upper=MAX_SINGLE_POSITION

    )

    # =====================================
    # RENORMALIZE
    # =====================================
    total_alloc = float(

        portfolio_df[
            "target_allocation"
        ].sum()

    )

    max_allocatable = (

        1
        - MIN_CASH_RESERVE

    )

    if total_alloc > max_allocatable:

        scale_factor = (

            max_allocatable
            / total_alloc

        )

        portfolio_df[
            "target_allocation"
        ] *= scale_factor

    logger.info(
        "Constraints applied"
    )

    return portfolio_df


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    print(
        "\nConstraint engine ready."
    )