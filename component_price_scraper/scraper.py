"""Single-item scraping API."""

from __future__ import annotations

import logging
import math
import numbers
import re
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import ScraperConfig
from .models import ScrapeResult
from .scrapers.router import find_price


logger = logging.getLogger(__name__)
_DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def normalize_price(value: Any) -> int:
    """Convert Persian/Arabic digits and common separators to an integer."""
    text = str(value).translate(_DIGIT_TRANSLATION).strip()
    text = text.replace("٬", "").replace(",", "").replace(" ", "")
    text = re.sub(r"[^0-9.\-]", "", text)

    if not text or text in {"-", ".", "-."}:
        raise ValueError(f"Invalid price value: {value!r}")

    # Multiple dots, or a single dot followed by exactly three digits, are
    # commonly used as thousands separators on supplier websites.
    if text.count(".") > 1:
        text = text.replace(".", "")
    elif "." in text and len(text.rsplit(".", 1)[1]) == 3:
        text = text.replace(".", "")

    try:
        return int(Decimal(text))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid price value: {value!r}") from exc


def _is_missing(value: Any) -> bool:
    if value is None or type(value).__name__ in {"NAType", "NaTType"}:
        return True
    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def _quantity(value: Any) -> Decimal:
    if _is_missing(value) or value == "":
        return Decimal("1")
    try:
        quantity = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid quantity: {value!r}") from exc
    if not quantity.is_finite():
        raise ValueError(f"Invalid quantity: {value!r}")
    return quantity


class PriceScraper:
    """Fetch supplier pages and extract prices using the built-in registry."""

    def __init__(self, config: ScraperConfig | None = None) -> None:
        self.config = config or ScraperConfig()

    def scrape(self, supplier: Any, quantity: Any = 1) -> ScrapeResult:
        """Scrape one URL/local HTML file, or calculate a manually entered price."""
        if _is_missing(supplier):
            return ScrapeResult(status="NO")

        try:
            qty = _quantity(quantity)

            if isinstance(supplier, (numbers.Real, Decimal)) and not isinstance(supplier, bool):
                price = normalize_price(supplier)
                return ScrapeResult("OK", price, int(Decimal(price) * qty))

            source = str(supplier).strip()
            if source.startswith(("http://", "https://")):
                html = self._fetch(source)
            else:
                html = Path(source).expanduser().read_text(encoding="utf-8")

            return self.scrape_html(source, html, quantity=qty)

        except Exception as exc:
            logger.warning("Could not process supplier %r: %s", supplier, exc)
            return ScrapeResult(status="ERROR", error=str(exc), content=f"ERROR: {exc}")

    def scrape_html(self, url: str, html: str, quantity: Any = 1) -> ScrapeResult:
        """Extract a price from HTML already in memory (useful for tests/offline use)."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            match = find_price(url, soup)
            for tag in soup(["script", "style"]):
                tag.decompose()
            content = soup.get_text(separator=" ", strip=True)

            if not match or len(match) < 2 or match[0] in (None, ""):
                return ScrapeResult(status="NO", content=content)

            raw_price, currency = match
            price = normalize_price(raw_price)
            if str(currency).strip() == "تومان":
                price *= 10

            qty = _quantity(quantity)
            return ScrapeResult(
                status="OK",
                price=price,
                total_price=int(Decimal(price) * qty),
                content=content,
            )
        except Exception as exc:
            logger.warning("Could not parse %s: %s", url, exc)
            return ScrapeResult(status="ERROR", error=str(exc), content=f"ERROR: {exc}")

    def _fetch(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.config.retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=self.config.headers,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("Request attempt %s/%s failed for %s", attempt, self.config.retries, url)
                if attempt < self.config.retries and self.config.retry_delay:
                    time.sleep(self.config.retry_delay)

        assert last_error is not None
        raise last_error
