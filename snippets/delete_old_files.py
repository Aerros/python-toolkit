r""" README
Purpose: Keep only the newest N files in a folder and delete the rest (old logs, old snapshots, old exports).
Output: Returns the files actually deleted - or, in a dry run, the files that WOULD be deleted.
        Files that couldn't be deleted are logged as warnings and left out of the list.
Personal Variables: None. Pass the folder, pattern and count in.
Implementation:
    Paste this block into your script and call it at the END of a successful run.
    First run - preview only (the default):
        delete_old_files(SNAPSHOT_DIR, "XiFin_Dist_Details_*.xlsx", keep=2)   # logs "Would delete: ..."
    Once the log shows the right files, turn deleting on:
        delete_old_files(SNAPSHOT_DIR, "XiFin_Dist_Details_*.xlsx", keep=2, dry_run=False)
CRITICAL - the pattern is the only thing standing between this and the wrong files:
    ALWAYS pass a specific pattern. "*" in a shared folder deletes other people's files.
    Deleted files skip the Recycle Bin. There is no undo.
Behavior:
    dry_run defaults to True: nothing is deleted until you pass dry_run=False.
    Newest is decided by last modified time.
    A file that can't be deleted (open in Excel, no permission) is logged and skipped, not fatal.
    keep less than 1 raises ValueError rather than emptying the folder.
Note:
    If you use log_setup.py, RotatingFileHandler already caps log files; you don't need this for those.
"""

import logging
from pathlib import Path


def delete_old_files(folder: Path, pattern: str, keep: int, dry_run: bool = True) -> list[Path]:
    """Delete all but the `keep` newest files matching pattern in folder. Previews unless dry_run=False."""
    if keep < 1:
        raise ValueError("keep must be at least 1")                             # guard against wiping the folder
    files = sorted(
        (f for f in Path(folder).glob(pattern) if f.is_file()),
        key=lambda f: f.stat().st_mtime,
        reverse=True,                                                           # newest first
    )
    old = files[keep:]                                                          # everything after the first `keep`
    if dry_run:
        for f in old:
            logging.info("Would delete: %s", f)
        return old
    deleted: list[Path] = []
    for f in old:
        try:
            f.unlink()
            deleted.append(f)                                                   # only counted once it's really gone
            logging.info("Deleted old file: %s", f.name)
        except OSError as exc:
            logging.warning("Could not delete %s: %s", f.name, exc)
    return deleted
