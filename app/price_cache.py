# app/price_cache.py

import time

from app.logger import logger

from app.market_data_service import (
    get_live_price
)


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
    # CACHE HIT
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

    prices = {}

    # =====================================
    # SYMBOL LOOP
    # =====================================
    for symbol in symbols:

        try:

            price = get_live_price(
                symbol
            )

            if price > 0:

                prices[symbol] = (
                    price
                )

            else:

                logger.warning(

                    f"Invalid live price "
                    f"for {symbol}"

                )

        except Exception as e:

            logger.error(

                f"Price fetch failed "
                f"for {symbol}: {e}"

            )

    # =====================================
    # UPDATE CACHE
    # =====================================
    if len(prices) > 0:

        PRICE_CACHE = prices

        LAST_UPDATE = now

        logger.info(
            "Price cache updated"
        )

        return prices

    # =====================================
    # FALLBACK
    # =====================================
    logger.warning(
        "Returning stale cache"
    )

    return PRICE_CACHE