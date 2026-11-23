import re


def get_price(soup):

    element = soup.find(
        "meta",
        property="product:price:amount"
    )

    if element:

        price = element.get("content")

        currency = "ریال"

        currency_tag = soup.find(
            "meta",
            property="product:price:currency"
        )

        if currency_tag:

            cur = currency_tag.get(
                "content",
                ""
            ).upper()

            if cur == "IRT":
                currency = "تومان"

            elif cur == "IRR":
                currency = "ریال"

        return price, currency

    return None