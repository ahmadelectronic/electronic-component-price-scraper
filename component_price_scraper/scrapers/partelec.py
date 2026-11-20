import re


def get_price(soup):
    # https://partelec.ir/

    element = soup.select_one(
        "p.price > span.woocommerce-Price-amount"
    )

    if element:

        txt = element.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)',
            txt
        )

        if m:

            currency = "تومان"

            if "ریال" in txt:
                currency = "ریال"

            return m.group(1), currency
        


    return None