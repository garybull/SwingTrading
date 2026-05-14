# app/portfolio_state.py

import sqlite3
import pandas as pd

from app.config import DB_NAME


# =====================================
# UPDATE SYSTEM EQUITY
# =====================================
def refresh_system_state():

    conn = sqlite3.connect(DB_NAME)

    positions = pd.read_sql_query(

        """

        SELECT
            market_value

        FROM positions

        """,

        conn

    )

    total_market_value = 0

    if not positions.empty:

        total_market_value = float(

            positions[
                "market_value"
            ].sum()

        )

    # =====================================
    # GET CASH
    # =====================================
    state = pd.read_sql_query(

        """

        SELECT
            current_cash

        FROM system_state

        WHERE id = 1

        """,

        conn

    )

    if not state.empty:

        cash = float(

            state.iloc[0][
                "current_cash"
            ]

        )

    else:

        cash = 0

    # =====================================
    # TOTAL EQUITY
    # =====================================
    equity = (
        total_market_value
        + cash
    )

    # =====================================
    # UPDATE STATE
    # =====================================
    cur = conn.cursor()

    cur.execute(

        """

        UPDATE system_state

        SET
            current_equity = ?

        WHERE id = 1

        """,

        (equity,)

    )

    conn.commit()

    conn.close()

    return equity