""" README
Purpose: Read a vendor text extract (pipe, comma or tab delimited) into a DataFrame safely: every value as text,
         encoding detected, stray quotes handled, junk "Unnamed" columns dropped.
Output: Returns a DataFrame where every cell is a string ("" for empty).
Personal Variables: None. Pass the path and delimiter in.
Implementation:
    Paste this block into your script.
        df = read_delimited(OUTPUT_DIR / "accn_contact.txt")                    # pipe-delimited by default
        df = read_delimited(path, sep=",")                                      # CSV
        table = path.stem                                                       # "accn_contact" -> load into [accn_contact]
Behavior:
    dtype=str: pandas does not guess types, so ZIP 01234 stays "01234" and ID 1001 doesn't become 1001.0.
    Encoding: tries UTF-8 first, then cp1252 (Windows/Excel exports), which can read any byte.
    quoting=QUOTE_NONE: a lone " inside a value (5" x 7" slide) is kept as data instead of swallowing the rest of the file.
    That replaces rewriting the file to delete quotes (sanitize_accn_file) - the source file is never modified.
    Set strip_quotes=True if you want the " characters removed from the values too.
    Headers and values are trimmed. A trailing delimiter at line end ("a|b|c|") no longer creates an "Unnamed: 3" column.
Requires: pip install pandas
"""

import csv
from pathlib import Path

import pandas as pd

ENCODINGS = ("utf-8-sig", "cp1252")                                             # utf-8-sig also strips a BOM if present


def read_delimited(path: Path, sep: str = "|", strip_quotes: bool = False) -> pd.DataFrame:
    """Read a delimited text file with every column as text."""
    last_error = None
    for encoding in ENCODINGS:
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                dtype=str,                                                      # no type guessing - like importing all as VARCHAR
                encoding=encoding,
                quoting=csv.QUOTE_NONE,                                         # treat " as ordinary text
                keep_default_na=False,                                          # "NA" and "null" stay as text, blanks become ""
            )
            break
        except UnicodeDecodeError as exc:
            last_error = exc                                                    # wrong guess - try the next encoding
    else:
        raise last_error                                                        # for/else: every encoding failed

    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]                       # drop empty columns from trailing delimiters
    df = df.apply(lambda col: col.str.strip())                                  # LTRIM(RTRIM()) every value
    if strip_quotes:
        df = df.apply(lambda col: col.str.replace('"', "", regex=False))
        df.columns = [c.replace('"', "") for c in df.columns]
    return df
