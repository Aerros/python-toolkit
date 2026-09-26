r""" README
Purpose: Tag free-text notes with one or more categories using a dictionary of regex patterns, one row per match.
Output: Returns a DataFrame: id column, Category, Matched_Text. A note matching 3 categories produces 3 rows.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Paste this block into your script.
        tagged = tag_notes_by_keyword(df, id_col="Accession", text_col="Contact Info")
        tagged.to_sql("note_categories", engine, if_exists="replace", index=False)
    Then in SQL:  SELECT Category, COUNT(DISTINCT Accession) FROM note_categories GROUP BY Category
Writing patterns:
    Matching is case-insensitive; write patterns in lower case.
    \b     = word boundary:  r"\bauth" matches "auth", "authorization", but not "coauthor".
    .*?    = "anything, as little as possible":  r"\bsent.*?medical records"
    A category with several phrasings is just a list of patterns - ANY one match tags the note.
    Test patterns at https://regex101.com (Python flavor) against a few real notes before adding them.
Behavior:
    Blank notes -> Category = BLANK_LABEL.  Notes nothing matched -> Category = NO_MATCH_LABEL.
    Matched_Text shows the exact words that triggered the tag, so you can spot a pattern that's too greedy.
    Patterns are compiled once, not once per row - this matters at 100k+ notes.
Why:
    The contact-info script's approach (explode one note into many category rows) works for any
    free-text field: denial reasons, memo lines, ticket descriptions.
"""

import re

import pandas as pd

CATEGORY_PATTERNS: dict[str, list[str]] = {                                     #!REPLACE - your categories and phrasings
    "Appeal Submitted": [r"\bappeal (?:was )?sent", r"\bsubmitted\w* appeal"],
    "Medical Records Sent": [r"\bsent med(?:ical)? rec", r"\battached medical records"],
    "Timely Filing": [r"\buntimely", r"\btfl expired"],
}
BLANK_LABEL = "Uncategorized"                                                   #!REPLACE - label for empty notes
NO_MATCH_LABEL = "Uncategorized Free-Text"                                      #!REPLACE - label for notes nothing matched

_COMPILED = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]                  # compile once, reuse for every row
    for category, patterns in CATEGORY_PATTERNS.items()
}


def match_categories(note: object) -> list[tuple[str, str | None]]:
    """Return [(category, matched text), ...] for one note."""
    if pd.isna(note) or not str(note).strip():
        return [(BLANK_LABEL, None)]
    text = str(note)
    found = []
    for category, patterns in _COMPILED.items():
        hits = {m.group(0).lower() for p in patterns for m in p.finditer(text)}  # every distinct phrase that matched
        if hits:
            found.append((category, ", ".join(sorted(hits))))
    return found or [(NO_MATCH_LABEL, None)]


def tag_notes_by_keyword(df: pd.DataFrame, id_col: str, text_col: str) -> pd.DataFrame:
    """One output row per (id, category) - like CROSS APPLY in SQL."""
    out = df[[id_col]].copy()
    out["_hits"] = df[text_col].map(match_categories)
    out = out.explode("_hits")                                                  # one row per list item
    out["Category"] = out["_hits"].str[0]
    out["Matched_Text"] = out["_hits"].str[1]
    return out.drop(columns="_hits").drop_duplicates().reset_index(drop=True)
