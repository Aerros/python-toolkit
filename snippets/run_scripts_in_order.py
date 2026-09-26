r""" README
Purpose: Run other Python scripts one after another, wait for each, and stop the chain if one fails.
Output: Returns True if every script exited with code 0, False as soon as one doesn't.
Personal Variables: None. Pass the script paths in.
Implementation:
    Paste this block into your script, near the end of main().
        ok = run_scripts_in_order([
            PYTHON_ROOT / "XiFin Import to SQL.py",
            PYTHON_ROOT / "HL7 Monitoring.py",
        ])
        return 0 if ok else 1
Behavior:
    sys.executable runs the children with the SAME Python (and installed packages) as the parent.
    Plain "python" can pick a different install from PATH, and it will fail to import pandas at 3 a.m.
    Each child's printed output and errors are captured into THIS script's log.
    The chain stops at the first non-zero exit code; later scripts don't run on half-loaded data.
    For this to work, each child must end with sys.exit(main()) and return 1 on failure (see script_template.py).
    A child that skips itself on purpose ("not Monday") should exit 0, so the chain continues.
Why not Popen + CREATE_NEW_CONSOLE?
    A new console window shows output to nobody when the job runs unattended, and the window's text is lost.
    Capturing it here means one log tells the whole story of the run.
"""

import logging
import subprocess
import sys
from pathlib import Path


def run_script(script: Path, timeout_minutes: float | None = None) -> bool:
    """Run one script and wait. Returns True if it exited 0."""
    script = Path(script)
    if not script.exists():
        logging.error("Script not found: %s", script)
        return False

    logging.info("Starting: %s", script.name)
    try:
        result = subprocess.run(
            [sys.executable, str(script)],                                      # a list, not a string: spaces in paths are safe
            capture_output=True,                                                # collect stdout/stderr instead of printing
            text=True,                                                          # as str, not bytes
            cwd=script.parent,                                                  # relative paths inside the child still work
            timeout=timeout_minutes * 60 if timeout_minutes else None,
        )
    except subprocess.TimeoutExpired:
        logging.error("%s timed out after %s minutes", script.name, timeout_minutes)
        return False

    if result.stdout.strip():
        logging.info("%s output:\n%s", script.name, result.stdout.strip())
    if result.stderr.strip():
        logging.warning("%s stderr:\n%s", script.name, result.stderr.strip())
    if result.returncode != 0:
        logging.error("%s failed with exit code %s", script.name, result.returncode)
        return False
    logging.info("Finished: %s", script.name)
    return True


def run_scripts_in_order(scripts: list[Path], timeout_minutes: float | None = None) -> bool:
    """Run scripts in order; stop at the first failure."""
    for script in scripts:
        if not run_script(script, timeout_minutes):
            logging.error("Stopping the chain - later scripts were not run.")
            return False
    return True
