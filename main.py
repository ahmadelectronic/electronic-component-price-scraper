import os
import re
import platform
import subprocess
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from urllib.parse import urlparse


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


        # Read HTML
        if str(link).startswith(("http://", "https://")):

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }

            response = requests.get(
                link,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            html = response.text


        else:

            with open(link, "r", encoding="utf-8") as f:
                html = f.read()



        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")


        for tag in soup(["script", "style"]):
            tag.decompose()


        text = soup.get_text(separator=" ", strip=True)


        contents.append(text)



        # Search price
        meta_price_check = soup.find("meta", attrs={"name": "price"})

        if "ریال" in text or "تومان" in text or meta_price_check:

            status.append("OK")


            # First, try to get price from meta tags
            match = None

            # twitter:data1
            meta_price = soup.find("meta", attrs={"name": "twitter:data1"})

            # <meta name="price" content="683000">
            price_meta = soup.find("meta", attrs={"name": "price"})

            # <span itemprop="price" content="11477000">
            itemprop_price = soup.find(attrs={"itemprop": "price"})

            #suport <div class="current-price"><span class="price" itemprop="price" content="11477000">11,477,000 ریال</span>
            if price_meta:

                price_text = price_meta.get("content", "")
                match = (price_text, "ریال")

            elif itemprop_price:

                # First try the content attribute
                price_text = itemprop_price.get("content", "")

                if not price_text:
                    # Otherwise use the visible text
                    price_text = itemprop_price.get_text(" ", strip=True)

                # Detect currency
                if "تومان" in price_text:
                    currency = "تومان"
                else:
                    currency = "ریال"

                numbers = re.search(r'[\d۰-۹,٬]+', price_text)

                if numbers:
                    match = (numbers.group(), currency)

            elif meta_price:

                price_text = meta_price.get("content", "")
                price_text = price_text.replace("\xa0", " ")

                match = re.search(
                    r'([\d۰-۹,٬]+)\s*(ریال|تومان)',
                    price_text
                )

            # If not found, search the page text as before
            if not match:
                match = re.search(
                    r'([\d۰-۹]{1,3}(?:[,٬][\d۰-۹]{3})*|[\d۰-۹]+)\s*(ریال|تومان)',
                    text
                )

            if match:

                if isinstance(match, tuple):
                    price = match[0]
                    currency = match[1]
                else:
                    price = match.group(1)
                    currency = match.group(2)

                # Convert Persian digits to English
                price = price.translate(
                    str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
                )

                # Remove thousand separators
                price = price.replace(",", "").replace("٬", "")

                price = float(price)

                # Convert Toman to Rial
                if currency == "تومان":
                    price *= 10

                # Save price as integer (Rial)
                prices.append(int(price))

                # Read quantity
                quantity = df.loc[index, "Quantity"]

                if pd.isna(quantity):
                    quantity = 1

                # Calculate total price
                total_prices.append(int(price * float(quantity)))


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
# Color Link column by website
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

if link_col:

    color_index = 0

    for row in range(2, ws.max_row + 1):

        link_cell = ws.cell(row=row, column=link_col)

        if link_cell.value:

            try:
                domain = urlparse(str(link_cell.value)).netloc

                # remove www.
                domain = domain.replace("www.", "")

                if domain not in site_colors:

                    site_colors[domain] = PatternFill(
                        start_color=colors[color_index % len(colors)],
                        end_color=colors[color_index % len(colors)],
                        fill_type="solid"
                    )

                    color_index += 1


                # Color only Link cell
                link_cell.fill = site_colors[domain]

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