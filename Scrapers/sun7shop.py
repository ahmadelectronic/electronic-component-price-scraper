import re


def get_price(soup):

    # sun7shop.ir
    element = soup.select_one(
        "div.price.single_price .woocommerce-Price-amount"
    )

    if not element:
        return None

    text = element.get_text(" ", strip=True)

    match = re.search(
        r"[\d۰-۹][\d۰-۹,٬.]*",
        text
    )

    if not match:
        return None

    price = match.group(0)

    if "تومان" in text:
        return price, "تومان"

    if "ریال" in text:
        return price, "ریال"

    return None