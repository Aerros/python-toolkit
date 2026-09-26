r""" README
Purpose: Run a saved .sql file (a stored refresh, a count, an INSERT...SELECT) from Python.
Output: Returns nothing. Raises if the file is empty or any statement fails; nothing is committed on failure.
Personal Variables: None. Pass the connection and file path in.
Implementation:
    Needs a pyodbc connection (see sql_connect.py).
        with connect() as cnxn:
            run_sql_file(cnxn, Path(r"C:\sql\daily_counts.sql"))
Behavior:
    Splits the file into batches on GO lines, like SSMS. GO is an SSMS command, not T-SQL,
    so sending it to the server raises a syntax error. Recognized forms, any case:
        GO
        GO 5                  runs the batch above it 5 times, as SSMS does
        GO -- any comment
    GO inside a /* block comment */ is still treated as a separator (SSMS does the same).
    All batches run in one transaction: either every batch commits, or none do.
    Encoding is detected: UTF-16 ("Unicode" in SSMS's Save with Encoding), UTF-8 with or without BOM,
    then Windows cp1252.
Why keep SQL in a file?
    You can open, test and edit it in SSMS without touching the Python.
Requires: pip install pyodbc
"""

import re
from pathlib import Path
from typing import Any

GO_LINE = re.compile(r"^\s*GO(?:\s+(?P<count>\d+))?\s*(?:--.*)?$", re.IGNORECASE)   # GO, GO 5, GO -- note


def read_sql_text(sql_path: Path) -> str:
    """Read a .sql file in whatever encoding SSMS saved it."""
    raw = Path(sql_path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):                                   # UTF-16 byte-order mark
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8-sig")                                          # utf-8-sig also drops a UTF-8 BOM
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")                           # older "ANSI" saves


def split_batches(text: str) -> list[str]:
    """Split T-SQL text into batches on GO lines, repeating a batch for GO n."""
    batches: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        match = GO_LINE.match(line)
        if not match:
            current.append(line)
            continue
        batch = "\n".join(current).strip()
        if batch:
            batches.extend([batch] * int(match.group("count") or 1))            # GO 5 -> same batch 5 times
        current = []
    tail = "\n".join(current).strip()                                           # last batch needs no GO after it
    if tail:
        batches.append(tail)
    return batches


def run_sql_file(cnxn: Any, sql_path: Path) -> None:                           # cnxn: a pyodbc connection
    """Execute every batch in a .sql file inside a single transaction."""
    batches = split_batches(read_sql_text(sql_path))
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
