""" README
Purpose: Retry a call that fails for a known, temporary reason (SQL deadlock, Excel "Call was rejected by callee", a locked file).
Output: Returns whatever the call returns. Re-raises the error if it is not a retryable one, or if every attempt fails.
Personal Variables: None. Pass the error text to watch for when you call it.
Implementation:
    Wrap the call in a lambda so it is not run until retry() is ready:
        retry(lambda: df.to_sql("LSA Rates", engine, if_exists="replace", index=False),
              retry_if="deadlock")
        wb = retry(lambda: excel.Workbooks.Open(path),
                   retry_if="call was rejected by callee", attempts=600, delay=0.1)
Behavior:
    retry_if is matched case-insensitively against the error message.
    Any OTHER error is raised immediately - a typo in a column name should not be retried 5 times.
    Waits `delay` seconds between attempts; with backoff=2 the wait doubles each time.
Why:
    Two scripts had hand-written loops for the same idea (CI Reimbursement deadlocks, Daily Deposit COM rejections).
"""

import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")                                                                # "whatever type the call returns"


def retry(
    call: Callable[[], T],
    retry_if: str,
    attempts: int = 5,
    delay: float = 1.0,
    backoff: float = 1.0,
) -> T:
    """Run call(); if it fails with an error containing retry_if, wait and try again."""
    for attempt in range(1, attempts + 1):
        try:
            return call()                                                       # success leaves the loop right here
        except Exception as exc:
            retryable = retry_if.lower() in str(exc).lower()
            if not retryable or attempt == attempts:                            # wrong kind of error, or out of tries
                raise
            logging.warning(
                "Attempt %s/%s failed (%s). Retrying in %.1fs.",
                attempt, attempts, retry_if, delay,
            )
            time.sleep(delay)
            delay *= backoff
    raise RuntimeError("unreachable")                                           # keeps type checkers happy
