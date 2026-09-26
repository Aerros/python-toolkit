r""" README
Purpose: Read a vendor text extract (pipe, comma or tab delimited) into a DataFrame safely: every value as text,
         encoding detected, quotes handled, junk "Unnamed" columns dropped.
Output: Returns a DataFrame where every cell is a string ("" for empty).
Personal Variables: None. Pass the path and delimiter in.
Implementation:
    Paste this block into your script.
        df = read_pipe_or_csv(OUTPUT_DIR / "accn_contact.txt")                  # pipe-delimited by default
        df = read_pipe_or_csv(path, sep=",")                                    # CSV
        df = read_pipe_or_csv(path, sep="\t")                                   # tab-delimited
        table = path.stem                                                       # "accn_contact" -> load into [accn_contact]
Behavior:
    dtype=str: pandas does not guess types, so ZIP 01234 stays "01234" and ID 1001 doesn't become 1001.0.
    Encoding: tries UTF-8, then cp1252 (Windows/Excel exports), then latin-1, which accepts every byte.
    Quotes depend on the delimiter:
        sep=","   standard CSV quoting: "Smith, John" stays one value, and the quotes are removed.
        any other a " is ordinary text, so a lone " inside a value (5" x 7" slide) can't swallow the rest
                  of the file. This replaces rewriting the file to delete quotes (sanitize_accn_file);
                  the source file is never modified.
    Set strip_quotes=True to also remove any " characters left in the values.
    Headers and values are trimmed.
    Trailing delimiters are safe whether they're on every line ("a|b|c|") or only on the data rows:
    the extra empty column is dropped and the other columns stay where they belong.
    A column with a blank header but real data in it (a||c) is kept, named Column_<n>; only empty ones are dropped.
    When only the data rows have the extra delimiter, pandas prints a ParserWarning. That is expected; it is also
    what you'd see if a row had a real extra value, so if the row counts look wrong, open the file and check.
Requires: pip install pandas
"""

import csv
import re
from pathlib import Path

import pandas as pd

ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")                                  # utf-8-sig strips a BOM; latin-1 never fails


def read_pipe_or_csv(path: Path, sep: str = "|", strip_quotes: bool = False) -> pd.DataFrame:
    """Read a delimited text file with every column as text."""
    quoting = csv.QUOTE_MINIMAL if sep == "," else csv.QUOTE_NONE               # CSV honors quotes; pipe/tab treat " as text
    last_error: Exception | None = None
    for encoding in ENCODINGS:
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                dtype=str,                                                      # no type guessing - like importing all as VARCHAR
                encoding=encoding,
                quoting=quoting,
                keep_default_na=False,                                          # "NA" and "null" stay as text, blanks become ""
                index_col=False,                                                # never turn column 1 into the row index
            )
            break
        except UnicodeDecodeError as exc:
            last_error = exc                                                    # wrong guess - try the next encoding
    else:
        raise last_error                                                        # for/else: only if every encoding failed

    df = df.apply(lambda col: col.str.strip())                                  # LTRIM(RTRIM()) every value
    names = []
    for n, name in enumerate(df.columns, start=1):
        name = str(name).strip()
        if re.fullmatch(r"Unnamed: \d+", name):                                 # pandas' exact label for a blank header cell
            name = "" if (df.iloc[:, n - 1] == "").all() else f"Column_{n}"     # empty -> drop later; has data -> keep it
        names.append(name)
    df.columns = names
    df = df.loc[:, [name != "" for name in names]]                              # drop only the truly empty ones
    if strip_quotes:
        df = df.apply(lambda col: col.str.replace('"', "", regex=False))
        df.columns = [c.replace('"', "") for c in df.columns]
    return df
