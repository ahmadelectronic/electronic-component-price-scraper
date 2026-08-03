import os
import re
import platform
import subprocess
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openpyxl import load_workbook

# Input and output Excel files
INPUT_EXCEL = "database.xlsx"
OUTPUT_EXCEL = "output.xlsx"

# Read Excel file
df = pd.read_excel(INPUT_EXCEL)

# Remove extra spaces from column names
df.columns = df.columns.str.strip()

# Check required columns
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

        # Read HTML from URL
        if str(link).startswith(("http://", "https://")):
            response = requests.get(link, timeout=30)
            response.raise_for_status()
            html = response.text

        # Read local HTML file
        else:
            with open(link, "r", encoding="utf-8") as f:
                html = f.read()

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style tags
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Extract visible text
        text = soup.get_text(separator=" ", strip=True)

        contents.append(text)

        # Search currency
        if "ریال" in text or "تومان" in text:
            status.append("OK")

            # Find price
            match = re.search(
                r'([\d۰-۹]{1,3}(?:[,٬][\d۰-۹]{3})*|[\d۰-۹]+)\s*(?:ریال|تومان)',
                text
            )

            if match:
                price = match.group(1)

                # Convert Persian numbers and remove separators
                price = price.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
                price = price.replace(",", "").replace("٬", "")

                prices.append(price)

                # Get quantity
                quantity = df.loc[index, "Quantity"]

                if pd.isna(quantity):
                    quantity = 1

                # Calculate total price
                total = float(price) * float(quantity)
                total_prices.append(total)

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


# Add new columns
df["Content"] = contents
df["Status"] = status
df["Price"] = prices
df["Total Price"] = total_prices


# Save DataFrame
df.to_excel(OUTPUT_EXCEL, index=False)


# -------------------------------
# Edit Excel file
# -------------------------------
wb = load_workbook(OUTPUT_EXCEL)
ws = wb.active


# -------------------------------
# Make Link column clickable
# -------------------------------
link_col = None

for cell in ws[1]:
    if cell.value == "Link":
        link_col = cell.column
        break

if link_col:
    for row in range(2, ws.max_row + 1):
        cell = ws.cell(row=row, column=link_col)
        link = cell.value

        if link:
            cell.hyperlink = str(link)
            cell.style = "Hyperlink"


# -------------------------------
# Add Grand Total row
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

    # Add total at bottom
    last_row = ws.max_row + 1

    ws.cell(row=last_row, column=total_col - 1).value = "Grand Total"
    ws.cell(row=last_row, column=total_col).value = grand_total


# Save workbook
wb.save(OUTPUT_EXCEL)

print(f"Done! Output saved to {OUTPUT_EXCEL}")


# -------------------------------
# Automatically open output.xlsx
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