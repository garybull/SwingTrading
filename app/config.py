# app/config.py

import os


# =====================================
# DATABASE
# =====================================
DB_NAME = "trading_system.db"


# =====================================
# PORTFOLIO SETTINGS
# =====================================
START_CAPITAL = 90000

TOP_N = 1

REBALANCE_DAYS = 10

REBALANCE_OFFSET = 0

CASH_RESERVE = 0.15

SLIPPAGE = 0.001


# =====================================
# UNIVERSE
# =====================================
UNIVERSE = [

    "TQQQ",
    "SOXL",
    "TECL",
    "UPRO",
    "USD",
    "QQQ",
    "SPY"

]


# =====================================
# EMAIL
# =====================================
SMTP_SERVER = "smtp.gmail.com"

SMTP_PORT = 587

EMAIL_ADDRESS = "garybull781@gmail.com"

EMAIL_PASSWORD = "qlmyllragbmroswf"


TO_EMAIL = "garybull781@gmail.com"


ENABLE_EMAILS = True

# =====================================
# DASHBOARD
# =====================================
WEB_HOST = "0.0.0.0"

WEB_PORT = 8000


# =====================================
# MARKET DATA
# =====================================
DATA_START_DATE = "2010-01-01"

MIN_HISTORY_DAYS = 200


# =====================================
# SYSTEM FLAGS
# =====================================
ENABLE_EMAILS = True

ENABLE_REBALANCE_LOGGING = True

ENABLE_MARKET_FILTER = True

# =====================================
# EXECUTION MODE
# =====================================
AUTO_EXECUTE = False
SEND_SUMMARY_EMAIL = True