import re


def get_price(soup):

    elements = soup.select(
        "span.px-01.font-weight-bold"
    )

    # Third element = current price
    if len(elements) < 3:
        return None

    element = elements[2]

    price = element.get_text(
        " ",
        strip=True
    )

    match = re.search(
        r"[\d۰-۹,٬.]+",
        price
    )

    if not match:
        return None

    # Find currency in the nearby parent
    parent = element.parent

    if parent:
        text = parent.get_text(
            " ",
            strip=True
        )

        if "تومان" in text:
            return match.group(0), "تومان"

        if "ریال" in text:
            return match.group(0), "ریال"

    # This site shows ریال
    return match.group(0), "ریال"