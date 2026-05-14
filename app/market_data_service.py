# app/market_data_service.py

import yfinance as yf
import pandas as pd

from app.logger import logger

from app.config import (
    DATA_START_DATE
)


# =====================================
# DOWNLOAD HISTORICAL DATA
# =====================================
def get_historical_data(

    symbol,

    start=DATA_START_DATE

):

    logger.info(

        f"Fetching historical data "
        f"for {symbol}"

    )

    try:

        df = yf.download(

            symbol,

            start=start,

            auto_adjust=True,

            progress=False,

            threads=False

        )

        if df.empty:

            logger.warning(

                f"No historical data "
                f"for {symbol}"

            )

            return None

        return df

    except Exception as e:

        logger.error(

            f"Historical data failed "
            f"for {symbol}: {e}"

        )

        return None


# =====================================
# GET LIVE PRICE
# =====================================
def get_live_price(symbol):

    logger.info(

        f"Fetching live price "
        f"for {symbol}"

    )

    try:

        ticker = yf.Ticker(symbol)

        hist = ticker.history(

            period="1d",

            interval="1m"

        )

        if hist.empty:

            logger.warning(

                f"No live price for "
                f"{symbol}"

            )

            return 0

        return float(

            hist["Close"].iloc[-1]

        )

    except Exception as e:

        logger.error(

            f"Live price failed "
            f"for {symbol}: {e}"

        )

        return 0


# =====================================
# GET MULTIPLE LIVE PRICES
# =====================================
def get_live_prices(symbols):

    logger.info(
        "Fetching batch live prices..."
    )

    prices = {}

    for symbol in symbols:

        prices[symbol] = (
            get_live_price(symbol)
        )

    return prices