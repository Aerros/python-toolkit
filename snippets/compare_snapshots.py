r""" README
Purpose: Compare two versions of the same table (yesterday's snapshot vs today's) and return what was added, removed, or changed.
Output: Each function returns a DataFrame. Empty DataFrame = nothing to report.
Personal Variables: None. Pass the key column(s) and the columns to watch.
Implementation:
    Paste this block into your script. Pair it with find_latest_files.py to get the two files:
        save_snapshot(read_sql(QUERY), SNAPSHOT_DIR, "xifin_client_type")      # today's copy
        files = latest_files(SNAPSHOT_DIR, "xifin_client_type_*.xlsx", n=2, by="name")
        if len(files) < 2:
            return 0                                                            # first run: nothing to compare yet
        older, newer = files
        old, new = pd.read_excel(older), pd.read_excel(newer)

        added   = added_rows(old, new, key="client_id")                               # new hospitals
        removed = removed_rows(old, new, key="order_code")                            # missing distribution details
        changed = changed_rows(old, new, key="EntryDate", watch=["Charges", "Volume"])  # counts that moved

        if not changed.empty:
            changed.to_excel(CHANGES_DIR / f"changes_{today}.xlsx", index=False)
            send_email(...)
SQL equivalents:
    added_rows    ->  SELECT n.* FROM new n LEFT JOIN old o ON o.key = n.key WHERE o.key IS NULL
    removed_rows  ->  SELECT o.* FROM old o LEFT JOIN new n ON n.key = o.key WHERE n.key IS NULL
    changed_rows  ->  SELECT ... FROM old o JOIN new n ON n.key = o.key WHERE o.col <> n.col OR ...
Behavior:
    Keys are compared as trimmed, upper-case TEXT, so 1001 (number) matches "1001" (text) and "ab1 " matches "AB1".
    Excel round-trips often turn IDs into numbers; this is what the astype(str) lines in the originals were fixing.
    changed_rows returns columns <col>_old and <col>_new side by side, plus the key.
    Two blanks (NaN and NaN) in a WATCHED column count as equal, not as a change.
    Rows with a blank KEY are left out of every result - a blank key can't be matched to anything.
    Keys should be unique. If one key appears on several rows, changed_rows pairs every old copy with every new copy.
"""

from datetime import date
from pathlib import Path

import pandas as pd


def save_snapshot(df: pd.DataFrame, folder: Path, prefix: str) -> Path:
    """Save df as folder/prefix_YYYY-MM-DD.xlsx (today) and return the path. Re-running the same day overwrites."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{prefix}_{date.today():%Y-%m-%d}.xlsx"                    # ISO date: sorts correctly by name
    df.to_excel(path, index=False)
    return path


def _norm(series: pd.Series) -> pd.Series:
    """Make keys comparable: text, trimmed, upper-case, no trailing .0."""
    return (
        series.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\.0$", "", regex=True)                                   # 1001.0 (float from Excel) -> 1001
    )


BLANK_KEYS = {"", "NAN", "NONE", "<NA>", "NAT"}                                 # how an empty cell looks after _norm


def _with_keys(df: pd.DataFrame, key: str | list[str]) -> tuple[pd.DataFrame, list[str]]:
    keys = [key] if isinstance(key, str) else list(key)                         # accept one key or a composite key
    out = df.copy()
    blank = pd.Series(False, index=out.index)
    for k in keys:
        blank |= out[k].isna()
        out[k] = _norm(out[k])
        blank |= out[k].isin(BLANK_KEYS)
    return out.loc[~blank], keys                                                # WHERE key IS NOT NULL - can't match a blank key


def added_rows(old: pd.DataFrame, new: pd.DataFrame, key: str | list[str]) -> pd.DataFrame:
    """Rows in new whose key is not in old."""
    old, keys = _with_keys(old, key)
    new, _ = _with_keys(new, key)
    merged = new.merge(old[keys].drop_duplicates(), on=keys, how="left", indicator=True)
    return merged[merged["_merge"] == "left_only"].drop(columns="_merge")       # WHERE old.key IS NULL


def removed_rows(old: pd.DataFrame, new: pd.DataFrame, key: str | list[str]) -> pd.DataFrame:
    """Rows in old whose key is no longer in new."""
    return added_rows(new, old, key)                                            # same anti-join, sides swapped


def changed_rows(
    old: pd.DataFrame,
    new: pd.DataFrame,
    key: str | list[str],
    watch: list[str],
) -> pd.DataFrame:
    """Rows present in both whose watched columns differ."""
    old, keys = _with_keys(old, key)
    new, _ = _with_keys(new, key)
    merged = old[keys + watch].merge(
        new[keys + watch], on=keys, how="inner", suffixes=("_old", "_new")      # INNER JOIN on key
    )
    differs = pd.Series(False, index=merged.index)
    for col in watch:
        a, b = merged[f"{col}_old"], merged[f"{col}_new"]
        both_blank = a.isna() & b.isna()                                        # NULL vs NULL is not a change
        not_equal = (a != b).fillna(True).astype(bool)                          # NULL vs value IS a change (Int64 gives NA here)
        differs |= not_equal & ~both_blank                                      # OR together: any watched column moved
    ordered = keys + [c for col in watch for c in (f"{col}_old", f"{col}_new")]
    return merged.loc[differs, ordered]
