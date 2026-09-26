""" README
Purpose: Turn a "report-shaped" Excel sheet (title rows on top, a blank first column, a summary block at the bottom)
         into a clean table: the real header row as column names, only the data rows underneath.
Output: Returns a DataFrame.
Personal Variables: None. Pass the header text and stop text in.
Implementation:
    Paste this block into your script.
        df = report_sheet_to_table(
            path, sheet="Appeal Detail",
            header_contains="Accession",                                        # any text that appears in the real header row
            stop_at="payment and appeal success rate:",                         # first row of the summary block (optional)
        )
Behavior:
    Finds the header row by searching for header_contains, instead of counting rows - so an extra title
    line added by the vendor next month doesn't shift everything by one.
    Columns that are entirely empty (the blank column A) are dropped.
    stop_at is matched case-insensitively anywhere in a row; that row and everything below it are dropped.
    Fully blank rows are dropped. Header names are trimmed and cut to 128 characters (SQL Server's limit).
    Raises ValueError if the header row can't be found, rather than loading garbage.
Why:
    Appeal_Detail sliced iloc[1:, 1:] and Financial Assistance used skiprows=2 - both break if the layout moves one cell.
Requires: pip install pandas openpyxl
"""

from pathlib import Path

import pandas as pd


def _row_contains(df: pd.DataFrame, text: str) -> pd.Series:
    """True for each row where any cell contains text (case-insensitive)."""
    lowered = df.astype(str).apply(lambda col: col.str.lower())
    return lowered.apply(lambda col: col.str.contains(text.lower(), regex=False)).any(axis=1)


def report_sheet_to_table(
    path: Path,
    sheet: str | int = 0,
    *,                                                                          # everything after this must be named
    header_contains: str,
    stop_at: str | None = None,
) -> pd.DataFrame:
    """Read a formatted report sheet and return just the data table."""
    raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object)      # header=None: read every row as data
    raw = raw.dropna(axis=1, how="all")                                         # drop fully empty columns (blank column A)

    header_hits = _row_contains(raw, header_contains)
    if not header_hits.any():
        raise ValueError(f"Header row containing '{header_contains}' not found in {Path(path).name}")
    header_pos = raw.index.get_loc(header_hits.idxmax())                        # first matching row

    table = raw.iloc[header_pos + 1:].copy()
    table.columns = [str(c).strip()[:128] for c in raw.iloc[header_pos]]        # promote the header row

    if stop_at:
        stop_hits = _row_contains(table, stop_at)
        if stop_hits.any():
            table = table.iloc[: table.index.get_loc(stop_hits.idxmax())]       # keep rows above the summary

    table = table.dropna(axis=0, how="all")                                     # drop blank spacer rows
    return table.reset_index(drop=True)
