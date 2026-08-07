from urllib.parse import urlparse

from . import (
    electronic724,
    eca,
    lionelectronic,
    qom_elec,
    bahar_enclosure,
    buybestelectronic,
    javanelec,
    roboeq,
    thecaferobot,
    partelec,
    iran_module,
    skytech,
    kavirelectronic,
    esys,
    sisoog,
    jamtronic,
    ideaelec,
    voltatech,
    microele
)


SCRAPERS = {

    "electronic724.com": electronic724.get_price,

    "eshop.eca.ir": eca.get_price,

    "lionelectronic.ir": lionelectronic.get_price,

    "shop.qom-elec.ir": qom_elec.get_price,

    "bahar-enclosure.ir": bahar_enclosure.get_price,

    "buybestelectronic.com": buybestelectronic.get_price,

    "javanelec.com": javanelec.get_price,

    "roboeq.ir": roboeq.get_price,

    "thecaferobot.com": thecaferobot.get_price,

    "partelec.ir": partelec.get_price,

    "iran-module.ir": iran_module.get_price,

    "skytech.ir": skytech.get_price,

    "kavirelectronic.ir": kavirelectronic.get_price,

    "esys.ir": esys.get_price,

    "shop.sisoog.com": sisoog.get_price,

    "jamtronic.com": jamtronic.get_price,
    
    "shop.ideaelec.com": ideaelec.get_price,

    "voltatech.ir": voltatech.get_price,   

    "microele.com": microele.get_price,   
     
}


def find_price(url, soup):

    domain = urlparse(url).netloc

    domain = domain.replace(
        "www.",
        ""
    )


    for site, scraper in SCRAPERS.items():

        if domain.endswith(site):

            return scraper(soup)


    return None