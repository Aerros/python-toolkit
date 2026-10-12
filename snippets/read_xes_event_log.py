r""" README
Purpose: Read a process-mining event log (.xes, or .xes.gz straight from the download) into a flat DataFrame,
         one row per event, ready for sql_create_table_from_df.py.
Output: Returns a DataFrame. Event fields keep their XES names with ":" swapped for "_" (concept:name -> concept_name);
        case-level fields get a "case_" prefix and repeat on every event row of that case.
Personal Variables: None. Pass the path in.
Implementation:
    Paste this block into your script, or import it.
        events = read_xes_event_log(DOWNLOADS / "Hospital Billing - Event Log.xes.gz")
        events = events.reset_index(names="event_id")                           # keep the file's order as a column
        rows = sql_create_table_from_df(events, "hospital_billing_events", make_engine())
    The three columns process mining needs:
        case_concept_name   case ID     (which case the event belongs to)
        concept_name        activity    (what happened)
        time_timestamp      timestamp   (when)
Behavior:
    XES is XML: each <trace> is one case, each <event> inside it is one row. Fields are tags like
    <string key="concept:name" value="BILLED"/>, so the key becomes the column and the value the cell.
    Text, int, float and boolean values all load as text, like dtype=str in read_pipe_or_csv.py. CAST in SQL if needed.
    Values from <date> tags become datetimes, converted to UTC and stored without a time zone, because SQL Server
    datetime2 has none. Durations between events are unaffected.
    A .gz file is read compressed; nothing is unzipped to disk.
    The file is read one case at a time and each case is cleared from memory after it is copied,
    so a log with hundreds of thousands of events doesn't load the whole XML tree at once.
    Nested list or container fields (rare in public logs) are skipped.
Why:
    pm4py reads XES too, but it is a large install with its own dependencies.
    This needs only the standard library and pandas, and shows exactly how the XML turns into rows.
Requires: pip install pandas
"""

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

FIELD_TAGS = {
      "string"
    , "date"
    , "int"
    , "float"
    , "boolean"
    , "id"
}


def _tag_name(element: ET.Element) -> str:
    """Drop the XML namespace: "{http://www.xes-standard.org/}trace" -> "trace"."""
    parts = element.tag.split("}")
    return parts[len(parts) - 1]                                                # last part; same as parts[-1]


def _column_name(key: str) -> str:
    """concept:name -> concept_name, so SQL Server column names need no brackets."""
    return key.replace(":", "_")


def read_xes_event_log(path: Path) -> pd.DataFrame:
    """Read an XES event log into one row per event, case fields repeated on each row."""
    rows = []
    date_columns = set()                                                        # DISTINCT list of columns that came from <date>
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as xes_file:
        for _, element in ET.iterparse(xes_file, events=("end",)):              # "end" = the tag and everything inside it is read
            if _tag_name(element) != "trace":                                   # wait until one whole case is read
                continue

            case_fields = {}
            for child in element:                                               # fields sitting directly on the case
                if _tag_name(child) in FIELD_TAGS:
                    column = "case_" + _column_name(child.get("key"))
                    case_fields[column] = child.get("value")
                    if _tag_name(child) == "date":
                        date_columns.add(column)

            for child in element:                                               # each event in the case becomes a row
                if _tag_name(child) != "event":
                    continue
                row = dict(case_fields)                                         # copy, so cases don't share one dict
                for field in child:
                    if _tag_name(field) in FIELD_TAGS:
                        column = _column_name(field.get("key"))
                        row[column] = field.get("value")
                        if _tag_name(field) == "date":
                            date_columns.add(column)
                rows.append(row)

            element.clear()                                                     # free this case's XML before reading the next

    events = pd.DataFrame(rows)
    for column in date_columns:
        events[column] = (
            pd.to_datetime(events[column], utc=True, errors="coerce")           # TRY_CONVERT, offsets lined up to UTC
              .dt.tz_convert(None)                                              # drop the zone: datetime2 has none
        )
    return events
