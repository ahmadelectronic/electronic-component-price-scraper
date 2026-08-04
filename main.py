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
        if "ریال" in text or "تومان" in text:

            status.append("OK")


            # First, try to get the price from the Twitter meta tag
            match = None

            meta_price = soup.find("meta", attrs={"name": "twitter:data1"})

            if meta_price:
                price_text = meta_price.get("content", "")
                price_text = price_text.replace("\xa0", " ")

                match = re.search(r'([\d۰-۹,٬,]+)\s*(ریال|تومان)',
                    price_text
                )

            # If not found, search the page text as before
            if not match:
                match = re.search(
                    r'([\d۰-۹]{1,3}(?:[,٬][\d۰-۹]{3})*|[\d۰-۹]+)\s*(ریال|تومان)',
                    text
                )

            if match:

                # Extract price and currency
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