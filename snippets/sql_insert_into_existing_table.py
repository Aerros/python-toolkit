""" README
Purpose: Insert a whole DataFrame into an EXISTING SQL Server table, fast, in one transaction.
Output: Returns the number of rows inserted. Raises on failure, and nothing is committed.
Personal Variables: None. Pass the connection, table and DataFrame in.
Implementation:
    Needs a pyodbc connection (see sql_connect.py).
        with connect() as cnxn:
            rows = bulk_insert(cnxn, "dbo.claims", df)                          # append
            rows = bulk_insert(cnxn, "dbo.claims", df, replace=True)            # empty the table first, then load
Behavior:
    The DataFrame's column names must match the table's column names. Order does not matter.
    Table must already exist. To create/replace the table from the DataFrame, use df_to_sql_typed.py instead.
    replace=True runs DELETE and INSERT in the same transaction: if the insert fails, the old rows come back.
    NaN / NaT are sent as NULL.
Why not df.to_sql?
    to_sql with if_exists="replace" DROPS the table and rebuilds it, losing your column types, keys and indexes.
    This keeps the table you designed in SSMS and only swaps the rows.
Requires: pip install pyodbc pandas
"""

import pandas as pd


def bulk_insert(cnxn, table: str, df: pd.DataFrame, replace: bool = False) -> int:
    """Insert every row of df into table. Returns the row count."""
    if df.empty:
        return 0

    schema, _, name = table.rpartition(".")                                     # "dbo.claims" -> ("dbo", ".", "claims")
    target = f"[{schema}].[{name}]" if schema else f"[{name}]"                  # brackets survive spaces: [Client Pricing]
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
        cursor.executemany(insert_sql, rows)
        cnxn.commit()                                                           # COMMIT TRAN - both steps land together
    except Exception:
        cnxn.rollback()                                                         # ROLLBACK TRAN - table is left exactly as it was
        raise
    finally:
        cursor.close()
    return len(rows)
