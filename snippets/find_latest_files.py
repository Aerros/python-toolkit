""" README
Purpose: Find the newest file (or newest N files) in a folder that match a name pattern.
Output: latest_file() returns a Path or None; latest_files() returns a list, newest LAST, possibly shorter than n.
Personal Variables: None. Pass the folder and pattern in.
Implementation:
    Paste this block into your script.
        newest = latest_file(DOWNLOADS, "Appeal_Detail*.xlsx")
        if newest is None:
            logging.info("Nothing to import.")
        older, newer = latest_files(SNAPSHOT_DIR, "daily_snapshot_*.xlsx", n=2)   # only if len(...) == 2
Behavior:
    Sorted by LAST MODIFIED time, not creation time. On Windows, copying a file keeps its modified time but
    gives it a new creation time, so "newest by creation" can pick an old file that was just copied in.
    Excel's temporary lock files (~$Report.xlsx) are skipped.
    Folders are skipped even if their name matches.
    A missing folder returns None / [] rather than raising.
Tip:
    If your filenames carry a sortable date (daily_snapshot_2026-09-26.xlsx), sort by name instead:
    set by="name". That can't be fooled by someone opening and re-saving an old file.
"""

from pathlib import Path


def latest_files(folder: Path, pattern: str = "*", n: int = 2, by: str = "modified") -> list[Path]:
    """Return up to n matching files, oldest first, newest last."""
    folder = Path(folder)
    if not folder.exists():
        return []
    files = [
        f for f in folder.glob(pattern)                                         # FROM folder WHERE name LIKE pattern
        if f.is_file() and not f.name.startswith("~$")                          # skip folders and Excel lock files
    ]
    if by == "name":
        files.sort(key=lambda f: f.name)                                        # ORDER BY name
    else:
        files.sort(key=lambda f: f.stat().st_mtime)                             # ORDER BY modified time
    return files[-n:]                                                           # the last n = the newest n


def latest_file(folder: Path, pattern: str = "*", by: str = "modified") -> Path | None:
    """Return the single newest matching file, or None."""
    found = latest_files(folder, pattern, n=1, by=by)
    return found[0] if found else None
