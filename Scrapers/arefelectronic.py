import re


def get_price(soup):

    # https://arefelectronic.com/ style
    # Current price is inside <ins>
    element = soup.select_one(
        "p.price ins .woocommerce-Price-amount"
    )

    if element:

        txt = element.get_text(" ", strip=True)

        m = re.search(
            r'(ریال|تومان)\s*([\d۰-۹,٬.]+)',
            txt
        )

        if m:
            return m.group(2), m.group(1)

        # Handles price where number comes first
        m = re.search(
            r'([\d۰-۹,٬.]+)\s*(ریال|تومان)',
            txt
        )

        if m:
            return m.group(1), m.group(2)

    return None