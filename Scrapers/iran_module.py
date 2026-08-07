import re


def get_price(soup):
    # https://www.iran-module.ir/ style

    element = soup.select_one(
        "span.productPrice[itemprop='price']"
    )

    if element:

        txt = element.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)\s*(ریال|تومان)',
            txt
        )

        if m:
            return m.group(1), m.group(2)


        # content="807000" + TMN currency
        price = element.get("content")

        if price:

            currency = "ریال"

            currency_tag = soup.select_one(
                "meta[itemprop='priceCurrency']"
            )

            if currency_tag:

                cur = currency_tag.get(
                    "content",
                    ""
                ).upper()

                if cur == "TMN":
                    currency = "تومان"

                elif cur == "IRR":
                    currency = "ریال"


            return price, currency



    return None