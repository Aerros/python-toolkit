r""" README
Purpose: Find records whose effective-date ranges overlap for the same ID (two active contracts, prices, or mappings at once).
Output: Returns a DataFrame of the offending rows, each paired with the next period it runs into. Empty = no overlaps.
Personal Variables: None. Pass the column names in.
Implementation:
    Paste this block into your script.
        bad = find_overlapping_date_ranges(df, id_col="Facility ID",
                            start_col="Facility Effective Date", end_col="Facility Termination Date")
        if not bad.empty:
            ids = ", ".join(bad["Facility ID"].astype(str).unique())
            send_email(EMAIL_TO, "Action Required: date overlap", f"Overlapping IDs: {ids}")
SQL equivalent:
    SELECT *, LEAD(start) OVER (PARTITION BY id ORDER BY start) AS next_start
    ... WHERE ISNULL(end, '2199-12-31') >= next_start
Behavior:
    A blank end date means "still active", so it overlaps ANY later period for that ID.
    touching_is_overlap=True (default): ending 3/31 and the next starting 3/31 is an overlap (both active that day).
    Set it False if your ranges are end-exclusive.
    Rows with a blank START date can't be placed and are returned separately by missing_starts().
    Dates may be in different formats within one column (1/31/2026 and 2026-02-28); each is read on its own.
    An END date that is filled in but can't be read as a date (a typo like "13/45/2026") is treated like a
    blank one - still active - so it will show up as an overlap. That is on purpose: it gets looked at.
"""

import pandas as pd

OPEN_ENDED = pd.Timestamp("2199-12-31")                                         # stands in for "no end date"


def find_overlapping_date_ranges(
    df: pd.DataFrame,
    id_col: str,
    start_col: str,
    end_col: str,
    touching_is_overlap: bool = True,
) -> pd.DataFrame:
    """Rows whose period runs into the next period for the same id."""
    work = df.copy()
    work["_start"] = pd.to_datetime(work[start_col], format="mixed", errors="coerce")  # each value parsed on its own
    work["_end"] = pd.to_datetime(work[end_col], format="mixed", errors="coerce").fillna(OPEN_ENDED)  # ISNULL(end, '2199-12-31')
    work = work.dropna(subset=["_start"]).sort_values([id_col, "_start"])       # ORDER BY id, start
    work["Next Start"] = work.groupby(id_col)["_start"].shift(-1)               # LEAD(start) OVER (PARTITION BY id ...)
    if touching_is_overlap:
        hits = work["_end"] >= work["Next Start"]
    else:
        hits = work["_end"] > work["Next Start"]
    return work.loc[hits].drop(columns=["_start", "_end"])


def missing_starts(df: pd.DataFrame, start_col: str) -> pd.DataFrame:
    """Rows with no usable start date."""
    return df[pd.to_datetime(df[start_col], format="mixed", errors="coerce").isna()]
