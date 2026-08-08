import re


def get_price(soup):
    # WooCommerce single-product price
    selectors = [
        "p.price > span.woocommerce-Price-amount",
        ".elementor-widget-woocommerce-product-price p.price span.woocommerce-Price-amount",
        "div.elementor-widget-woocommerce-product-price p.price span.woocommerce-Price-amount",
    ]

    for selector in selectors:
        element = soup.select_one(selector)

        if not element:
            continue

        txt = element.get_text(" ", strip=True)

        # Make sure this is an actual product price
        # and not a zero/cart/installment price.
        m = re.search(r'([\d۰-۹,٬.]+)\s*(تومان|ریال)', txt)

        if m:
            return m.group(1), m.group(2)

    return None