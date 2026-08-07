import re


def get_price(soup):
   # https://jamtronic.com/ style

    element = soup.select_one(
        "div.elementor-widget-container p.price span.woocommerce-Price-amount"
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