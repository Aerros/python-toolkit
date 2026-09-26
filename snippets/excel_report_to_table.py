r""" README
Purpose: Turn a "report-shaped" Excel sheet (title rows on top, a blank first column, a summary block at the bottom)
         into a clean table: the real header row as column names, only the data rows underneath.
Output: Returns a DataFrame.
Personal Variables: None. Pass the header cell text and stop text in.
Implementation:
    Paste this block into your script.
        df = excel_report_to_table(
            path, sheet="Appeal Detail",
            header_cell="Accession",                                            # the EXACT text of one header cell
            stop_at="payment and appeal success rate:",                         # first row of the summary block (optional)
        )
Behavior:
    Finds the header row as the first row with a cell whose whole text equals header_cell
    (trimmed, any case), instead of counting rows. So an extra title line added by the vendor next
    month doesn't shift everything by one, and a title like "Appeal Detail - by Accession" is
    not mistaken for the header.
    Columns that are entirely empty (the blank column A) are dropped.
    stop_at is matched case-insensitively ANYWHERE in a row; that row and everything below it are dropped.
    Fully blank rows are dropped. Header names are trimmed and cut to 128 characters (SQL Server's limit);
    a blank header cell becomes Column_<n>.
    Raises ValueError if no cell equals header_cell, rather than loading garbage.
Why:
    Appeal_Detail sliced iloc[1:, 1:] and Financial Assistance used skiprows=2 - both break if the layout moves one cell.
Requires: pip install pandas openpyxl
"""

from pathlib import Path

import pandas as pd


def _cells_lower(df: pd.DataFrame) -> pd.DataFrame:
    """Every cell as trimmed lower-case text ("" for blanks)."""
    return df.apply(lambda col: col.map(lambda v: "" if pd.isna(v) else str(v).strip().lower()))


def excel_report_to_table(
    path: Path,
    sheet: str | int = 0,
    *,                                                                          # everything after this must be named
    header_cell: str,
    stop_at: str | None = None,
) -> pd.DataFrame:
    """Read a formatted report sheet and return just the data table."""
    raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object)      # header=None: read every row as data
    raw = raw.dropna(axis=1, how="all")                                         # drop fully empty columns (blank column A)
    cells = _cells_lower(raw)

    header_hits = (cells == header_cell.strip().lower()).any(axis=1)            # a cell that IS the header text
    if not header_hits.any():
        raise ValueError(f"No cell equal to '{header_cell}' found in {Path(path).name} (sheet {sheet!r})")
    header_pos = raw.index.get_loc(header_hits.idxmax())                        # first matching row

    names = []
    for n, value in enumerate(raw.iloc[header_pos], start=1):
        name = "" if pd.isna(value) else str(value).strip()[:128]
        names.append(name or f"Column_{n}")                                     # blank header cell -> Column_3
    table = raw.iloc[header_pos + 1:].copy()
    table.columns = names                                                       # promote the header row

    if stop_at:
        below = cells.iloc[header_pos + 1:]
        stop_hits = below.apply(lambda col: col.str.contains(stop_at.lower(), regex=False)).any(axis=1)
        if stop_hits.any():
            table = table.iloc[: below.index.get_loc(stop_hits.idxmax())]       # keep rows above the summary

    table = table.dropna(axis=0, how="all")                                     # drop blank spacer rows
    return table.reset_index(drop=True)
