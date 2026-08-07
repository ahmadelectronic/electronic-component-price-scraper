import re


def get_price(soup):
    # https://roboeq.ir/ style

    for span in soup.find_all(
        "span",
        class_=lambda c: c and "rial-symbol" in c
    ):

        price_text = span.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)',
            price_text
        )

        if m:
            return m.group(1), "ریال"



    return None