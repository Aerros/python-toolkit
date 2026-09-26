""" README
Purpose: Run a saved .sql file (a stored refresh, a count, an INSERT...SELECT) from Python.
Output: Returns nothing. Raises if the file is empty or any statement fails; nothing is committed on failure.
Personal Variables: None. Pass the connection and file path in.
Implementation:
    Needs a pyodbc connection (see sql_connect.py).
        with connect() as cnxn:
            run_sql_file(cnxn, Path(r"C:\\sql\\daily_counts.sql"))
Behavior:
    Splits the file on lines that contain only GO, the same way SSMS does. GO is an SSMS
    command, not T-SQL, so sending it to the server raises a syntax error.
    All batches run in one transaction: either every batch commits, or none do.
    Keep the .sql file in UTF-8 (SSMS "Save with Encoding" -> UTF-8).
Why keep SQL in a file?
    You can open, test and edit it in SSMS without touching the Python.
Requires: pip install pyodbc
"""

import re
from pathlib import Path

GO_LINE = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)               # a line that is only "GO" (any case)


def run_sql_file(cnxn, sql_path: Path) -> None:
    """Execute every batch in a .sql file inside a single transaction."""
    text = sql_path.read_text(encoding="utf-8-sig")                             # utf-8-sig drops the BOM SSMS sometimes adds
    batches = [b.strip() for b in GO_LINE.split(text) if b.strip()]             # split on GO, drop blank pieces
    if not batches:
        raise ValueError(f"SQL file is empty: {sql_path}")

    cursor = cnxn.cursor()
    try:
        for batch in batches:
            cursor.execute(batch)
            while cursor.nextset():                                             # drain extra result sets, or later batches can fail
                pass
        cnxn.commit()
    except Exception:
        cnxn.rollback()
        raise
    finally:
        cursor.close()
