"""Compatibility imports for older code using ``scrapers.router``."""

from component_price_scraper.scrapers.router import SCRAPERS, find_price, register_scraper

__all__ = ["SCRAPERS", "find_price", "register_scraper"]
