import re


def get_price(soup):
    # https://shop.sisoog.com/ style

    element = soup.select_one(
        "p.price .woocommerce-Price-amount"
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