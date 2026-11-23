import re


def get_price(soup):
    # https://lionelectronic.ir/ style

    for element in soup.find_all(
        "div",
        class_=lambda c: c and "price-row" in c
    ):

        txt = element.parent.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)\s*(ریال|تومان)',
            txt
        )

        if m:
            return m.group(1), m.group(2)


    return None