
import re


def get_price(soup):

    # chehrehelec.com
    element = soup.select_one(
        ".price-group .product-price"
    )

    if not element:
        return None

    text = element.get_text(" ", strip=True)

    # Find price
    match = re.search(
        r"[\d۰-۹][\d۰-۹,٬.]*",
        text
    )

    if not match:
        return None

    price = match.group(0)

    # Find currency
    if "تومان" in text:
        return price, "تومان"

    if "ریال" in text:
        return price, "ریال"

    return None
