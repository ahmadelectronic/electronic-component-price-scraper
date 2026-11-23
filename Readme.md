# Electronic Component Price Scraper

A reusable Python library and command-line tool for collecting electronic-component prices from supplier websites, calculating quantity totals, and producing Excel reports with price history.

## What's changed

The original application logic has been separated into a reusable package. `main.py` is now only an entry point; scraping, configuration, concurrency, Excel formatting, and history tracking live in `component_price_scraper/`. The 29 supplier-specific extractors are retained inside `component_price_scraper/scrapers/`.

## Install

## Python Environment (Recommended)

It is recommended to use a Python virtual environment to keep project dependencies isolated.

### Windows

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source venv/Scripts/activate
```

### Linux / macOS

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### Install Dependencies

After activating the environment, install the required packages:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Verify Python Environment

Check your Python version:

```bash
python --version
```

Check installed dependencies:

```bash
python -m pip list
```

### Deactivate Environment

When you finish working with the project:

```bash
deactivate
```

**Note:** Activate the virtual environment before running the application or executing tests. The `.venv` directory should not be committed to version control.

## Run the Excel monitor

Keep `database.xlsx` in the working directory. It must contain `Supplier` and `Quantity` columns. A supplier can be a supported product URL, a path to a local HTML file, or a manually entered numeric price.

```bash
python main.py
```

Or use the installed command:

```bash
component-price-scraper --input database.xlsx --output output.xlsx --history price_history.xlsx
```

Useful options:

```bash
python main.py --workers 15 --timeout 20 --no-open
```

The generated report includes `Status`, `Price`, and `Total Price`, supplier links, status/domain coloring, a grand total, and the previous-run comparison. Prices detected in toman are converted to rial, matching the previous application behavior.

## Use as a library

```python
from component_price_scraper import PriceMonitor, ScraperConfig

config = ScraperConfig(
    input_file="database.xlsx",
    output_file="output.xlsx",
    history_file="price_history.xlsx",
    max_workers=10,
    auto_open=False,
)

summary = PriceMonitor(config).run()
print(summary.grand_total)
```

For one URL, without running the Excel workflow:

```python
from component_price_scraper import PriceScraper

result = PriceScraper().scrape(
    "https://www.electronic724.com/product/example",
    quantity=4,
)

print(result.status, result.price, result.total_price)
```

HTML already downloaded can be parsed without making a network request:

```python
result = PriceScraper().scrape_html(url, html, quantity=2)
```

## Add another supplier

You can register an extractor at runtime without editing the package:

```python
from component_price_scraper import register_scraper


def my_store_price(soup):
    element = soup.select_one(".product-price")
    if not element:
        return None
    return element.get_text(strip=True), "تومان"


register_scraper("my-store.example", my_store_price)
```

An extractor receives a BeautifulSoup object and returns `(price, currency)` or `None`. To permanently add a built-in supplier, create a module under `component_price_scraper/scrapers/` and add its domain/module pair to `SCRAPER_MODULES` in `router.py`.

The shared library converts Persian/Arabic digits, applies currency conversion, quantity calculations, retries, and error handling for every extractor.

## Package layout

```text
component_price_scraper/
├── __init__.py
├── config.py
├── models.py
├── scraper.py
├── monitor.py
├── report.py
├── cli.py
└── scrapers/
    ├── router.py
    └── [29 supplier-specific extractors]
main.py
pyproject.toml
requirements.txt
tests/
```

Run the automated tests with:

```bash
python -m unittest discover -s tests -v
```

The old `scrapers.router` import remains as a compatibility shim. New code should import from `component_price_scraper`.
