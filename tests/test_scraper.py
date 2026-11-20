import unittest

from component_price_scraper import PriceScraper, ScraperConfig, normalize_price, register_scraper
from component_price_scraper.scrapers.router import SCRAPERS, find_price


class PriceScraperTests(unittest.TestCase):
    def setUp(self):
        self.scraper = PriceScraper(ScraperConfig(retries=1, auto_open=False))

    def test_all_supplier_extractors_are_registered(self):
        self.assertEqual(len(SCRAPERS), 29)

    def test_persian_and_arabic_digits(self):
        self.assertEqual(normalize_price("۱۲۳٬۴۵۶"), 123456)
        self.assertEqual(normalize_price("١٢٣,٤٥٦"), 123456)

    def test_toman_is_converted_to_rial_and_quantity_applied(self):
        html = '''
            <html><head>
              <meta property="product:price:amount" content="125,000">
              <meta property="product:price:currency" content="IRT">
            </head><body><h1>Test component</h1></body></html>
        '''
        result = self.scraper.scrape_html("https://www.electronic724.com/item", html, 2)
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.price, 1_250_000)
        self.assertEqual(result.total_price, 2_500_000)

    def test_manual_price(self):
        result = self.scraper.scrape(150_000, 3)
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.price, 150_000)
        self.assertEqual(result.total_price, 450_000)

    def test_unknown_site_returns_no_price(self):
        from bs4 import BeautifulSoup
        result = find_price("https://unknown.example/product", BeautifulSoup("<p>no price</p>", "html.parser"))
        self.assertIsNone(result)

    def test_custom_scraper_can_be_registered(self):
        from bs4 import BeautifulSoup
        register_scraper("custom-store.example", lambda soup: ("123", "ریال"))
        try:
            result = find_price("https://www.custom-store.example/item", BeautifulSoup("<p>123</p>", "html.parser"))
            self.assertEqual(result, ("123", "ریال"))
        finally:
            SCRAPERS.pop("custom-store.example", None)

    def test_domain_matching_does_not_accept_fake_suffix(self):
        from bs4 import BeautifulSoup
        result = find_price("https://not-electronic724.com/item", BeautifulSoup(
            '<meta property="product:price:amount" content="10">', "html.parser"
        ))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
