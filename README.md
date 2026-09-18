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
- `log_setup.py` — rotating file + console logging for unattended scripts
- `credentials.py` — read secrets/credentials from environment variables

Files and folders:
- `find_latest_folder_date.py` — find latest folder whose name matches a date

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
