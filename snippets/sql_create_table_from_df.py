r""" README
Purpose: Write a DataFrame to SQL Server with real column types (DATE, DECIMAL(18,2), NVARCHAR) instead of pandas' guesses.
Output: Returns the number of rows written. Raises on failure.
Personal Variables: None. Pass the column lists in.
Implementation:
    Needs a SQLAlchemy engine (see sql_connect.py make_engine()).
        rows = sql_create_table_from_df(
            df, "Client_Pricing", engine,
            date_cols=["Effective", "Initiated"],
            money_cols=["Price", "Total Price"],
        )
    Clean the values first (see clean_columns.py) - this sets the SQL TYPE, it does not fix bad data.
    In particular, Excel serial dates (46291) need clean_date() first; here they would become NULL.
CRITICAL - "replace" means DROP TABLE:
    if_exists="replace" (default) drops and recreates the table every run. Any keys, indexes, permissions
    or column types you set in SSMS are gone after the first run. Good for "mirror this spreadsheet" tables
    nobody else designs; for a table you built by hand, use sql_insert_into_existing_table.py with replace=True instead.
Behavior:
    if_exists="append" adds rows to the existing table; types only apply when the table is first created.
    Text columns not listed in date_cols / money_cols become NVARCHAR(MAX); numeric columns keep pandas' INT/FLOAT.
    Your DataFrame is not modified; the function works on a copy.
    A column name in the lists that is not in the DataFrame is ignored.
Why:
    Without dtype=, pandas creates FLOAT for money (0.1 + 0.2 = 0.30000000000000004) and DATETIME for dates,
    and TEXT for strings. Five scripts built this mapping by hand.
Requires: pip install pandas sqlalchemy pyodbc
"""

import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.types import NVARCHAR, Date, Numeric


def _is_text_column(series: pd.Series) -> bool:
    """True for a column of strings, even with blanks in it (pandas' own is_string_dtype says False then)."""
    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
        return False
    return pd.api.types.infer_dtype(series, skipna=True) in ("string", "empty")  # skipna: look past NaN/None


def sql_create_table_from_df(
    df: pd.DataFrame,
    table: str,
    engine: Engine,
    date_cols: list[str] | tuple = (),
    money_cols: list[str] | tuple = (),
    schema: str = "dbo",
    if_exists: str = "replace",
) -> int:
    """Write df to schema.table with DATE, DECIMAL(18,2) and NVARCHAR(MAX) columns."""
    df = df.copy()                                                              # don't change the caller's DataFrame
    text_cols = [c for c in df.columns if _is_text_column(df[c])]               # only text columns; numbers keep INT/FLOAT
    dtype = {col: NVARCHAR(None) for col in text_cols}                          # NVARCHAR(MAX) instead of TEXT
    dtype.update({col: Date() for col in date_cols if col in df.columns})       # DATE - no 00:00:00 tail
    dtype.update({col: Numeric(18, 2) for col in money_cols if col in df.columns})  # DECIMAL(18,2) - exact cents

    for col in date_cols:
        if col in df.columns:
            values = df[col]
            if not pd.api.types.is_datetime64_any_dtype(values):
                is_number = pd.to_numeric(values, errors="coerce").notna()      # bare numbers would parse as 1970-01-01
                values = values.astype(object).where(~is_number, None)
            parsed = pd.to_datetime(values, format="mixed", errors="coerce")    # TRY_CONVERT(DATE, col), each value on its own
            df[col] = parsed.dt.date.astype(object).where(parsed.notna(), None)

    df.to_sql(
        name=table,
        con=engine,
        schema=schema,
        if_exists=if_exists,
        index=False,                                                            # don't write pandas' row numbers as a column
        dtype=dtype,
        chunksize=10_000,                                                       # send in pieces so huge frames don't time out
    )
    return len(df)
