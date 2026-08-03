import os
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Input and output Excel files
INPUT_EXCEL = "database.xlsx"
OUTPUT_EXCEL = "output.xlsx"

# Read Excel file
df = pd.read_excel(INPUT_EXCEL)

# Remove extra spaces from column names
df.columns = df.columns.str.strip()

# Check if Link column exists
if "Link" not in df.columns:
    raise ValueError(f"Excel file must contain a 'Link' column. Found columns: {list(df.columns)}")

contents = []
status = []
prices = []

for link in df["Link"]:
    try:
        if pd.isna(link):
            contents.append("")
            status.append("NO")
            prices.append("")
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

        # Save extracted text
        contents.append(text)

        # Search for currency
        if "ریال" in text or "تومان" in text:
            status.append("OK")

            # Extract the first price before ریال or تومان
            match = re.search(
                r'([\d۰-۹]{1,3}(?:[,٬][\d۰-۹]{3})*|[\d۰-۹]+)\s*(?:ریال|تومان)',
                text
            )

            if match:
                prices.append(match.group(1))
            else:
                prices.append("")

        else:
            status.append("NO")
            prices.append("")

    except Exception as e:
        print(f"Error processing {link}: {e}")
        contents.append(f"ERROR: {e}")
        status.append("ERROR")
        prices.append("")

# Add new columns to DataFrame
df["Content"] = contents
df["Status"] = status
df["Price"] = prices

# Save results
df.to_excel(OUTPUT_EXCEL, index=False)

print(f"Done! Output saved to {OUTPUT_EXCEL}")