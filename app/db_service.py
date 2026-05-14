# app/db_service.py

import sqlite3
import pandas as pd

from app.config import (
    DB_NAME
)

from app.logger import logger


# =====================================
# GET CONNECTION
# =====================================
def get_connection():

    return sqlite3.connect(DB_NAME)


# =====================================
# RUN SELECT QUERY
# =====================================
def query_df(

    sql,

    params=None

):

    logger.info(
        "Running dataframe query..."
    )

    conn = get_connection()

    try:

        df = pd.read_sql_query(

            sql,

            conn,

            params=params

        )

        return df

    finally:

        conn.close()


# =====================================
# EXECUTE WRITE QUERY
# =====================================
def execute(

    sql,

    params=None

):

    logger.info(
        "Executing write query..."
    )

    conn = get_connection()

    cur = conn.cursor()

    try:

        if params:

            cur.execute(
                sql,
                params
            )

        else:

            cur.execute(sql)

        conn.commit()

    finally:

        conn.close()


# =====================================
# EXECUTE MANY
# =====================================
def executemany(

    sql,

    rows

):

    logger.info(
        "Executing batch insert..."
    )

    conn = get_connection()

    cur = conn.cursor()

    try:

        cur.executemany(
            sql,
            rows
        )

        conn.commit()

    finally:

        conn.close()