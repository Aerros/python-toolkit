r""" README
Purpose: Business-day math and "only run on..." checks: skip weekends and US bank holidays, find last Friday,
         the first business day of the month, and the gap in business days between two dates.
Output: Plain date objects, ints and bools.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Paste this block into your script.
    "Only run on Mondays" guard, at the top of main():
        if not runs_today("Monday"):
            logging.info("Not Monday - nothing to do.")
            return 0                                                            # 0 = success, so a parent script doesn't see a crash
    Monthly job:
        if not is_first_business_day_of_month():
            return 0
    Report period:
        week_ending = last_weekday("Friday")                                    # most recent Friday before today
    Deposit / SLA gap:
        gap = business_days_between(last_deposit, previous_business_day())
        if gap >= 3: send_email(...)
Holidays:
    BANK_DAYS = True (default) follows the Federal Reserve / bank calendar:
        the 11 federal holidays; one on a Sunday moves to Monday; one on a SATURDAY is not moved,
        so the Friday before is a normal business day (banks are open Fri 2026-07-03).
    BANK_DAYS = False follows the federal-office calendar instead: Saturday holidays move to Friday.
    Use True for anything about deposits, payments or banks; False for federal-office schedules.
    Holiday dates come from the `holidays` package. If it isn't installed, only weekends are skipped
    and a warning is logged.
Behavior:
    Accepts date, datetime or pandas Timestamp (e.g. straight from a SQL MAX(date) query); the time is ignored.
    business_days_between counts the business days AFTER start, up to and INCLUDING end.
        Fri -> next Mon = 1.  Same day = 0.  end before start = 0.
    Day names are checked: runs_today("Mon") raises ValueError instead of quietly never running.
Why:
    Four scripts had "is it Monday" checks; the XiFin import computed "first weekday of the month" with a nested
    conditional that ignores holidays (a Monday-the-1st that is New Year's Day still ran).
Requires: pip install holidays   (optional, but recommended)
"""

import logging
from datetime import date, datetime, timedelta
from functools import lru_cache

BANK_DAYS = True                                                                #!REPLACE - True: bank calendar; False: federal-office calendar
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _as_date(d: date | datetime) -> date:
    """datetime / Timestamp -> date; date stays date. Comparing a date to a datetime raises TypeError."""
    return d.date() if isinstance(d, datetime) else d                           # Timestamp is a datetime subclass


def _day_index(name: str) -> int:
    """'monday' -> 0 ... 'sunday' -> 6; raises on anything else."""
    try:
        return WEEKDAYS.index(name.strip().capitalize())
    except ValueError:
        raise ValueError(f"Unknown weekday {name!r}; use a full name like 'Monday'") from None


@lru_cache(maxsize=None)                                                        # build each year's calendar once
def _holidays_for(year: int) -> frozenset:
    try:
        import holidays
    except ImportError:
        logging.warning("'holidays' not installed - only weekends will be skipped.")
        return frozenset()
    if not BANK_DAYS:
        return frozenset(holidays.country_holidays("US", years=year).keys())    # federal observed dates
    actual = holidays.country_holidays("US", years=year, observed=False)        # the holidays on their real dates
    days = set(actual.keys())
    days |= {d + timedelta(days=1) for d in actual if d.weekday() == 6}         # Sunday holiday -> Monday off
    return frozenset(days)                                                      # Saturday holiday -> nothing extra


def is_business_day(d: date | datetime) -> bool:
    """True if d is Monday-Friday and not a holiday."""
    d = _as_date(d)
    return d.weekday() < 5 and d not in _holidays_for(d.year)                  # weekday(): Mon=0 ... Sun=6


def previous_business_day(d: date | datetime | None = None) -> date:
    """The last business day strictly before d (default: today)."""
    d = _as_date(d or date.today()) - timedelta(days=1)
    while not is_business_day(d):
        d -= timedelta(days=1)
    return d


def business_days_between(start: date | datetime, end: date | datetime) -> int:
    """Business days after start up to and including end."""
    start, end = _as_date(start), _as_date(end)
    count, d = 0, start
    while d < end:
        d += timedelta(days=1)
        count += is_business_day(d)                                             # True counts as 1, False as 0
    return count


def is_first_business_day_of_month(d: date | datetime | None = None) -> bool:
    """True if d (default today) is the first business day of its month."""
    d = _as_date(d or date.today())
    first = d.replace(day=1)
    while not is_business_day(first):
        first += timedelta(days=1)
    return d == first


def last_weekday(name: str, d: date | datetime | None = None) -> date:
    """Most recent `name` day strictly before d (default today). last_weekday("Friday") on a Monday = 3 days ago."""
    d = _as_date(d or date.today())
    back = (d.weekday() - _day_index(name)) % 7 or 7                            # "or 7": on a Friday, go back a full week
    return d - timedelta(days=back)


def runs_today(*day_names: str, d: date | datetime | None = None) -> bool:
    """True if today is one of the given weekday names. runs_today("Monday", "Thursday")"""
    d = _as_date(d or date.today())
    return d.weekday() in {_day_index(n) for n in day_names}
