[README.md](https://github.com/user-attachments/files/32687625/README.md)
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
