import re


def get_price(soup):
    # https://eshop.eca.ir/ style

    element = soup.select_one("span.current-price")

    if element:

        price_text = element.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)',
            price_text
        )

        if m:

            currency = "ریال"  # default

            # find currency next to price
            parent = element.find_parent(
                class_="price-wrapper"
            )

            if parent:

                currency_text = parent.get_text(
                    " ",
                    strip=True
                )

                if "تومان" in currency_text:
                    currency = "تومان"

                elif "ریال" in currency_text:
                    currency = "ریال"


            return m.group(1), currency



    return None