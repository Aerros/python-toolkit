""" README
Purpose: Find the newest MMDDYYYY-named folder under a directory tree.
Output: Returns a datetime, or None if no valid date folders were found.
Personal Variables: Find "#!REPLACE" comments to locate.
Use case:
    Deriving "where did I leave off" from the filesystem instead of storing a cursor in a file.
    A failed run leaves nothing stale behind to clean up.

CRITICAL - root and FOLDER_PATTERN must agree:
    Count the levels from root down to the dated folder, and use one * per level.
    Get this wrong and the function silently returns None. It will not error.
    Only the LAST folder name is read as a date; levels above it can be named anything.

    root = ...\Output          FOLDER_PATTERN = "*/*"       (2 levels down)
        Output\
            2026\                       <- anything
                08282026\               <- parsed as a date  MATCH
                08292026\               <- parsed as a date  MATCH

    root = ...\Output          FOLDER_PATTERN = "*"         (1 level down)
        Output\
            08282026\                   <- parsed as a date  MATCH
            08292026\                   <- parsed as a date  MATCH

    root = ...\Output\2026     FOLDER_PATTERN = "*"         (1 level down)
        Output\2026\
            08282026\                   <- parsed as a date  MATCH
        NOTE: pointing root at the year folder means ONE level remains,
        so the pattern is "*", not "*/*".

    root = ...\Output          FOLDER_PATTERN = "*/*/*"     (3 levels down)
        Output\
            2026\
                Q3\                     <- anything
                    08282026\           <- parsed as a date  MATCH

Behavior:
    Folders that are not valid dates are ignored, not errors.
    A missing or empty root returns None rather than raising.
    Files at any level are ignored.
"""

from datetime import datetime
from pathlib import Path

DATE_FOLDER_FORMAT = "%m%d%Y"                                                   #!REPLACE - "%Y%m%d" if folders are YYYYMMDD
FOLDER_PATTERN = "*/*"                                                          #!REPLACE - one * per level between root and the dated folder


def parse_folder_date(name: str) -> datetime | None:                            # like SQL TRY_CONVERT: returns a value or None, never raises
    """Convert a folder name to a datetime, or None if it is not a date."""
    try:
        return datetime.strptime(name, DATE_FOLDER_FORMAT)                      # strptime rejects "notes" and "13322026" alike
    except ValueError:
        return None


def find_latest_folder_date(root: Path) -> datetime | None:                     # root is passed in so one copy serves every script
    """Return the newest dated folder under root, or None if there are none."""
    if not root.exists():                                                       # guard: no folder means nothing to search
        return None
    dates = [
        parse_folder_date(folder.name)                                          # SELECT
        for folder in root.glob(FOLDER_PATTERN)                                 # FROM - glob walks the levels for us
        if folder.is_dir() and parse_folder_date(folder.name)                   # WHERE - skip files and non-dates
    ]
    return max(dates, default=None)                                             # MAX() - default=None covers the empty case
