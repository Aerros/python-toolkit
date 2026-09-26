r""" README
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
    clean_money  "$1,234.50" -> 1234.50   "(45.00)" -> -45.00   "N/A", "nan", "inf" -> NULL   rounded half-up to cents
    clean_int    "1,234" -> 1234   "12.0" -> 12   12.5 -> 13   "abc", "inf", "1e20" -> NULL   nullable Int64
    clean_date   "2026-09-26", "9/26/2026" mixed in one column, Excel serials (46291) -> date   junk -> NULL
    clean_id     1001.0 -> "1001"   12345678901234567.0 -> "12345678901234568"   " AB12 " -> "AB12"
    clean_text   trims spaces; "", "nan", "None", "NaT", "null" -> NULL
    Every function is SQL TRY_CONVERT-style: bad values become NULL, never an error.
Behavior:
    clean_frame runs clean_text on every text column NOT listed elsewhere (including text columns with blanks),
    and trims header whitespace. Number and date columns it wasn't told about are left alone.
    Column names in the lists that are not in the DataFrame are ignored.
    The DataFrame you pass in is not modified; clean_frame works on a copy.
    clean_int rounds halves away from zero (12.5 -> 13, -12.5 -> -13), the same way clean_money rounds cents.
CRITICAL - IDs that arrive as numbers have already lost precision:
    A float can only hold about 15-16 digits exactly, so a 17-digit ID read as a number is already wrong
    before clean_id sees it (see the example above: ...567 became ...568).
    Read ID columns as text in the first place: pd.read_excel(path, dtype={"Client ID": str}).
    clean_int has the same limit: it's for counts and quantities, exact up to 9,007,199,254,740,992.
    Anything that is really an identifier belongs in id_cols, not int_cols.
Dates:
    Text dates may be in different formats within one column. Each value is parsed on its own.
    Ambiguous text like 03/04/2026 is read month-first (March 4), US style.
    Excel serial dates are recognized when the cell holds a NUMBER (46291) or short digit text ("46291",
    up to 5 digits): 1 = 1900-01-01, 46291 = 2026-09-26.
    Compact 8-digit text ("20260926", "09262026") is ambiguous, so it becomes NULL unless you say which
    it is: clean_date(col, fmt="%Y%m%d") or fmt="%m%d%Y". With fmt, only that one format is accepted.
Why:
    Seven scripts each had their own version (clean_money, clean_money_column, round_money, the .0 regex...),
    and they disagreed - one handled (negatives), one rounded half-up, one did neither.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import numpy as np
import pandas as pd

NULL_TEXT = {"", "nan", "none", "nat", "null", "<na>"}                          # strings that really mean "empty"
INT64_LIMIT = 2**63                                                             # SQL BIGINT range is -2^63 .. 2^63-1
EXCEL_SERIAL_MAX = 2958465                                                      # Excel's serial number for 9999-12-31
EXCEL_EPOCH = "1899-12-30"                                                      # serial 0 in Excel's calendar
SHORT_DIGITS = r"\d{1,5}(?:\.0+)?"                                              # "46291" or "46291.0" - serial-sized digit text


def is_text_column(series: pd.Series) -> bool:
    """True for a column of strings, even with blanks in it (pandas' own is_string_dtype says False then)."""
    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
        return False                                                            # bool counts as numeric here too
    return pd.api.types.infer_dtype(series, skipna=True) in ("string", "empty")  # skipna: look past NaN/None


def _to_cents(value: object) -> Decimal | None:
    """One money value -> Decimal rounded to cents, or None."""
    if pd.isna(value):
        return None
    text = str(value).strip().replace("$", "").replace(",", "")
    if text.startswith("(") and text.endswith(")"):                             # accounting format: (45.00) means -45.00
        text = "-" + text[1:-1]
    try:
        amount = Decimal(text)
    except (InvalidOperation, ValueError):
        return None                                                             # TRY_CONVERT -> NULL
    if not amount.is_finite():                                                  # "nan", "inf" parse as Decimal but SQL rejects them
        return None
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)             # 2.345 -> 2.35, like a cashier, not a float


