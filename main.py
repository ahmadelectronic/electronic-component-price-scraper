import os
import re
import platform
import subprocess
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill
from urllib.parse import urlparse
from scrapers.router import find_price
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

# Input and output Excel files
INPUT_EXCEL = "database.xlsx"
OUTPUT_EXCEL = "output.xlsx"
HISTORY_EXCEL = "price_history.xlsx"

# Read Excel file
df = pd.read_excel(INPUT_EXCEL)

df.columns = df.columns.str.strip()


if "Supplier" not in df.columns:
    raise ValueError(f"Excel file must contain 'Supplier' column. Found: {list(df.columns)}")

if "Quantity" not in df.columns:
    raise ValueError(f"Excel file must contain 'Quantity' column. Found: {list(df.columns)}")


contents = []
status = []
prices = []
total_prices = []

def get_page(url):

    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36",

        "Accept":
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8",

        "Accept-Language":
            "en-US,en;q=0.9"
    }

    for attempt in range(2):

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=15
            )

            response.raise_for_status()

            return response.text

        except Exception as e:

            print(
                f"Attempt {attempt + 1}/2 failed: {url}"
            )

            if attempt < 1:
                time.sleep(1)
            else:
                raise e
            

def process_row(index, supplier):
    try:

        # --------------------------------
        # Empty supplier
        # --------------------------------

        if pd.isna(supplier):
            return index, "", "NO", "", ""

        # --------------------------------
        # Manual price
        # --------------------------------

        if isinstance(supplier, (int, float)):

            price = float(supplier)

            quantity = df.loc[index, "Quantity"]

            if pd.isna(quantity):
                quantity = 1

            total_price = int(
                price * float(quantity)
            )

            return (
                index,
                "",
                "OK",
                int(price),
                total_price
            )

        # --------------------------------
        # Supplier URL / local HTML file
        # --------------------------------

        supplier = str(supplier).strip()

        if supplier.startswith(("http://", "https://")):

            html = get_page(supplier)

        else:

            with open(
                supplier,
                "r",
                encoding="utf-8"
            ) as f:

                html = f.read()

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # IMPORTANT:
        # Don't remove script/style if find_price() might need them.
        # Your current price scrapers don't appear to need them.
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        match = find_price(
            str(supplier),
            soup
        )

        if match:
            price = match[0]
            currency = match[1]

            # Persian numbers -> English
            price = price.translate(
                str.maketrans(
                    "۰۱۲۳۴۵۶۷۸۹",
                    "0123456789"
                )
            )

            price = price.replace(",", "").replace("٬", "")

            price = float(price)

            # Convert Toman -> Rial
            if currency == "تومان":
                price *= 10

            price = int(price)

            quantity = df.loc[index, "Quantity"]

            if pd.isna(quantity):
                quantity = 1

            total_price = int(price * float(quantity))

            return (
                index,
                text,
                "OK",
                price,
                total_price
            )

        return index, text, "NO", "", ""

    except Exception as e:

        print(f"Error processing {supplier}: {e}")

        return (
            index,
            f"ERROR: {e}",
            "ERROR",
            "",
            ""
        )


# --------------------------------
# PROCESS URLS IN PARALLEL
# --------------------------------

results = [None] * len(df)

# Start with 10 workers.
# You can try 15 or 20 if the websites allow it.
MAX_WORKERS = 10

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

    futures = [
        executor.submit(
            process_row,
            index,
            supplier
        )
        for index, supplier in enumerate(df["Supplier"])
    ]

    for future in tqdm(
        as_completed(futures),
        total=len(futures),
        desc="Scraping sites",
        unit="site"
    ):

        result = future.result()

        index = result[0]

        results[index] = result

# --------------------------------
# Restore original Excel order
# --------------------------------

contents = []
status = []
prices = []
total_prices = []

for result in results:

    index, content, stat, price, total_price = result

    contents.append(content)
    status.append(stat)
    prices.append(price)
    total_prices.append(total_price)

# Add columns
# df["Content"] = contents   # Don't save this column
df["Status"] = status
df["Price"] = prices
df["Total Price"] = total_prices

