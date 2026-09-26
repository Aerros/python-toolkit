""" README
Purpose: Pull a date out of a FILE name (claims_202608281430.txt, 09262026-000123.xlsx) and optionally strip it off.
Output: date_from_filename() returns a datetime or None. strip_date() returns the name without the date.
Personal Variables: Find "#!REPLACE" comments to locate.
Pairs with:
    find_latest_folder_date.py reads dates from FOLDER names (the read side).
    dated_folder_path.py builds dated folder paths (the write side).
Implementation:
    Paste this block into your script.
        date_from_filename("claims_202608281430.txt")   -> datetime(2026, 8, 28)
        date_from_filename("readme.txt")                -> None
        strip_date("claims_202608281430.txt")           -> "claims.txt"
Choosing the pattern:
    DATE_REGEX finds the digits; DATE_FORMAT says what they mean. They must agree.
        YYYYMMDD  (XiFin):  DATE_REGEX = r"\\d{8}"   DATE_FORMAT = "%Y%m%d"
        MMDDYYYY  (NGS):    DATE_REGEX = r"\\d{8}"   DATE_FORMAT = "%m%d%Y"
        YYYY-MM-DD:         DATE_REGEX = r"\\d{4}-\\d{2}-\\d{2}"   DATE_FORMAT = "%Y-%m-%d"
    Test a pattern at https://regex101.com (choose the Python flavor).
Behavior:
    The FIRST match in the name is used.
    Digits that match the regex but aren't a real date (20261340) return None, not an error.
    OPTIONAL_TIME lets an HHMM tail ride along (202608281430) without breaking the date.
Consistency note:
    find_latest_folder_date.py parses the WHOLE folder name, so "08282026_reprocessed" is ignored there.
    This one SEARCHES inside the name, so "claims_20260828.txt" works. That difference is on purpose:
    folders are ours and named exactly; vendor file names are not.
"""

import re
from datetime import datetime

DATE_REGEX = r"\d{8}"                                                           #!REPLACE - the digits that make up the date
DATE_FORMAT = "%Y%m%d"                                                          #!REPLACE - what those digits mean
OPTIONAL_TIME = r"(?:\d{4})?"                                                   # optional HHMM right after the date

_FIND = re.compile(rf"(?P<date>{DATE_REGEX}){OPTIONAL_TIME}")
_STRIP = re.compile(rf"[_\-\s]?{DATE_REGEX}{OPTIONAL_TIME}")                    # also eats one _ - or space before the date


def date_from_filename(name: str) -> datetime | None:
    """Return the date embedded in name, or None."""
    match = _FIND.search(name)                                                  # search = anywhere in the name
    if not match:
        return None
    try:
        return datetime.strptime(match.group("date"), DATE_FORMAT)
    except ValueError:                                                          # 8 digits, but not a real date
        return None


def strip_date(name: str) -> str:
    """Remove the first date (and its separator) from name."""
    return _STRIP.sub("", name, count=1)
