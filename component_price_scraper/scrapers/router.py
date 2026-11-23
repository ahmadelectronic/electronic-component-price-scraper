"""Resolve supplier domains to their site-specific price extractors."""

from importlib import import_module
from collections.abc import Callable
from urllib.parse import urlparse


# Keep each store's extraction rules isolated; adding a store only requires
# adding one domain/module pair here and one extractor module beside this file.
SCRAPER_MODULES = {
    "electronic724.com": "electronic724",
    "eshop.eca.ir": "eca",
    "lionelectronic.ir": "lionelectronic",
    "shop.qom-elec.ir": "qom_elec",
    "bahar-enclosure.ir": "bahar_enclosure",
    "buybestelectronic.com": "buybestelectronic",
    "javanelec.com": "javanelec",
    "roboeq.ir": "roboeq",
    "thecaferobot.com": "thecaferobot",
    "partelec.ir": "partelec",
    "iran-module.ir": "iran_module",
    "skytech.ir": "skytech",
    "kavirelectronic.ir": "kavirelectronic",
    "esys.ir": "esys",
    "shop.sisoog.com": "sisoog",
    "jamtronic.com": "jamtronic",
    "shop.ideaelec.com": "ideaelec",
    "voltatech.ir": "voltatech",
    "microele.com": "microele",
    "arefelectronic.com": "arefelectronic",
    "efarvahar.ir": "efarvahar",
    "nemonehsaz.com": "nemonehsaz",
    "ariaebox.com": "ariabox",
    "elecohm.com": "elecohm",
    "daneshjookit.com": "daneshjookit",
    "sparkeyelec.ir": "sparkeyelec",
    "zagroselec.ir": "zagroselec",
    "chehrehelec.com": "chehrehelec",
    "sun7shop.ir": "sun7shop",
}


SCRAPERS: dict[str, Callable] = {
    domain: import_module(f".{module}", __package__).get_price
    for domain, module in SCRAPER_MODULES.items()
}


def register_scraper(domain: str, extractor: Callable, *, replace: bool = False) -> None:
    """Register a custom supplier extractor at runtime.

    ``extractor`` receives a BeautifulSoup object and returns ``(price, currency)``
    or ``None``. Existing built-in domains require ``replace=True`` to override.
    """
    host = str(domain).strip().lower().removeprefix("www.").rstrip(".")
    if not host or not callable(extractor):
        raise ValueError("A valid domain and callable extractor are required")
    if host in SCRAPERS and not replace:
        raise ValueError(f"A scraper is already registered for {host!r}")
    SCRAPERS[host] = extractor


def find_price(url: str, soup):
    """Return ``(raw_price, currency)`` for a supported supplier URL."""
    host = (urlparse(str(url)).hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]

    # Longest matches first, so specific subdomains win over parent domains.
    for domain, scraper in sorted(SCRAPERS.items(), key=lambda item: len(item[0]), reverse=True):
        if host == domain or host.endswith(f".{domain}"):
            return scraper(soup)
    return None