# Save Excel
df.to_excel(OUTPUT_EXCEL, index=False)



# Open workbook
wb = load_workbook(OUTPUT_EXCEL)
ws = wb.active



# -------------------------------
# Make Link clickable
# -------------------------------

supplier_col = None

for cell in ws[1]:

    if cell.value == "Supplier":
        supplier_col = cell.column
        break


if supplier_col:

    for row in range(2, ws.max_row + 1):

        cell = ws.cell(row=row, column=supplier_col)

        if cell.value:

            cell.hyperlink = str(cell.value)
            cell.style = "Hyperlink"



# -------------------------------
# Color Status column only
# -------------------------------

status_col = None

for cell in ws[1]:
    if cell.value == "Status":
        status_col = cell.column
        break

green_fill = PatternFill(
    start_color="C6EFCE",
    end_color="C6EFCE",
    fill_type="solid"
)

red_fill = PatternFill(
    start_color="FFC7CE",
    end_color="FFC7CE",
    fill_type="solid"
)

if status_col:
    for row in range(2, ws.max_row + 1):

        status_cell = ws.cell(row=row, column=status_col)

        if status_cell.value == "OK":
            status_cell.fill = green_fill

        elif status_cell.value in ["NO", "ERROR"]:
            status_cell.fill = red_fill

# -------------------------------
# Color supplier column by website
# -------------------------------

from urllib.parse import urlparse

site_colors = {}

colors = [
    "D9D2E9",  # Purple
    "CFE2F3",  # Light Blue
    "FCE5CD",  # Orange
    "FFF2CC",  # Yellow
    "D0E0E3",  # Gray Blue
    "EAD1DC",  # Pink Purple
    "B6D7A8",  # Light Green
    "F4CCCC",  # Soft Pink
    "C9DAF8",  # Sky Blue
    "FFD966",  # Gold
    "B4A7D6",  # Violet
    "A2C4C9"   # Teal
]

if supplier_col:

    color_index = 0

    for row in range(2, ws.max_row + 1):

        supplier_cell = ws.cell(row=row, column=supplier_col)

        if supplier_cell.value:

            try:
                domain = urlparse(str(supplier_cell.value)).netloc

                # remove www.
                domain = domain.replace("www.", "")

                if domain not in site_colors:

                    site_colors[domain] = PatternFill(
                        start_color=colors[color_index % len(colors)],
                        end_color=colors[color_index % len(colors)],
                        fill_type="solid"
                    )

                    color_index += 1


                # Color only supplier cell
                supplier_cell.fill = site_colors[domain]

            except:
                pass
# -------------------------------
# Add Grand Total
# -------------------------------

total_col = None

for cell in ws[1]:

    if cell.value == "Total Price":
        total_col = cell.column
        break



if total_col:

    # --------------------------------
    # Calculate Grand Total
    # --------------------------------

    grand_total = 0

    for row in range(2, ws.max_row + 1):

        value = ws.cell(
            row=row,
            column=total_col
        ).value

        if value is not None:

            try:
                grand_total += float(value)
            except (ValueError, TypeError):
                pass

    # --------------------------------
    # PRICE HISTORY
    # --------------------------------

    previous_total = None

    # Read previous run
    if os.path.exists(HISTORY_EXCEL):

        history_wb = load_workbook(HISTORY_EXCEL)
        history_ws = history_wb.active

        if history_ws.max_row >= 2:

            previous_total = history_ws.cell(
                row=history_ws.max_row,
                column=2
            ).value

    else:

        history_wb = Workbook()

        history_ws = history_wb.active

        history_ws.title = "Price History"

        history_ws.append([
            "Date / Time",
            "Grand Total",
            "Price Change %"
        ])

    # --------------------------------
    # Add Grand Total to output.xlsx
    # --------------------------------

    last_row = ws.max_row + 1

    ws.cell(
        row=last_row,
        column=total_col - 1
    ).value = "Grand Total"

    ws.cell(
        row=last_row,
        column=total_col
    ).value = grand_total

    # --------------------------------
    # Previous Total + Difference
    # --------------------------------

    if previous_total is not None:

        previous_row = last_row + 1

        ws.cell(
            row=previous_row,
            column=total_col - 1
        ).value = "Previous Total"

        ws.cell(
            row=previous_row,
            column=total_col
        ).value = previous_total

        difference = (
            grand_total -
            float(previous_total)
        )

        difference_row = last_row + 2

        ws.cell(
            row=difference_row,
            column=total_col - 1
        ).value = "Difference"

        ws.cell(
            row=difference_row,
            column=total_col
        ).value = difference

        ws.cell(
            row=difference_row,
            column=total_col
        ).number_format = '#,##0;[Red]-#,##0'

    # --------------------------------
    # Save ONE history entry
    # --------------------------------

