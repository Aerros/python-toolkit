""" README
Purpose: Turn a DataFrame into a readable HTML table for an email body - currency formatted, keywords colored.
Output: Returns an HTML string to drop into an HTML email (send_email(..., html=True) in outlook_email.py).
Personal Variables: None. Pass the columns and colors in.
Implementation:
    Paste this block into your script.
        table = df_to_html_table(
            df,
            money_cols=["Balance_Prev", "Balance_Now", "Delta_Balance"],
            highlight={"STAGNANT": "red", "Improving": "green", "Growing": "orange"},
        )
        body = f"<p>Variance this week:</p>{table}"
        send_email(EMAIL_TO, "Weekly AR", body, html=True)
Behavior:
    The DataFrame you pass in is not changed; formatting happens on a copy (keep raw numbers for the Excel attachment).
    Money shows as $1,234.50 and negatives as -$45.00. Blank money cells stay blank.
    highlight colors a cell whose ENTIRE value equals the keyword - unlike str.replace on the HTML,
    it can't accidentally recolor a column header or a longer word that contains the keyword.
    Values are HTML-escaped, so a note containing "<" or "&" can't break the email layout.
    Inline styles only - Outlook ignores <style> blocks and CSS classes.
"""

import html

import pandas as pd

CELL = "border:1px solid #bbb;padding:4px 8px;"
HEAD = CELL + "background:#f0f0f0;font-weight:bold;"


def _money(value: float | None) -> str:
    if pd.isna(value):
        return ""
    return f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"


def df_to_html_table(
    df: pd.DataFrame,
    money_cols: list[str] = (),
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
