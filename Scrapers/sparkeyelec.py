import re


def get_price(soup):
    element = soup.select_one(
        "p.price span.woocommerce-Price-amount"
    )

    if not element:
        return None

    txt = element.get_text(" ", strip=True)

    # Example:
    # 618,420 تومان
    # 378,000 تومان
    # 29,000 ریال
    m = re.search(
        r'([\d۰-۹,٬.]+)\s*(ریال|تومان)',
        txt
    )

    if m:
        return m.group(1), m.group(2)

    # Currency before number
    # Example: تومان 618,420
    m = re.search(
        r'(ریال|تومان)\s*([\d۰-۹,٬.]+)',
        txt
    )

    if m:
        return m.group(2), m.group(1)

    return None