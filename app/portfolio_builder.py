# app/portfolio_builder.py

import pandas as pd
from datetime import datetime

from app.config import (

    TOP_N,
    CASH_RESERVE,
    START_CAPITAL

)

from app.regime_engine import (
    determine_market_regime
)

from app.constraint_engine import (

    validate_portfolio,
    apply_constraints

)

from app.logger import logger

from app.db_service import (

    query_df,
    execute

)


# =====================================
# LOAD RANKINGS
# =====================================
def load_rankings():

    return query_df("""

        SELECT *

        FROM rankings

        ORDER BY rank ASC

    """)


# =====================================
# BUILD TARGET PORTFOLIO
# =====================================
def build_target_portfolio():

    logger.info(
        "Building target portfolio..."
    )

    rankings = load_rankings()

    # =====================================
    # EMPTY SAFETY
    # =====================================
    if rankings.empty:

        logger.warning(
            "No rankings found"
        )

        return pd.DataFrame()

    # =====================================
    # MARKET REGIME
    # =====================================
    regime_data = (
        determine_market_regime()
    )

    regime = regime_data[
        "regime"
    ]

    logger.info(

        f"Market regime: "
        f"{regime}"

    )

    # =====================================
    # RISK OFF
    # =====================================
    if regime != "RISK_ON":

        logger.warning(

            "Risk-off regime detected. "
            "Holding cash."

        )

        return pd.DataFrame()

    # =====================================
    # SELECT TOP N
    # =====================================
    selected = rankings.head(
        TOP_N
    ).copy()

    # =====================================
    # SAFETY
    # =====================================
    if "volatility" not in selected.columns:

        logger.error(
            "Missing volatility column"
        )

        return pd.DataFrame()

    # =====================================
    # REMOVE INVALID VOLATILITY
    # =====================================
    selected = selected[

        selected["volatility"] > 0

    ]

    if selected.empty:

        logger.warning(
            "No valid volatility data"
        )

        return pd.DataFrame()

    # =====================================
    # VOLATILITY WEIGHTING
    # MATCH BACKTEST LOGIC
    # =====================================
    selected[
        "inverse_volatility"
    ] = (

        1 / selected[
            "volatility"
        ]

    )

    total_inverse_vol = float(

        selected[
            "inverse_volatility"
        ].sum()

    )

    # =====================================
    # SAFETY
    # =====================================
    if total_inverse_vol <= 0:

        logger.warning(
            "Invalid volatility values"
        )

        return pd.DataFrame()

    # =====================================
    # WEIGHTS
    # =====================================
    selected[
        "weight"
    ] = (

        selected[
            "inverse_volatility"
        ]

        / total_inverse_vol

    )

    # =====================================
    # TARGET ALLOCATION
    # MATCH BACKTEST
    # =====================================
    selected[
        "target_allocation"
    ] = (

        selected["weight"]

        * (1 - CASH_RESERVE)

    )

    # =====================================
    # ACTION LABEL
    # =====================================
    selected[
        "action"
    ] = "BUY"

    # =====================================
    # TARGET VALUE
    # =====================================
    selected[
        "target_value"
    ] = (

        START_CAPITAL

        * selected[
            "target_allocation"
        ]

    )

    # =====================================
    # CURRENT PRICE
    # =====================================
    selected[
        "current_price"
    ] = selected[
        "close"
    ]

    # =====================================
    # SHARE COUNT
    # =====================================
    selected[
        "recommended_shares"
    ] = (

        selected[
            "target_value"
        ]

        / selected[
            "current_price"
        ]

    ).astype(int)

    # =====================================
    # APPLY CONSTRAINTS
    # =====================================
    selected = (
        apply_constraints(
            selected
        )
    )

    # =====================================
    # VALIDATE PORTFOLIO
    # =====================================
    validation = (
        validate_portfolio(
            selected
        )
    )

    if not validation["valid"]:

        logger.warning(

            "Portfolio constraint "
            "violations detected"

        )

        for w in validation[
            "warnings"
        ]:

            logger.warning(w)

    else:

        logger.info(
            "Portfolio constraints passed"
        )

    logger.info(

        f"Effective Exposure: "
        f"{validation['effective_exposure']}%"

    )

    logger.info(

        f"Cash Reserve: "
        f"{validation['cash_reserve']}%"

    )

    logger.info(

        f"Built target portfolio "
        f"with {len(selected)} assets"

    )

    logger.info(

        f"Total target allocation: "
        f"{round(selected['target_allocation'].sum() * 100, 2)}%"

    )

    return selected


# =====================================
# SAVE RECOMMENDED PORTFOLIO
# =====================================
def save_recommended_portfolio(

    portfolio_df

):

    logger.info(
        "Saving recommended portfolio..."
    )

    if portfolio_df.empty:

        logger.warning(
            "No portfolio to save"
        )

        return

    # =====================================
    # CLEAR OLD RECOMMENDATIONS
    # =====================================
    execute("""

        DELETE FROM recommended_portfolio

    """)

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # =====================================
    # INSERT NEW RECOMMENDATIONS
    # =====================================
    for _, row in portfolio_df.iterrows():

        execute("""

            INSERT INTO recommended_portfolio (

                date,
                symbol,
                target_allocation,
                score,
                action,
                current_price,
                target_value,
                recommended_shares

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            today,

            row["symbol"],

            float(
                row[
                    "target_allocation"
                ]
            ),

            float(
                row["score"]
            ),

            row["action"],

            float(
                row["current_price"]
            ),

            float(
                row["target_value"]
            ),

            int(
                row["recommended_shares"]
            )

        ))

    logger.info(
        "Recommended portfolio saved"
    )


# =====================================
# LOAD RECOMMENDED PORTFOLIO
# =====================================
def load_recommended_portfolio():

    return query_df("""

        SELECT *

        FROM recommended_portfolio

        ORDER BY score DESC

    """)


# =====================================
# RUN FULL PORTFOLIO PIPELINE
# =====================================
def run_portfolio_builder():

    portfolio_df = (
        build_target_portfolio()
    )

    if portfolio_df.empty:

        return portfolio_df

    save_recommended_portfolio(
        portfolio_df
    )

    return portfolio_df


# =====================================
# RUN
# =====================================
if __name__ == "__main__":

    run_portfolio_builder()