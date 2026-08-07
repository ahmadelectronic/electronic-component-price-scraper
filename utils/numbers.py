def clean_price(price):

    price = str(price)

    price = price.translate(
        str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    )

    price = price.replace(",", "")
    price = price.replace("٬", "")

    return float(price)


def toman_to_rial(price, currency):

    currency = str(currency).strip()

    if "تومان" in currency:
        return price * 10

    return price