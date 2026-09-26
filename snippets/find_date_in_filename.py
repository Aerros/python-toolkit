r""" README
Purpose: Pull a date out of a FILE name (claims_202608281430.txt, 09262026-000123.xlsx) and optionally strip it off.
Output: find_date_in_filename() returns a datetime or None. strip_date() returns the name without the date.
Personal Variables: Find "#!REPLACE" comments to locate.
Pairs with:
    find_latest_folder_date.py reads dates from FOLDER names (the read side).
    build_dated_folder_path.py builds dated folder paths (the write side).
Implementation:
    Paste this block into your script.
        find_date_in_filename("claims_202608281430.txt")        -> datetime(2026, 8, 28)
        find_date_in_filename("acc_1234567890_20260828.txt")    -> datetime(2026, 8, 28)
        find_date_in_filename("readme.txt")                     -> None
        strip_date("claims_202608281430.txt")                   -> "claims.txt"
Choosing the pattern:
    DATE_REGEX finds the digits; DATE_FORMAT says what they mean. They must agree.
        YYYYMMDD  (XiFin):  DATE_REGEX = r"\d{8}"   DATE_FORMAT = "%Y%m%d"
        MMDDYYYY  (NGS):    DATE_REGEX = r"\d{8}"   DATE_FORMAT = "%m%d%Y"
        YYYY-MM-DD:         DATE_REGEX = r"\d{4}-\d{2}-\d{2}"   DATE_FORMAT = "%Y-%m-%d"
    Test a pattern at https://regex101.com (choose the Python flavor).
Behavior:
    A date must be a whole run of digits: 8 digits, or 8 digits plus an HHMM time (12 digits).
    Digits inside a longer number (an account number, a 10-digit ID) are never read as a date.
    Every candidate is tried in order, and the first one that is a real date wins;
    candidates that aren't real dates (20261340) are skipped.
    No real date anywhere -> find_date_in_filename returns None, and strip_date returns the name unchanged.
    strip_date removes only the date that find_date_in_filename found, plus one _ - or space before it.
Consistency note:
    find_latest_folder_date.py parses the WHOLE folder name, so "08282026_reprocessed" is ignored there.
    This one SEARCHES inside the name, so "claims_20260828.txt" works. That difference is on purpose:
    folders are ours and named exactly; vendor file names are not.
"""

import re
from datetime import datetime

DATE_REGEX = r"\d{8}"                                                           #!REPLACE - the digits that make up the date
DATE_FORMAT = "%Y%m%d"                                                          #!REPLACE - what those digits mean
TIME_REGEX = r"\d{4}"                                                           # optional HHMM right after the date

_CANDIDATE = re.compile(
    rf"(?<!\d)(?P<date>{DATE_REGEX})(?:{TIME_REGEX})?(?!\d)"                    # (?<!\d) (?!\d): not part of a longer number
)
SEPARATORS = "_- "                                                              # one of these before the date is stripped too


def _first_real_date(name: str) -> tuple[datetime, re.Match] | None:
    """The first candidate in name that parses as a real date, with its match."""
    for match in _CANDIDATE.finditer(name):
        try:
            return datetime.strptime(match.group("date"), DATE_FORMAT), match
        except ValueError:                                                      # looks like a date, isn't one - keep looking
            continue
    return None


def find_date_in_filename(name: str) -> datetime | None:
    """Return the date embedded in name, or None."""
    found = _first_real_date(name)
    return found[0] if found else None


def strip_date(name: str) -> str:
    """Remove the date find_date_in_filename() finds (and one separator before it) from name."""
    found = _first_real_date(name)
    if not found:
        return name
    start, end = found[1].span()
    if start > 0 and name[start - 1] in SEPARATORS:
        start -= 1
    return name[:start] + name[end:]
