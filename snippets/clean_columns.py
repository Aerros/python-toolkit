""" README
Purpose: Clean messy spreadsheet/CSV columns into values SQL will accept: money, whole numbers, dates, IDs, and text.
Output: Each function takes a pandas column (Series) and returns a cleaned one. clean_frame() does a whole DataFrame.
Personal Variables: None. Pass the column lists when you call clean_frame().
Implementation:
    Paste this block into your script.
        df = clean_frame(
            df,
            money_cols=["Credit Amount", "Debit Amount"],
            date_cols=["Date"],
            int_cols=["NOS", "COUNT"],
            id_cols=["Client ID", "CheckNo"],
        )
    Or one column at a time:
        df["Price"] = clean_money(df["Price"])
What each one fixes:
    clean_money  "$1,234.50" -> 1234.50   "(45.00)" -> -45.00   "N/A" -> NULL     rounded half-up to cents
    clean_int    "12.0" -> 12   "abc" -> NULL                                     nullable Int64, so blanks stay blank
    clean_date   "2026-09-26", "9/26/2026", Excel dates -> date   junk -> NULL    no 00:00:00 tail
    clean_id     1001.0 -> "1001"   " AB12 " -> "AB12"                            keeps leading zeros that are already text
    clean_text   trims spaces; "", "nan", "None", "NaT" -> NULL
    Every function is SQL TRY_CONVERT-style: bad values become NULL, never an error.
Behavior:
    clean_frame runs clean_text on every text column NOT listed elsewhere, and trims header whitespace.
    Column names in the lists that are not in the DataFrame are ignored.
Why:
    Seven scripts each had their own version (clean_money, clean_money_column, round_money, the .0 regex...),
    and they disagreed - one handled (negatives), one rounded half-up, one did neither.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import pandas as pd

NULL_TEXT = {"", "nan", "none", "nat", "null", "<na>"}                          # strings that really mean "empty"


def _to_cents(value) -> Decimal | None:
    """One money value -> Decimal rounded to cents, or None."""
    if pd.isna(value):
        return None
    text = str(value).strip().replace("$", "").replace(",", "")
    if text.startswith("(") and text.endswith(")"):                             # accounting format: (45.00) means -45.00
        text = "-" + text[1:-1]
    try:
        return Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # 2.345 -> 2.35, like a cashier, not a float
    except (InvalidOperation, ValueError):
        return None                                                             # TRY_CONVERT -> NULL


def clean_money(series: pd.Series) -> pd.Series:
    """Currency text -> exact Decimal cents (or None)."""
    return series.map(_to_cents).astype(object)


def clean_int(series: pd.Series) -> pd.Series:
    """Numbers that should be whole -> nullable Int64."""
    nums = pd.to_numeric(series, errors="coerce")                               # TRY_CONVERT(FLOAT, col)
    return nums.round().astype("Int64")                                         # capital I = allows NULLs


def clean_date(series: pd.Series, fmt: str | None = None) -> pd.Series:
    """Any date-like value -> date (no time), junk -> None. Pass fmt (e.g. "%Y%m%d") when the text is compact."""
    parsed = pd.to_datetime(series, format=fmt, errors="coerce")                # TRY_CONVERT(DATETIME, col)
    return parsed.dt.date.astype(object).where(parsed.notna(), None)            # CAST(... AS DATE), NaT -> None


def clean_id(series: pd.Series) -> pd.Series:
    """Identifiers -> trimmed text with Excel's .0 removed."""
    text = series.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    blank = text.str.lower().isin(NULL_TEXT) | series.isna()
    return text.astype(object).where(~blank, None)                              # object dtype keeps None as None (pandas 3 too)


def clean_text(series: pd.Series) -> pd.Series:
    """Trim text; placeholder blanks -> None."""
    text = series.astype(str).str.strip()                                       # LTRIM(RTRIM(col))
    blank = text.str.lower().isin(NULL_TEXT) | series.isna()                    # NULLIF(col, '')
    return text.astype(object).where(~blank, None)


def clean_frame(
    df: pd.DataFrame,
    money_cols: list[str] = (),
    date_cols: list[str] = (),
    int_cols: list[str] = (),
    id_cols: list[str] = (),
) -> pd.DataFrame:
    """Apply the right cleaner to each listed column, and clean_text to the remaining text columns."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]                           # " Date " header -> "Date"
    handled = set()
    for cols, fn in ((money_cols, clean_money), (date_cols, clean_date),
                     (int_cols, clean_int), (id_cols, clean_id)):
        for col in cols:
            if col in df.columns:
                df[col] = fn(df[col])
                handled.add(col)
    for col in df.columns:
        if col not in handled and pd.api.types.is_string_dtype(df[col]):        # text columns only (object or str dtype)
            df[col] = clean_text(df[col])
    return df
