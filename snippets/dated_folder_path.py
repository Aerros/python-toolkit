""" README
Purpose: Build a dated folder path like Output\\2026\\09262026 from a date - the write side of find_latest_folder_date.py.
Output: Returns a Path. make=True also creates the folder.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Paste this block into your script.
        folder = dated_folder(OUTPUT_ROOT, file_date, make=True)
        shutil.move(src, folder / final_name)
CRITICAL - keep in sync with find_latest_folder_date.py:
    LEVEL_FORMATS here and FOLDER_PATTERN / DATE_FOLDER_FORMAT there describe the same tree.
        LEVEL_FORMATS = ["%Y", "%m%d%Y"]    <->  FOLDER_PATTERN = "*/*",  DATE_FOLDER_FORMAT = "%m%d%Y"
        LEVEL_FORMATS = ["%Y-%m"]           <->  FOLDER_PATTERN = "*",    DATE_FOLDER_FORMAT = "%Y-%m"
    One * per entry in LEVEL_FORMATS, and the LAST entry equals DATE_FOLDER_FORMAT.
    If they drift apart, the reader silently finds nothing and the next run re-downloads everything.
Examples:
    ["%Y", "%m%d%Y"]  -> Output\\2026\\09262026        (XiFin daily tree)
    ["%Y-%m"]         -> Archive\\2026-09              (NGS monthly staging)
    ["%Y", "%m"]      -> Archive\\2026\\09
"""

from datetime import date, datetime
from pathlib import Path

LEVEL_FORMATS = ["%Y", "%m%d%Y"]                                                #!REPLACE - one strftime format per folder level


def dated_folder(root: Path, when: date | datetime, make: bool = False) -> Path:
    """Return root / <level1> / <level2> ... for the given date."""
    folder = Path(root).joinpath(*(when.strftime(fmt) for fmt in LEVEL_FORMATS))  # root/2026/09262026
    if make:
        folder.mkdir(parents=True, exist_ok=True)                               # creates every missing level
    return folder
