r""" README
Purpose: Send email through the Outlook desktop app on this machine - with or without attachments, plain or HTML.
Output: Returns True if Outlook accepted the message, False if it failed. Never raises, so a failed alert can't crash the job.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Paste this block into your script.
    Plain report:
        send_email("a@x.com; b@x.com", "Weekly Backlog", "See attached.", attachments=[xlsx_path])
    HTML body:
        send_email(EMAIL_TO, "Daily HL7 Report", "<p>Greetings,</p>...", cc=EMAIL_CC, html=True)
    Failure alert with the log attached (use inside an except block):
        except Exception:
            send_failure_alert("XiFin Import to SQL", log_file=LOG_DIR / "myscript.log")
Behavior:
    Multiple recipients: one string separated by semicolons, the same as typing them into Outlook.
    Attachments that don't exist are skipped with a warning; the email still goes.
    Paths are made absolute, because Outlook rejects relative attachment paths.
Limits:
    Windows only, Outlook must be installed and signed in for the account running the script.
    If a scheduled task runs while nobody is logged in, Outlook may not start. Test it from Task Scheduler, not just by hand.
Why:
    22 of the 29 scripts pasted their own copy of Dispatch -> CreateItem(0) -> Send.
Requires: pip install pywin32
"""

import logging
import traceback
from pathlib import Path

import win32com.client as win32

ALERT_TO = "you@yourcompany.com"                                                #!REPLACE - who gets failure alerts
OL_MAIL_ITEM = 0                                                                # Outlook's code for "new email"


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    html: bool = False,
    attachments: list = (),
) -> bool:
    """Send one email through Outlook. Returns True on success."""
    try:
        outlook = win32.Dispatch("Outlook.Application")                         # attach to Outlook, starting it if needed
        mail = outlook.CreateItem(OL_MAIL_ITEM)
        mail.To = to
        mail.CC = cc
        mail.Subject = subject
        if html:
            mail.HTMLBody = body                                                # tags like <p>, <b>, <table> are rendered
        else:
            mail.Body = body                                                    # shown exactly as typed

        for path in attachments:
            path = Path(path).resolve()                                         # Outlook needs the full path
            if path.exists():
                mail.Attachments.Add(str(path))
            else:
                logging.warning("Attachment not found, sending without it: %s", path)

        mail.Send()
        logging.info("Email sent: %s", subject)
        return True
    except Exception as exc:                                                    # never let the alert take the job down with it
        logging.error("Email failed (%s): %s", subject, exc)
        return False


def send_failure_alert(job_name: str, log_file: Path | None = None, to: str = ALERT_TO) -> bool:
    """Email the current traceback (and the log, if given). Call from inside an except block."""
    details = traceback.format_exc()                                            # the full error, including which line failed
    body = (
        f"The automated job '{job_name}' failed.\n\n"
        f"Error details:\n{details}\n"
        + (f"Log file: {log_file}\n" if log_file else "")
    )
    for handler in logging.getLogger().handlers:
        handler.flush()                                                         # push buffered lines to disk before attaching
    return send_email(
        to,
        f"FAILED: {job_name}",
        body,
        attachments=[log_file] if log_file else [],
    )
