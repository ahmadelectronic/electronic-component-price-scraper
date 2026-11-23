import re


def get_price(soup):
    # https://shop.qom-elec.ir/ style

    element = soup.find("div", id="setak-price-display")

    if element:

        txt = element.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬.]+)',
            txt
        )

        if m:

            currency = "ریال"   # default

            # SVG currency icon
            use = element.find("use")

            if use:

                href = (
                    use.get("href")
                    or use.get("xlink:href")
                    or ""
                ).lower()

                if "toman" in href:
                    currency = "تومان"

                elif "rial" in href:
                    currency = "ریال"


            return m.group(1), currency
    


    return None