# --------------------------------
# Save current run to history
# --------------------------------

    run_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Find the last real history row
    last_history_row = 1

    for row in range(history_ws.max_row, 1, -1):

        if (
            history_ws.cell(row=row, column=1).value is not None
            or
            history_ws.cell(row=row, column=2).value is not None
        ):
            last_history_row = row
            break

    # Add new record directly after the last real record
    new_row = last_history_row + 1

    history_ws.cell(
        row=new_row,
        column=1
    ).value = run_time

    history_ws.cell(
        row=new_row,
        column=2
    ).value = grand_total

    history_ws.cell(
        row=new_row,
        column=2
    ).number_format = '#,##0'

    # --------------------------------
    # Calculate Price Change %
    # --------------------------------

    percentage_change = None

    if previous_total is not None:
        try:
            previous_total_float = float(previous_total)

            if previous_total_float != 0:
                percentage_change = (
                    (grand_total - previous_total_float)
                    / previous_total_float
                )
        except (ValueError, TypeError):
            percentage_change = None


    # Save percentage in Column C
    history_ws.cell(
        row=new_row,
        column=3
    ).value = percentage_change

    history_ws.cell(
        row=new_row,
        column=3
    ).number_format = '0.00%'



    history_ws.column_dimensions["A"].width = 22
    history_ws.column_dimensions["B"].width = 20
    history_ws.column_dimensions["C"].width = 18

    history_wb.save(HISTORY_EXCEL)

    print(f"History saved: {HISTORY_EXCEL}")
# -------------------------------
# Format Price columns with comma
# -------------------------------

price_col = None
total_price_col = None

for cell in ws[1]:

    if cell.value == "Price":
        price_col = cell.column

    if cell.value == "Total Price":
        total_price_col = cell.column


if price_col:

    for row in range(2, ws.max_row + 1):
        ws.cell(row=row, column=price_col).number_format = '#,##0'


if total_price_col:

    for row in range(2, ws.max_row + 1):
        ws.cell(row=row, column=total_price_col).number_format = '#,##0'


# -------------------------------
# Auto width for Price columns
# -------------------------------

if price_col:
    max_length = 0

    for row in range(1, ws.max_row + 1):
        value = ws.cell(row=row, column=price_col).value

        if value is not None:
            # Format as comma-separated number
            if isinstance(value, (int, float)):
                text = f"{int(value):,}"
            else:
                text = str(value)

            max_length = max(max_length, len(text))

    ws.column_dimensions[
        ws.cell(row=1, column=price_col).column_letter
    ].width = max_length + 2


if total_price_col:
    max_length = 0

    for row in range(1, ws.max_row + 1):
        value = ws.cell(row=row, column=total_price_col).value

        if value is not None:
            if isinstance(value, (int, float)):
                text = f"{int(value):,}"
            else:
                text = str(value)

            max_length = max(max_length, len(text))

    ws.column_dimensions[
        ws.cell(row=1, column=total_price_col).column_letter
    ].width = max_length + 2


# Save final workbook
wb.save(OUTPUT_EXCEL)


print(f"Done! Output saved to {OUTPUT_EXCEL}")



# -------------------------------
# Auto open Excel
# -------------------------------

try:

    if platform.system() == "Windows":

        os.startfile(OUTPUT_EXCEL)


    elif platform.system() == "Darwin":

        subprocess.call(["open", OUTPUT_EXCEL])


    else:

        subprocess.call(["xdg-open", OUTPUT_EXCEL])


except Exception as e:

    print(f"Could not open Excel file automatically: {e}")