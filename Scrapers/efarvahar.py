def get_price(soup, text=None):

    # https://efarvahar.ir/ style

    element = soup.find(
        "meta",
        property="product:price:amount"
    )

    if element:

        price = element.get("content")

        if not price:
            return None

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

            if cur in ("IRT", "TMN"):
                currency = "تومان"

            elif cur in ("IRR", "RLS"):
                currency = "ریال"

        return price, currency

    return None