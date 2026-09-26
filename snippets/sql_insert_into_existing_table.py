r""" README
Purpose: Insert a whole DataFrame into an EXISTING SQL Server table, fast, in one transaction.
Output: Returns the number of rows inserted. Raises on failure, and nothing is committed.
Personal Variables: None. Pass the connection, table and DataFrame in.
Implementation:
    Needs a pyodbc connection (see sql_connect.py).
        with connect() as cnxn:
            rows = sql_insert_into_existing_table(cnxn, "dbo.claims", df)               # append
            rows = sql_insert_into_existing_table(cnxn, "dbo.claims", df, replace=True) # swap all rows
CRITICAL - replace=True with no rows:
    An empty DataFrame usually means the source file was empty or failed to load, not "the table
    should now be empty". So replace=True with an empty DataFrame RAISES instead of wiping the table.
    If an empty table really is correct, pass allow_empty=True as well.
Behavior:
    The DataFrame's column names must match the table's column names. Order does not matter.
    The table name can be written any of these ways: claims, dbo.claims, [dbo].[Client Pricing], Billing.dbo.claims.
    (A name that itself contains a dot inside brackets is not supported.)
    Table must already exist. To create/replace the table from the DataFrame, use sql_create_table_from_df.py instead.
    replace=True runs DELETE and INSERT in the same transaction: if the insert fails, the old rows come back.
    An empty DataFrame without replace inserts nothing and returns 0.
    NaN / NaT / None are sent as NULL.
Why not df.to_sql?
    to_sql with if_exists="replace" DROPS the table and rebuilds it, losing your column types, keys and indexes.
    This keeps the table you designed in SSMS and only swaps the rows.
Requires: pip install pyodbc pandas
"""

from typing import Any

import pandas as pd


def sql_insert_into_existing_table(
    cnxn: Any,                                                                  # a pyodbc connection
    table: str,
    df: pd.DataFrame,
    replace: bool = False,
    allow_empty: bool = False,
) -> int:
    """Insert every row of df into table. Returns the row count."""
    if df.empty and not replace:
        return 0                                                                # nothing to add
    if df.empty and not allow_empty:
        raise ValueError(
            f"Refusing to empty {table}: the DataFrame has no rows. "
            "Pass allow_empty=True if an empty table is really what you want."
        )

    parts = [p.strip().strip("[]") for p in table.split(".")]                   # "[dbo].[Client Pricing]" -> dbo, Client Pricing
    target = ".".join(f"[{p}]" for p in parts)                                  # [Billing].[dbo].[claims] - spaces are safe
    columns = ", ".join(f"[{col}]" for col in df.columns)                       # [col1], [col2], ...
    placeholders = ", ".join("?" for _ in df.columns)                           # ?, ?, ...  one per column
    insert_sql = f"INSERT INTO {target} ({columns}) VALUES ({placeholders})"

    clean = df.astype(object).where(df.notna(), None)                           # NaN/NaT -> None, which pyodbc sends as NULL
    rows = list(clean.itertuples(index=False, name=None))                       # each row becomes a plain tuple

    cursor = cnxn.cursor()
    cursor.fast_executemany = True                                              # batches rows; 10-100x faster than one at a time
    try:
        if replace:
            cursor.execute(f"DELETE FROM {target}")                             # DELETE not TRUNCATE: it can roll back
        if rows:
            cursor.executemany(insert_sql, rows)                                # executemany rejects an empty list
        cnxn.commit()                                                           # COMMIT TRAN - both steps land together
    except Exception:
        cnxn.rollback()                                                         # ROLLBACK TRAN - table is left exactly as it was
        raise
    finally:
        cursor.close()
    return len(rows)
