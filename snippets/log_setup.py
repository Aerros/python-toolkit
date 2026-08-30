"""
Purpose: Reusable logging script.
Output: Writes timestamped logs to both a file and terminal
Personal Variables: Find "#!REPLACE" comments to locate
Implementation:
    Paste this whole block near the top of your script since configure_logging() has to run before any logging call.
    Call configure_logging() as the first line inside main().
    Then use logging.info() instead of print().
    Also available: logging.warning(), logging.error(), and logging.exception() (adds a traceback, use inside except).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(r"C:\use\your\directory\logs")                                   #!REPLACE - folder for log files
LOG_NAME = "myscript"                                                           #!REPLACE - becomes myscript.log

def configure_logging() -> None:
    """Write timestamped lines to LOG_DIR/LOG_NAME.log and to the screen."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            RotatingFileHandler(
                LOG_DIR / f"{LOG_NAME}.log",
                maxBytes=5 * 1024 * 1024,                                       #5MB max log file
                backupCount=30,                                                 #30 files total before oldest removed
                encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
