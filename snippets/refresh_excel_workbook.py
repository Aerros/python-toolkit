r""" README
Purpose: Open an Excel workbook invisibly, refresh every query/connection, save, and close - with no EXCEL.EXE left behind.
Output: Returns nothing. Raises if the refresh or save fails, so the caller decides whether to email.
Personal Variables: None. Pass the path in.
Implementation:
    Paste this block into your script.
        refresh_excel_workbook(Path(r"\\server\share\Reports\HL7 Report.xlsx"))
    Typical flow:
        refresh_excel_workbook(REPORT)
        send_email(EMAIL_TO, "Daily HL7 Report", BODY, html=True, attachments=[REPORT])
Behavior:
    DispatchEx starts a NEW, private Excel. Plain Dispatch attaches to the Excel you already have open,
    and the Quit() at the end would close YOUR workbooks too.
    CalculateUntilAsyncQueriesDone() waits for background queries, replacing guesses like time.sleep(30).
    Still, turning OFF "Enable background refresh" on each connection is the most reliable setup:
        Data > Queries & Connections > right-click each > Properties > uncheck "Enable background refresh".
    DisplayAlerts = False suppresses "Do you want to save?" and similar pop-ups that would hang an unattended run.
    The finally block always runs, so Excel quits even when the refresh throws.
Limits: Windows only, Excel must be installed.
Requires: pip install pywin32
"""

import logging
from pathlib import Path

import win32com.client as win32


def refresh_excel_workbook(path: Path) -> None:
    """Refresh all data connections in an .xlsx and save it."""
    path = Path(path).resolve()                                                 # COM needs a full path
    if not path.exists():
        raise FileNotFoundError(path)

    excel = win32.DispatchEx("Excel.Application")                               # Ex = separate instance, not your open Excel
    excel.Visible = False
    excel.DisplayAlerts = False                                                 # no pop-ups waiting for a click that never comes
    workbook = None
    try:
        logging.info("Opening %s", path.name)
        workbook = excel.Workbooks.Open(str(path), UpdateLinks=0)               # 0 = don't prompt about external links
        logging.info("Refreshing all connections...")
        workbook.RefreshAll()
        excel.CalculateUntilAsyncQueriesDone()                                  # block until every query has finished
        workbook.Save()
        logging.info("Refreshed and saved %s", path.name)
    finally:
        try:
            if workbook is not None:
                workbook.Close(SaveChanges=False)                               # already saved above
        finally:
            excel.Quit()                                                        # runs even if Close fails: no zombie EXCEL.EXE
