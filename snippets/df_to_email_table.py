r""" README
Purpose: Turn a DataFrame into a readable HTML table for an email body - currency formatted, keywords colored.
Output: Returns an HTML string to drop into an HTML email (send_email(..., html=True) in send_outlook_email.py).
Personal Variables: None. Pass the columns and colors in.
Implementation:
    Paste this block into your script.
        table = df_to_email_table(
            df,
            money_cols=["Balance_Prev", "Balance_Now", "Delta_Balance"],
            highlight={"STAGNANT": "red", "Improving": "green", "Growing": "orange"},
        )
        body = f"<p>Variance this week:</p>{table}"
        send_email(EMAIL_TO, "Weekly AR", body, html=True)
Behavior:
    The DataFrame you pass in is not changed; formatting happens on a copy (keep raw numbers for the Excel attachment).
    Money shows as $1,234.50 and negatives as -$45.00. Blank money cells stay blank.
    Money columns can hold numbers, Decimals, or text like "12.50" / "$1,234" (e.g. straight from read_pipe_or_csv);
    a value that isn't a number is shown as-is instead of raising.
    highlight colors a cell whose ENTIRE value equals the keyword - unlike str.replace on the HTML,
    it can't accidentally recolor a column header or a longer word that contains the keyword.
    Values are HTML-escaped, so a note containing "<" or "&" can't break the email layout.
    Inline styles only - Outlook ignores <style> blocks and CSS classes.
"""

import html
from decimal import Decimal, InvalidOperation

import pandas as pd

CELL = "border:1px solid #bbb;padding:4px 8px;"
HEAD = CELL + "background:#f0f0f0;font-weight:bold;"


def _money(value: object) -> str:
    """12.5, Decimal("12.5") or "$1,234.5" -> "$12.50" / "$1,234.50"; anything unreadable is shown as-is."""
    if pd.isna(value):
        return ""
    try:
        amount = Decimal(str(value).replace("$", "").replace(",", "").strip())
    except InvalidOperation:
        return str(value)                                                       # not a number - show it rather than crash
    if not amount.is_finite():
        return str(value)
    return f"-${abs(amount):,.2f}" if amount < 0 else f"${amount:,.2f}"


def df_to_email_table(
    df: pd.DataFrame,
    money_cols: list[str] | tuple = (),
    highlight: dict[str, str] | None = None,
) -> str:
    """Render df as an Outlook-friendly HTML table."""
    highlight = highlight or {}
    view = df.copy()
    for col in money_cols:
        if col in view.columns:
            view[col] = view[col].map(_money)

    def cell(value: object) -> str:
        text = "" if pd.isna(value) else str(value)
        color = highlight.get(text)
        style = CELL + (f"color:{color};font-weight:bold;" if color else "")
        return f'<td style="{style}">{html.escape(text)}</td>'                  # escape: "<" becomes "&lt;"

    header = "".join(f'<th style="{HEAD}">{html.escape(str(c))}</th>' for c in view.columns)
    rows = "".join(
        "<tr>" + "".join(cell(v) for v in row) + "</tr>"
        for row in view.itertuples(index=False, name=None)
    )
    return f'<table style="border-collapse:collapse;"><tr>{header}</tr>{rows}</table>'
