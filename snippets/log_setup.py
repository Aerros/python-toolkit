r""" README
Purpose: Reusable logging script.
Output: Writes timestamped logs to both a file and terminal
Personal Variables: Find "#!REPLACE" comments to locate
Implementation:
    Paste this whole block near the top of your script since configure_logging() has to run before any logging call.
    Call configure_logging() as the first line inside main().
    Then use logging.info() instead of print().
    Also available: logging.warning(), logging.error(), and logging.exception() (adds a traceback, use inside except).
    When IMPORTING this file (one shared copy for many scripts), give each script its own log name:
        log_file = configure_logging("xifin_client_type")                      # -> LOG_DIR/xifin_client_type.log
    It returns the log file's path, so you can attach it to a failure email.
Behavior:
    force=True: any logging set up earlier (by an imported library, or a logging call made before this
    function ran) is replaced. Without it, basicConfig silently does nothing and the log file stays empty.
    The log file rotates at 5MB and keeps 30 old copies (myscript.log.1 ... myscript.log.30).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(r"C:\use\your\directory\logs")                                   #!REPLACE - folder for log files
LOG_NAME = "myscript"                                                           #!REPLACE - becomes myscript.log

def configure_logging(log_name: str = LOG_NAME, log_dir: Path = LOG_DIR) -> Path:
    """Write timestamped lines to log_dir/log_name.log and to the screen. Returns the log path."""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{log_name}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,                                       #5MB max log file
                backupCount=30,                                                 #30 files total before oldest removed
                encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,                                                             # replace any logging set up before this
    )
    return log_file