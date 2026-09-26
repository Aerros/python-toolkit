""" README
Purpose: The starting shape for every unattended script: logging first, one main(), one safety net, a real exit code.
Output: Exit code 0 on success, 1 on failure - so Task Scheduler and parent scripts (run_scripts.py) can tell.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Copy this file, rename it, and fill in main().
    Paste the snippets you need (log_setup, outlook_email, sql_connect...) into the marked section,
    or keep them in a snippets/ folder next to the script and import them.
The shape, and why each piece is there:
    configure_logging() first    - anything that goes wrong after this line is recorded.
    main() -> int                - one entry point; returns 0 or 1 instead of scattering sys.exit() calls.
    try / except Exception       - the safety net: any error not handled inside a step lands here WITH its traceback,
                                   and triggers the failure email. Without it the job dies silently at 3 a.m.
    finally                      - the "Run finished" line is written whether the run worked or not.
    sys.exit(main())             - hands the exit code to Windows. Task Scheduler's "Last Run Result" shows it.
    if __name__ == "__main__"    - importing this file (to reuse a function) won't start the job.
Replaces:
    The critical_error_occurred flag + close/re-open log file + send_log_file_on_error dance in eight scripts.
"""

import logging
import sys
from datetime import datetime

JOB_NAME = "My Scheduled Job"                                                   #!REPLACE - shows up in the failure email subject

# --------------------------------------------------------------------------- #
# Paste snippets here: configure_logging, send_email, send_failure_alert ...  #
# --------------------------------------------------------------------------- #


def main() -> int:
    configure_logging()                                                         # from log_setup.py
    started = datetime.now()
    logging.info("=" * 60)
    logging.info("%s started", JOB_NAME)
    try:
        # ------------------------------------------------------------------ #
        # The actual work. Raise (or let errors raise) to signal failure.    #
        # Return 0 early for "nothing to do today" - that is not a failure.  #
        # ------------------------------------------------------------------ #
        ...                                                                     #!REPLACE - your steps
        return 0
    except Exception:
        logging.exception("%s failed", JOB_NAME)                                # .exception = error + full traceback
        send_failure_alert(JOB_NAME, log_file=LOG_DIR / f"{LOG_NAME}.log")      # from outlook_email.py; never raises
        return 1
    finally:
        logging.info("%s finished in %s", JOB_NAME, datetime.now() - started)


if __name__ == "__main__":
    sys.exit(main())
