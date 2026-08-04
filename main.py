import os
import re
import platform
import subprocess
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# Input and output Excel files
INPUT_EXCEL = "database.xlsx"
OUTPUT_EXCEL = "output.xlsx"

# Read Excel file
df = pd.read_excel(INPUT_EXCEL)

df.columns = df.columns.str.strip()

if "Link" not in df.columns:
    raise ValueError(f"Excel file must contain 'Link' column. Found: {list(df.columns)}")

if "Quantity" not in df.columns:
    raise ValueError(f"Excel file must contain 'Quantity' column. Found: {list(df.columns)}")


contents = []
status = []
prices = []
total_prices = []

for index, link in enumerate(df["Link"]):
    try:
        if pd.isna(link):
            contents.append("")
            status.append("NO")
            prices.append("")
            total_prices.append("")
            continue

        if str(link).startswith(("http://", "https://")):
            response = requests.get(link, timeout=30)
            response.raise_for_status()
            html = response.text
        else:
            with open(link, "r", encoding="utf-8") as f:
                html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        contents.append(text)

        if "ریال" in text or "تومان" in text:
            status.append("OK")

            match = re.search(
                r'([\d۰-۹]{1,3}(?:[,٬][\d۰-۹]{3})*|[\d۰-۹]+)\s*(?:ریال|تومان)',
                text
            )

            if match:
                price = match.group(1)
                price = price.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
                price = price.replace(",", "").replace("٬", "")

                prices.append(price)

                quantity = df.loc[index, "Quantity"]

                if pd.isna(quantity):
                    quantity = 1

                total_prices.append(float(price) * float(quantity))

            else:
                prices.append("")
                total_prices.append("")

        else:
            status.append("NO")
            prices.append("")
            total_prices.append("")


    except Exception as e:
        print(f"Error processing {link}: {e}")
        contents.append(f"ERROR: {e}")
        status.append("ERROR")
        prices.append("")
        total_prices.append("")


# Add columns
df["Content"] = contents
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
link_col = None

for cell in ws[1]:
    if cell.value == "Link":
        link_col = cell.column
        break

if link_col:
    for row in range(2, ws.max_row + 1):
        cell = ws.cell(row=row, column=link_col)
        if cell.value:
            cell.hyperlink = str(cell.value)
            cell.style = "Hyperlink"


# -------------------------------
# Color rows by Status
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

        status_value = ws.cell(row=row, column=status_col).value

        if status_value == "OK":
            for col in range(1, ws.max_column + 1):
                ws.cell(row=row, column=col).fill = green_fill

        elif status_value in ["NO", "ERROR"]:
            for col in range(1, ws.max_column + 1):
                ws.cell(row=row, column=col).fill = red_fill



# -------------------------------
# Add Grand Total
# -------------------------------
total_col = None

for cell in ws[1]:
    if cell.value == "Total Price":
        total_col = cell.column
        break


if total_col:

    grand_total = 0

    for row in range(2, ws.max_row + 1):
        value = ws.cell(row=row, column=total_col).value

        if value:
            try:
                grand_total += float(value)
            except:
                pass


    last_row = ws.max_row + 1

    ws.cell(row=last_row, column=total_col - 1).value = "Grand Total"
    ws.cell(row=last_row, column=total_col).value = grand_total



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