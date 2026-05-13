# app/logger.py

import logging
from logging.handlers import RotatingFileHandler
import os


# =====================================
# LOG DIRECTORY
# =====================================
LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):

    os.makedirs(LOG_DIR)


# =====================================
# LOGGER SETUP
# =====================================
def setup_logger(

    name="trading_system",

    log_file="logs/system.log",

    level=logging.INFO

):

    formatter = logging.Formatter(

        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"

    )

    handler = RotatingFileHandler(

        log_file,

        maxBytes=5 * 1024 * 1024,  # 5MB

        backupCount=5

    )

    handler.setFormatter(
        formatter
    )

    logger = logging.getLogger(
        name
    )

    logger.setLevel(level)

    # Prevent duplicate handlers
    if not logger.handlers:

        logger.addHandler(
            handler
        )

        # Console logging too
        console = logging.StreamHandler()

        console.setFormatter(
            formatter
        )

        logger.addHandler(
            console
        )

    return logger


# =====================================
# SYSTEM LOGGER
# =====================================
logger = setup_logger()