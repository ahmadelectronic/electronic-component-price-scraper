import re


def get_price(soup):
    # https://www.esys.ir/ style

    element = soup.select_one(
        "#ctl00_ContentPlaceHolder1_lbPrice"
    )

    if element:

        txt = element.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)\s*(ریال|تومان)',
            txt
        )

        if m:
            return m.group(1), m.group(2)



    return None