def clean_money(series: pd.Series) -> pd.Series:
    """Currency text -> exact Decimal cents (or None)."""
    return pd.Series([_to_cents(v) for v in series], index=series.index, dtype=object)


def clean_int(series: pd.Series) -> pd.Series:
    """Numbers that should be whole -> nullable Int64."""
    if not pd.api.types.is_numeric_dtype(series):
        series = series.astype(str).str.replace(",", "", regex=False).str.strip()   # "1,234" -> "1234"
    nums = pd.to_numeric(series, errors="coerce").astype("float64")             # TRY_CONVERT(FLOAT, col)
    nums = nums.where(nums.abs() < INT64_LIMIT)                                 # inf and out-of-range -> NULL instead of an error
    rounded = np.sign(nums) * np.floor(nums.abs() + 0.5)                        # half away from zero: 12.5 -> 13, -12.5 -> -13
    return rounded.astype("Int64")                                              # capital I = allows NULLs


def clean_date(series: pd.Series, fmt: str | None = None) -> pd.Series:
    """Any date-like value -> date (no time), junk -> None. See "Dates" above for serials and 8-digit text."""
    if pd.api.types.is_datetime64_any_dtype(series):
        parsed = series                                                         # already dates
    elif fmt:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")            # one known format
    else:
        values = series.astype(object)
        nums = pd.to_numeric(values, errors="coerce")                           # NaN for text dates and date objects
        is_number = values.map(lambda v: isinstance(v, (int, float, np.number)) and not isinstance(v, bool))
        is_short = values.astype(str).str.strip().str.fullmatch(SHORT_DIGITS)
        is_serial = nums.between(1, EXCEL_SERIAL_MAX) & (is_number | is_short)
        is_other_number = nums.notna() & ~is_serial                             # 8-digit text, out-of-range numbers -> NULL
        text_dates = pd.to_datetime(
            values.where(~(is_serial | is_other_number)),
            format="mixed", errors="coerce",                                    # each value parsed on its own
        )
        serial_dates = pd.to_datetime(
            nums.where(is_serial), unit="D", origin=EXCEL_EPOCH, errors="coerce"
        )
        parsed = text_dates.where(~is_serial, serial_dates)
    return parsed.dt.date.astype(object).where(parsed.notna(), None)            # CAST(... AS DATE), NaT -> None


def _id_text(value: object) -> str | None:
    """One identifier -> trimmed text, or None."""
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():                         # 1001.0 -> "1001", never "1.001e+03"
        return f"{value:.0f}"
    text = str(value).strip()
    if text.lower() in NULL_TEXT:
        return None
    return text[:-2] if text.endswith(".0") and text[:-2].lstrip("-").isdigit() else text   # "1001.0" -> "1001"


def clean_id(series: pd.Series) -> pd.Series:
    """Identifiers -> trimmed text with Excel's .0 removed."""
    return pd.Series([_id_text(v) for v in series], index=series.index, dtype=object)   # object keeps None as None


def clean_text(series: pd.Series) -> pd.Series:
    """Trim text; placeholder blanks -> None."""
    text = series.astype(str).str.strip()                                       # LTRIM(RTRIM(col))
    blank = text.str.lower().isin(NULL_TEXT) | series.isna()                    # NULLIF(col, '')
    return text.astype(object).where(~blank, None)


def clean_frame(
    df: pd.DataFrame,
    money_cols: list[str] | tuple = (),
    date_cols: list[str] | tuple = (),
    int_cols: list[str] | tuple = (),
    id_cols: list[str] | tuple = (),
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
        if col not in handled and is_text_column(df[col]):
            df[col] = clean_text(df[col])
    return df
