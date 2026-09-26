[README.md](https://github.com/user-attachments/files/32687884/README.md)
# python-toolkit

Reusable Python building blocks and practice projects.

Every file opens with a `""" README` docstring saying what it does, what it
returns, and what you have to change. Anything you must edit is marked
`#!REPLACE`.

## Layout

| Folder | Holds | How you use it |
|---|---|---|
| `snippets/` | Paste-in building blocks. No side effects. | Copy the block into your script, or import it |
| `tools/` | Standalone scripts that do something | Edit the constants at the top, then run the file |
| `projects/` | Multi-file work, not meant to be reused piecemeal | See that project's own README |

## snippets/

Core — used by any script, whatever it touches:
- `script_template.py` — the starting shape for an unattended job: logging
  first, `main() -> int`, one safety net that emails the traceback, a real exit
  code. Copy it, don't import it.
- `log_setup.py` — rotating file + console logging for unattended scripts
- `credentials.py` — read secrets/credentials from environment variables
- `outlook_email.py` — `send_email()` (plain or HTML, CC, attachments) and
  `send_failure_alert()` (traceback + log file). Never raises. Windows + Outlook.
- `run_scripts.py` — run other scripts in order with the same Python, capture
  their output into this log, stop the chain at the first failure
- `retry.py` — retry a call that fails for a known temporary reason (SQL
  deadlock, Excel "Call was rejected by callee"); any other error raises at once

SQL Server:
- `sql_connect.py` — one place for the Windows-auth connection string; gives a
  pyodbc connection, a SQLAlchemy engine, and `read_sql()`
- `sql_bulk_insert.py` — fast insert of a DataFrame into an existing table;
  `replace=True` empties it first in the same transaction
- `sql_run_file.py` — run a saved `.sql` file, split on `GO` like SSMS, all
  batches in one transaction
- `df_to_sql_typed.py` — `df.to_sql` with real column types (DATE,
  DECIMAL(18,2), NVARCHAR(MAX)). Default `replace` drops the table — read the
  CRITICAL section.

Cleaning and reading data:
- `clean_columns.py` — money (`$`, commas, `(negatives)`, half-up cents), whole
  numbers, dates, IDs (drops Excel's `.0`), text. Bad values become NULL.
- `read_delimited_file.py` — pipe/CSV extract with every value as text,
  encoding detected, stray quotes kept as data instead of rewriting the file
- `report_sheet_to_table.py` — report-shaped Excel sheet (title rows, blank
  column A, summary at the bottom) to a clean table, found by header text
  rather than row counting
- `categorize_text.py` — tag free-text notes with categories from a regex
  dictionary, one row per match

Comparing and checking:
- `compare_snapshots.py` — save today's snapshot; list rows added, removed, or
  changed since the last one
- `find_overlapping_periods.py` — records whose effective-date ranges overlap
  for the same ID (pandas version of SQL `LEAD()`)
- `alert_once.py` — remember the last alert sent so a daily job doesn't repeat
  the same email every day

Dates and schedules:
- `business_days.py` — skip weekends and US holidays, business-day gaps, last
  Friday, first business day of the month, "only run on Mondays"
- `date_from_filename.py` — pull a date out of a file name, and strip it off

Files and folders:
- `find_latest_folder_date.py` — find latest folder whose name matches a date
- `dated_folder_path.py` — build `Output\2026\09262026` from a date; the write
  side of the one above. Keep the two in sync.
- `find_latest_files.py` — newest file, or newest N files, matching a pattern
- `cleanup_old_files.py` — keep the newest N files, delete the rest. Defaults to
  `dry_run=True`; preview before applying.
- `atomic_write.py` — write to `.partial`, rename when complete, so a file is
  never half-written. `gunzip_file()` is the worked example.
- `sftp_download.py` — key-based SFTP download that verifies the server's host
  key and skips files already downloaded

Windows / Office (pywin32 + the desktop app):
- `html_table.py` — DataFrame to an Outlook-friendly HTML table: currency
  formatting, colored keywords, escaped values
- `excel_refresh.py` — open a workbook in a private hidden Excel, RefreshAll,
  wait for queries, save, quit. Never touches the Excel you have open.

## Using snippets together

There are two ways to combine snippets in one script. Both end up with the
same `main()`.

| | Paste | Import |
|---|---|---|
| How | Copy each snippet's code into the script | `from snippets.x import y` |
| Script is | One self-contained file | Small; the snippets live in one shared folder |
| Fix a bug in a snippet | Fix it in every script that has a copy | Fix it once, every script gets it |
| Best for | Handing a script to someone, one-off jobs | Your own scheduled jobs |

### The one rule: define first, run last

Python reads a file top to bottom. A `def` line does not run anything. It only
stores the function under that name. The code inside the function runs when
something *calls* it. So:

- `def`s can be in any order, and one can call another defined further down.
- A line that **calls** a function must come after that function's `def`.
- Nothing should run until the last line, `sys.exit(main())`. By then every
  `def` above it has been read.

### Option A: paste (stack them in one file)

Stack them in this order. The same order works for every script:

```python
# 1. IMPORTS - every import from every snippet you pasted, once each, at the top.
#    Two snippets both importing logging? Keep one line.
import logging
import sys
from pathlib import Path

import pandas as pd

# 2. CONSTANTS - every #!REPLACE line from every snippet, together, plus your own.
LOG_DIR = Path(r"C:\Logs\XiFin")
LOG_NAME = "xifin_client_type"
SERVER = "IRONMAN2"

# 3. SNIPPET FUNCTIONS - paste each snippet's def blocks (skip its docstring
#    and imports, which you already merged above). Any order.
def configure_logging(...): ...
def read_sql(...): ...
def send_email(...): ...

# 4. main() - your job, calling the functions above in the order the work happens.
def main() -> int:
    ...

# 5. ENTRY POINT - the only line that actually starts anything.
if __name__ == "__main__":
    sys.exit(main())
```

If two snippets define the same constant name (`LOG_DIR`, say), keep one line.

### Option B: import (keep one shared copy)

Leave the toolkit where it is and point each script at it:

```text
C:\Users\you\python-toolkit\         <- this repo, cloned once
    snippets\
        log_setup.py
        sql_connect.py
        ...
C:\Jobs\xifin_client_type.py         <- your script, can live anywhere
```

Then:

```python
import sys
sys.path.insert(0, r"C:\Users\you\python-toolkit")   # where to look for "snippets"

from snippets.log_setup import configure_logging     # from <folder>.<file> import <function>
from snippets.sql_connect import read_sql
```

- `sys.path.insert` has to come before the `from snippets...` lines. It tells
  Python where the `snippets` folder is.
- The `#!REPLACE` values in the shared copy are defaults for **every** script.
  Set the ones that stay the same everywhere (`SERVER`, `DRIVER`, `ALERT_TO`,
  `LOG_DIR`) once in the snippet file.
- Anything that differs per script, pass as an argument, **not** by editing the
  snippet: `configure_logging("xifin_client_type")`,
  `read_sql(QUERY, server="OTHER")`, `send_email(to=..., ...)`.
- Setting `sql_connect.SERVER = "X"` after importing does **not** reliably
  work. Default argument values are fixed when the file is first read. Pass
  arguments instead.
- Paste, don't import, the snippets whose settings are specific to one job:
  `date_from_filename`, `dated_folder_path`, `find_latest_folder_date`,
  `categorize_text`, `sftp_download`. Their `#!REPLACE` values describe one
  vendor or one folder tree.

### Worked example: XiFin Client Type, rebuilt from snippets

This is `XiFin Client Type.py` (about 120 lines) rebuilt with imports: take
today's snapshot, compare it with the last one, email any client whose
Hospital / Non-Hospital category changed, and email the error if anything
breaks.

```python
""" README
Purpose: Email when a client's Hospital / Non-Hospital category changes between daily snapshots.
Output: Exit 0 on success (changes or not), 1 on failure.
Personal Variables: Find "#!REPLACE" comments to locate.
"""

import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, r"C:\Users\you\python-toolkit")                              #!REPLACE - where this repo lives

import pandas as pd

from snippets.compare_snapshots import changed_rows, save_snapshot
from snippets.find_latest_files import latest_files
from snippets.log_setup import configure_logging
from snippets.outlook_email import send_email, send_failure_alert
from snippets.sql_connect import read_sql

JOB_NAME = "XiFin Client Type"
SNAPSHOT_DIR = Path(r"\\server\Billing\XiFin\Client Type\Snapshots")          #!REPLACE
CHANGES_DIR = Path(r"\\server\Billing\XiFin\Client Type\Changes")             #!REPLACE
EMAIL_TO = "a@company.com; b@company.com"                                      #!REPLACE
QUERY = """
    SELECT client_id, account_name, account_type,
           CASE WHEN account_type = 'Hospital' THEN 'Hospital' ELSE 'Non-Hospital' END
               AS account_type_category
    FROM dbo.Clients
"""                                                                             #!REPLACE - your query


def main() -> int:
    log_file = configure_logging("xifin_client_type")                           # 1. logging first, own log file
    try:
        save_snapshot(read_sql(QUERY), SNAPSHOT_DIR, "xifin_client_type")       # 2. today's copy

        files = latest_files(SNAPSHOT_DIR, "xifin_client_type_*.xlsx", n=2, by="name")
        if len(files) < 2:
            logging.info("First snapshot - nothing to compare yet.")
            return 0                                                            # nothing to do is not a failure
        old, new = (pd.read_excel(f) for f in files)                            # 3. yesterday vs today

        changed = changed_rows(old, new, key="client_id", watch=["account_type_category"])
        if changed.empty:
            logging.info("No client type changes.")
            return 0

        CHANGES_DIR.mkdir(parents=True, exist_ok=True)                          # 4. report + email
        report = CHANGES_DIR / f"xifin_client_type_changes_{date.today():%Y-%m-%d}.xlsx"
        changed.to_excel(report, index=False)
        send_email(
            EMAIL_TO,
            f"CDx Client Type Changes Detected - {date.today():%Y-%m-%d}",
            f"{len(changed)} client(s) moved between Hospital and Non-Hospital.\n"
            f"Details attached.",
            attachments=[report],
        )
        return 0

    except Exception:                                                           # 5. the safety net
        logging.exception("%s failed", JOB_NAME)
        send_failure_alert(JOB_NAME, log_file=log_file)
        return 1


if __name__ == "__main__":                                                      # 6. the only line that runs anything
    sys.exit(main())
```

Read `main()` top to bottom and it describes the job. Each detail (how to
connect, how to compare, how to email) is one function call whose code sits in
a snippet file.

## tools/

- `increment_intprefix_filenames.py` — add 1 to the leading number on every file
  in a folder (`1_claims.txt` → `2_claims.txt`). Renames highest-first so the
  numbers can't collide. Defaults to `DRY_RUN = True`; preview before applying.

## projects/

(coming)

## Conventions

These hold across every file here, so a file you wrote a year ago still reads
the way you expect.

- **Header docstring.** `""" README` block at the top: Purpose, Output, Personal
  Variables, and — where the thing can be used wrong — a `CRITICAL` section and
  a `Behavior` section stating what is ignored versus what raises.
- **`#!REPLACE`.** Marks every line you have to edit before the file runs.
  Searchable, so "what do I change" is a Ctrl+F, not a read-through.
- **Constants up top.** ALL_CAPS, directly under the imports, never inside a
  function.
- **Type hints on every signature.** Especially `X | None`, which is how a
  function says out loud that it might find nothing.
- **Comments in a right-hand column.** Aligned, so the code reads straight down
  and the commentary reads as a second column beside it.
- **Windows paths use `r"..."`.** Raw strings, always.
- **Anything destructive previews first.** A `DRY_RUN` / `@WhatIf` style flag
  defaulting to "show me, don't do it."

## Adding a file

1. Does it have side effects, or is it a building block? → `tools/` or `snippets/`.
2. Write the header docstring before the code.
3. Mark the edit points with `#!REPLACE`.
4. Add one line to the list above.
5. If it's a snippet, keep per-script settings as function arguments with
   defaults, so it works both pasted and imported.
