import re


def get_price(soup):
    # https://kavirelectronic.ir/ style

    element = soup.select_one(
        "div.current-price span.price"
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