""" README
Purpose: One place to build SQL Server connections (Windows Authentication), for both pyodbc and SQLAlchemy.
Output: connect() gives a pyodbc connection that closes itself; make_engine() gives a SQLAlchemy engine for pandas.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Paste this block into your script, or import it.
    Reading into pandas:
        df = read_sql("SELECT * FROM dbo.Clients")                               # server/database default to the constants
        df = read_sql("SELECT ...", server="OTHERSERVER")                        # override per call
    Running statements yourself (INSERT/UPDATE/DELETE):
        with connect() as cnxn:
            cnxn.execute("DELETE FROM dbo.Staging")
            cnxn.commit()
    Writing a DataFrame with df.to_sql(...):
        engine = make_engine()
Which one to use:
    pyodbc (connect)      - you write the SQL; fastest for executemany inserts and running .sql files.
    SQLAlchemy (engine)   - pandas writes the SQL for you (df.to_sql); pd.read_sql warns without it.
Why:
    18 of the 29 scripts rebuilt this string by hand, with three different driver names
    ("SQL Server", "ODBC Driver 17 for SQL Server", "SQL SERVER"). Pick one here, change it once.
Requires: pip install pyodbc sqlalchemy pandas
"""

from contextlib import closing
from typing import ContextManager
from urllib.parse import quote_plus

import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

SERVER = "YOURSERVER"                                                           #!REPLACE - default server name
DATABASE = "YourDatabase"                                                       #!REPLACE - default database name
DRIVER = "ODBC Driver 17 for SQL Server"                                        #!REPLACE - run pyodbc.drivers() to see what's installed


def conn_string(server: str = SERVER, database: str = DATABASE) -> str:
    """Build the ODBC connection string for Windows Authentication."""
    return (
        f"DRIVER={{{DRIVER}}};"                                                 # {{ }} prints literal braces around the driver name
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"                                               # = log in as the Windows account running the script
    )


def connect(server: str = SERVER, database: str = DATABASE) -> ContextManager[pyodbc.Connection]:
    """Open a pyodbc connection that closes itself at the end of a with-block."""
    return closing(pyodbc.connect(conn_string(server, database)))               # closing() adds .close() on exit, even after an error


def make_engine(server: str = SERVER, database: str = DATABASE) -> Engine:
    """Build a SQLAlchemy engine for pandas read_sql / to_sql."""
    params = quote_plus(conn_string(server, database))                          # URL-encodes ; = { } so they survive inside a URL
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={params}",
        fast_executemany=True,                                                  # sends rows in batches instead of one round trip each
    )


def read_sql(query: str, server: str = SERVER, database: str = DATABASE) -> pd.DataFrame:
    """Run a SELECT and return the result as a DataFrame."""
    engine = make_engine(server, database)
    try:
        return pd.read_sql(query, engine)                                       # like SELECT ... INTO a temp table you can work with
    finally:
        engine.dispose()                                                        # release the pooled connections
