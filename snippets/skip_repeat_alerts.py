r""" README
Purpose: Remember what you last alerted about, so a daily job doesn't send the same alert every day until it's fixed.
Output: already_alerted() returns True/False; mark_alerted() records the key. State lives in a small JSON file.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Paste this block into your script.
        key = f"deposit-gap:{last_deposit}"                                      # anything that identifies THIS problem
        if gap >= 3 and not already_alerted(key):
            if send_email(...):                                                 # only remember it if the email actually went
                mark_alerted(key)
    When the problem changes (a new last_deposit date), the key changes and the alert fires again.
Behavior:
    One JSON file can hold keys for several alerts: {"deposit-gap": "2026-09-22", "hl7-late": "..."}.
    The part before the first ":" is the alert name; each alert remembers only its latest value.
    A missing, unreadable or corrupt state file counts as "never alerted" - worst case you get one extra
    email, never zero. (Writing the file still raises if the folder isn't writable - that's a setup problem.)
    The file is written atomically, so a crash mid-write can't corrupt it.
Why a JSON file instead of an Excel file?
    The original used pandas + openpyxl to store one date. JSON needs no packages, and it can't be left
    locked because someone has it open in Excel.
"""

import json
import logging
from pathlib import Path

STATE_FILE = Path(r"C:\path\to\alert_state.json")                               #!REPLACE - somewhere the job account can write


def _load() -> dict:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):                                               # missing, unreadable, not UTF-8, not JSON
        return {}                                                               # no memory yet = never alerted
    return state if isinstance(state, dict) else {}                             # valid JSON but the wrong shape = no memory


def already_alerted(key: str) -> bool:
    """True if this exact key was the last one recorded for its alert name."""
    name, _, value = key.partition(":")                                         # "deposit-gap:2026-09-22" -> name, value
    return _load().get(name) == value


def mark_alerted(key: str) -> None:
    """Record key as the latest alert for its alert name."""
    name, _, value = key.partition(":")
    state = _load()
    state[name] = value
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_name(STATE_FILE.name + ".partial")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)                                                     # all-or-nothing, see write_file_safely.py
    logging.info("Recorded alert: %s", key)
