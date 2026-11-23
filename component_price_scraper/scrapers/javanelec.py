import re


def get_price(soup):
 
    # https://www.javanelec.com/ style

    for element in soup.find_all("div", class_="flex-align-base"):

        txt = element.get_text(" ", strip=True)

        m = re.search(
            r'([\d۰-۹,٬]+)\s*(ریال|تومان)',
            txt
        )

        if m:
            return m.group(1), m.group(2)
    


    return None