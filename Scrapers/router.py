"""Backward-compatible router; use ``component_price_scraper`` in new code."""

from component_price_scraper.scrapers.router import SCRAPERS, find_price, register_scraper

__all__ = ["SCRAPERS", "find_price", "register_scraper"]
