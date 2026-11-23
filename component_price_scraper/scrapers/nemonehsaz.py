import re


def get_price(soup, text=None):

    # https://nemonehsaz.com/ style

    element = soup.select_one(
        "li.product-prices"
    )

    if element:

        txt = element.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)\s*(ریال|تومان)',
            txt
        )

        if m:
            return m.group(1), m.group(2)

    return None