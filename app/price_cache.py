# app/price_cache.py

import time
import yfinance as yf

from app.logger import logger


# =====================================
# GLOBAL CACHE
# =====================================
PRICE_CACHE = {}

LAST_UPDATE = 0

CACHE_SECONDS = 60


# =====================================
# GET LIVE PRICES
# =====================================
def get_live_prices(symbols):

    global PRICE_CACHE
    global LAST_UPDATE

    now = time.time()

    # =====================================
    # USE CACHE
    # =====================================
    if (

        PRICE_CACHE

        and

        (now - LAST_UPDATE)
        < CACHE_SECONDS

    ):

        logger.info(
            "Using cached prices"
        )

        return PRICE_CACHE

    logger.info(
        "Refreshing live prices..."
    )

    try:

        data = yf.download(

            tickers=symbols,

            period="1d",

            interval="1m",

            progress=False,

            auto_adjust=True

        )

        prices = {}

        # =====================================
        # MULTI SYMBOL
        # =====================================
        if len(symbols) > 1:

            for symbol in symbols:

                try:

                    price = float(

                        data["Close"][
                            symbol
                        ]

                        .dropna()

                        .iloc[-1]

                    )

                    prices[symbol] = (
                        price
                    )

                except:

                    logger.warning(

                        f"No price for "
                        f"{symbol}"

                    )

        # =====================================
        # SINGLE SYMBOL
        # =====================================
        else:

            symbol = symbols[0]

            price = float(

                data["Close"]

                .dropna()

                .iloc[-1]

            )

            prices[symbol] = price

        PRICE_CACHE = prices

        LAST_UPDATE = now

        logger.info(
            "Price cache updated"
        )

        return prices

    except Exception as e:

        logger.error(

            f"Price cache failed: {e}"

        )

        return PRICE_CACHE