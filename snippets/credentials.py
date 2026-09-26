r""" README
Purpose: Read credentials from environment variables instead of clear-text hardcoding in script through Python.
Output: Returns the named values in the order requested; raises if any are missing.
Personal Variables: None! Instead, pass the names in when you call the function.
Implementation:
    Paste this block into your script.
    Call it with the variable names you want, in the order you want them back.
        Example: If the system name associated with the credentials was "ABC123", you would write in uppercase:
            USER, KEY, PASSPHRASE = load_credentials("ABC123_USER_NAME", "ABC123_KEY", "ABC123_PASSWORD")
Security:
    For anything higher-stakes, use Windows Credential Manager or a secrets store.
    Otherwise, this will sit inside the machine's registry.
Setup - Set them once per machine while logged in as that account, or use setx /M from an admin prompt to set them machine-wide for every user.
    Command Prompt Method:
        1. Open Command Prompt (not PowerShell).
        2. Set each one:
            setx ABC123_USER_NAME "youruser"
            setx ABC123_KEY "C:...\yourKeysFolder\yourActualFileName.pem"
            setx ABC123_PASSWORD "yourPassPhrase"
        3. CLOSE that window and open a NEW one. setx does not affect the window you typed it in.
        4. Verify:  echo %ABC123_USER_NAME%
    GUI alternative:
        1. Win+R, 2. sysdm.cpl, 3. Advanced, 4. Environment Variables,
        5. New... under the TOP box (User variables), 6. Set the 3 variables
        Note: the bottom box is System variables and needs admin rights.
"""
import os

def load_credentials(*names: str) -> tuple[str, ...]:                           # *names accepts 2+ names; returns a tuple of that many strings
    """Return the named environment variables, or raise if any are missing."""
    values = [os.environ.get(name) for name in names]                           # .get() gives None if unset instead of crashing
    missing = [name for name, value in zip(names, values) if not value]         # zip pairs them by position; "not value" catches None and ""
    if missing:                                                                 # empty list is falsy, so this means "if any are missing"
        raise RuntimeError(                                                     # raise stops here rather than failing later with a vague error
            "Missing environment variable(s): " + ", ".join(missing)            # join turns ["A","B"] into "A, B"
            + ". Set them with setx, then open a NEW terminal."
        )
    return tuple(values)                                                        # tuple unpacks cleanly: USER, KEY, PASS = load_credentials(...)