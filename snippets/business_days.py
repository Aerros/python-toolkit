""" README
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
Behavior:
    Holidays come from the `holidays` package (US federal / Federal Reserve observed dates).
    If it isn't installed, holidays are ignored and only weekends are skipped - a warning is logged once.
    business_days_between counts the business days AFTER start, up to and INCLUDING end.
        Fri -> next Mon = 1.  Same day = 0.  end before start = 0.
Why:
    Four scripts had "is it Monday" checks; the XiFin import computed "first weekday of the month" with a nested
    conditional that ignores holidays (a Monday-the-1st that is New Year's Day still ran).
Requires: pip install holidays   (optional, but recommended)
"""

import logging
from datetime import date, timedelta
from functools import lru_cache

HOLIDAY_CALENDAR = "US"                                                         #!REPLACE - e.g. "US" federal; see holidays package for others
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@lru_cache(maxsize=None)                                                        # build each year's calendar once
def _holidays_for(year: int) -> frozenset:
    try:
        import holidays
    except ImportError:
        logging.warning("'holidays' not installed - only weekends will be skipped.")
        return frozenset()
    return frozenset(holidays.country_holidays(HOLIDAY_CALENDAR, years=year).keys())


def is_business_day(d: date) -> bool:
    """True if d is Monday-Friday and not a holiday."""
    return d.weekday() < 5 and d not in _holidays_for(d.year)                  # weekday(): Mon=0 ... Sun=6


def previous_business_day(d: date | None = None) -> date:
    """The last business day strictly before d (default: today)."""
    d = (d or date.today()) - timedelta(days=1)
    while not is_business_day(d):
        d -= timedelta(days=1)
    return d


def business_days_between(start: date, end: date) -> int:
    """Business days after start up to and including end."""
    count, d = 0, start
    while d < end:
        d += timedelta(days=1)
        count += is_business_day(d)                                             # True counts as 1, False as 0
    return count


def is_first_business_day_of_month(d: date | None = None) -> bool:
    """True if d (default today) is the first business day of its month."""
    d = d or date.today()
    first = d.replace(day=1)
    while not is_business_day(first):
        first += timedelta(days=1)
    return d == first


def last_weekday(name: str, d: date | None = None) -> date:
    """Most recent `name` day strictly before d (default today). last_weekday("Friday") on a Monday = 3 days ago."""
    d = d or date.today()
    target = WEEKDAYS.index(name.capitalize())
    back = (d.weekday() - target) % 7 or 7                                      # "or 7": on a Friday, go back a full week
    return d - timedelta(days=back)


def runs_today(*day_names: str, d: date | None = None) -> bool:
    """True if today is one of the given weekday names. runs_today("Monday", "Thursday")"""
    d = d or date.today()
    return WEEKDAYS[d.weekday()] in {n.capitalize() for n in day_names}
