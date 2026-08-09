import re


def get_price(soup):

    print("THECAFEROBOT SCRAPER CALLED")

    # 1. Magento final price
    element = soup.find(
        "span",
        attrs={"data-price-type": "finalPrice"}
    )

    if element:

        amount = element.get("data-price-amount")

        print("FINAL PRICE ELEMENT FOUND:", amount)

        if amount:
            return amount, "تومان"

    # 2. Meta price
    meta = soup.find(
        "meta",
        attrs={"property": "product:price:amount"}
    )

    if meta:

        amount = meta.get("content")

        print("META PRICE FOUND:", amount)

        if amount:
            return amount, "تومان"

    # 3. Visible price fallback
    element = soup.select_one(
        ".price"
    )

    if element:

        text = element.get_text(" ", strip=True)

        print("VISIBLE PRICE:", text)

        match = re.search(
            r"[\d۰-۹,٬.]+",
            text
        )

        if match:
            return match.group(0), "تومان"

    print("THECAFEROBOT: PRICE NOT FOUND")

    return None