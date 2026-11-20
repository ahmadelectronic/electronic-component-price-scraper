"""Excel report formatting and price-history persistence."""

from __future__ import annotations

import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill

from .models import ScrapeResult


SITE_COLORS = [
    "D9D2E9", "CFE2F3", "FCE5CD", "FFF2CC", "D0E0E3", "EAD1DC",
    "B6D7A8", "F4CCCC", "C9DAF8", "FFD966", "B4A7D6", "A2C4C9",
]


def write_report(
    dataframe: pd.DataFrame,
    results: list[ScrapeResult],
    output_file: str | Path,
    history_file: str | Path,
) -> int:
    """Write the detailed workbook, append history and return the grand total."""
    output_path, history_path = Path(output_file), Path(history_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    dataframe = dataframe.copy()
    dataframe["Status"] = [item.status for item in results]
    dataframe["Price"] = [item.price if item.price is not None else "" for item in results]
    dataframe["Total Price"] = [item.total_price if item.total_price is not None else "" for item in results]
    dataframe.to_excel(output_path, index=False)

    workbook = load_workbook(output_path)
    sheet = workbook.active
    columns = {cell.value: cell.column for cell in sheet[1]}
    supplier_col = columns.get("Supplier")
    status_col = columns.get("Status")
    price_col = columns.get("Price")
    total_col = columns.get("Total Price")

    _format_supplier_links(sheet, supplier_col)
    _format_status(sheet, status_col)
    _format_supplier_domains(sheet, supplier_col)

    grand_total = sum(item.total_price or 0 for item in results)
    previous_total = _append_summary(sheet, total_col, grand_total, history_path)
    _append_history(history_path, grand_total, previous_total)

    _format_price_columns(sheet, price_col, total_col)
    workbook.save(output_path)
    return grand_total


def _format_supplier_links(sheet, column: int | None) -> None:
    if not column:
        return
    for row in range(2, sheet.max_row + 1):
        cell = sheet.cell(row, column)
        if cell.value:
            cell.hyperlink = str(cell.value)
            cell.style = "Hyperlink"


def _format_status(sheet, column: int | None) -> None:
    if not column:
        return
    fills = {
        "OK": PatternFill("solid", fgColor="C6EFCE"),
        "NO": PatternFill("solid", fgColor="FFC7CE"),
        "ERROR": PatternFill("solid", fgColor="FFC7CE"),
    }
    for row in range(2, sheet.max_row + 1):
        cell = sheet.cell(row, column)
        if cell.value in fills:
            cell.fill = fills[cell.value]


def _format_supplier_domains(sheet, column: int | None) -> None:
    if not column:
        return
    site_fills: dict[str, PatternFill] = {}
    for row in range(2, sheet.max_row + 1):
        cell = sheet.cell(row, column)
        if not cell.value:
            continue
        host = urlparse(str(cell.value)).hostname or "local-file"
        host = host.removeprefix("www.").lower()
        if host not in site_fills:
            color = SITE_COLORS[len(site_fills) % len(SITE_COLORS)]
            site_fills[host] = PatternFill("solid", fgColor=color)
        cell.fill = site_fills[host]


def _read_previous_total(history_path: Path) -> float | None:
    if not history_path.exists():
        return None
    history = load_workbook(history_path, read_only=True, data_only=True)
    sheet = history.active
    for row in range(sheet.max_row, 1, -1):
        value = sheet.cell(row, 2).value
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _append_summary(sheet, total_col: int | None, grand_total: int, history_path: Path) -> float | None:
    if not total_col:
        return None
    previous_total = _read_previous_total(history_path)
    row = sheet.max_row + 1
    sheet.cell(row, total_col - 1, "Grand Total")
    sheet.cell(row, total_col, grand_total)
    if previous_total is not None:
        sheet.cell(row + 1, total_col - 1, "Previous Total")
        sheet.cell(row + 1, total_col, previous_total)
        sheet.cell(row + 2, total_col - 1, "Difference")
        difference_cell = sheet.cell(row + 2, total_col, grand_total - previous_total)
        difference_cell.number_format = "#,##0;[Red]-#,##0"
    return previous_total


def _append_history(history_path: Path, grand_total: int, previous_total: float | None) -> None:
    if history_path.exists():
        workbook = load_workbook(history_path)
        sheet = workbook.active
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Price History"

    if sheet.max_row == 1 and all(cell.value is None for cell in sheet[1]):
        for column, title in enumerate(("Date / Time", "Grand Total", "Price Change %"), start=1):
            sheet.cell(1, column, title)
    elif sheet.max_row == 1 and sheet.cell(1, 1).value != "Date / Time":
        sheet.insert_rows(1)
        sheet.cell(1, 1, "Date / Time")
        sheet.cell(1, 2, "Grand Total")
        sheet.cell(1, 3, "Price Change %")

    new_row = sheet.max_row + 1
    sheet.cell(new_row, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    total_cell = sheet.cell(new_row, 2, grand_total)
    total_cell.number_format = "#,##0"

    percentage = None
    if previous_total not in (None, 0):
        percentage = (grand_total - previous_total) / previous_total
    percent_cell = sheet.cell(new_row, 3, percentage)
    percent_cell.number_format = "0.00%"

    sheet.column_dimensions["A"].width = 22
    sheet.column_dimensions["B"].width = 20
    sheet.column_dimensions["C"].width = 18
    workbook.save(history_path)


def _format_price_columns(sheet, price_col: int | None, total_col: int | None) -> None:
    for column in (price_col, total_col):
        if not column:
            continue
        longest = 0
        for row in range(1, sheet.max_row + 1):
            cell = sheet.cell(row, column)
            cell.number_format = "#,##0"
            text = f"{int(cell.value):,}" if isinstance(cell.value, (int, float)) else str(cell.value or "")
            longest = max(longest, len(text))
        sheet.column_dimensions[sheet.cell(1, column).column_letter].width = longest + 2


def open_file(path: str | Path) -> None:
    """Open the generated report with the operating system's default app."""
    target = str(Path(path).resolve())
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(target)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])
    except (OSError, AttributeError) as exc:
        import logging
        logging.getLogger(__name__).warning("Could not open Excel file: %s", exc)
