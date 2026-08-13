# Supplier Price Scraper & Excel Price Monitor

A Python automation tool that collects product prices from supplier websites, processes the results, and generates a formatted Excel report with price calculations and historical tracking.

## Overview

This project is designed to automate supplier price collection from a list of URLs stored in an Excel database.

The application:

* Reads supplier URLs and quantities from `database.xlsx`
* Scrapes supplier webpages
* Extracts product prices using custom price scrapers
* Supports Persian numerals
* Converts prices from Toman to Rial when necessary
* Calculates the total price based on quantity
* Processes multiple websites concurrently for better performance
* Generates a formatted `output.xlsx` report
* Tracks previous totals and price changes
* Stores historical totals in `price_history.xlsx`
* Automatically opens the generated Excel file on Windows, macOS, and Linux

The main input and output files are defined as `database.xlsx`, `output.xlsx`, and `price_history.xlsx`.

## Features

### 🌐 Web Scraping

The project uses `requests` and `BeautifulSoup` to download and parse supplier webpages.

It supports both:

* HTTP/HTTPS URLs
* Local HTML files

The scraper also uses retry logic and request timeouts to handle temporary connection problems.

### 💰 Automatic Price Extraction

Prices are extracted through the project's custom scraper router:

```python
from scrapers.router import find_price
```

The extracted price is converted into a numeric value so it can be used for calculations.

### 🇮🇷 Persian Number Support

The application converts Persian digits into English digits before processing prices.

For example:

```text
۱۲۳۴۵۶
```

becomes:

```text
123456
```

It also removes comma and Persian thousands separators.

### 📦 Quantity-Based Calculation

Each supplier/product can have a quantity specified in the Excel input file.

The application calculates:

```text
Total Price = Unit Price × Quantity
```

If quantity is missing, it defaults to `1`.

### ⚡ Parallel Processing

Supplier websites are processed concurrently using `ThreadPoolExecutor`.

The current configuration uses **10 workers**, allowing multiple supplier pages to be processed at the same time.

### 📊 Excel Report

The generated `output.xlsx` contains additional columns including:

* `Status`
* `Price`
* `Total Price`

The original supplier order is preserved after parallel processing.

### 🎨 Excel Formatting

The generated workbook includes several formatting features:

* Clickable supplier links
* Color-coded status cells
* Different colors for different supplier websites
* Comma-separated price formatting
* Automatic column width adjustment
* Grand total calculation

Successful results are marked as `OK`, while missing prices and errors are marked as `NO` or `ERROR`.

### 📈 Price History

The application keeps track of previous grand totals in:

```text
price_history.xlsx
```

Each run stores:

* Date / Time
* Grand Total

When previous data exists, the output also displays:

* Current Grand Total
* Previous Total
* Difference

This makes it possible to monitor changes in overall supplier costs over time.

## Project Structure

A typical project structure is:

```text
project/
│
├── main.py
├── database.xlsx
├── output.xlsx
├── price_history.xlsx
│
├── scrapers/
│   ├── router.py
│   └── ...
│
└── README.md
```

> The exact filenames and scraper modules may differ depending on your repository structure.

## Requirements

The project uses Python and the following main libraries:

```text
pandas
requests
beautifulsoup4
openpyxl
tqdm
```

It also requires the project's local `scrapers` package.

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Install the required Python packages:

```bash
pip install pandas requests beautifulsoup4 openpyxl tqdm
```

If the project contains a `requirements.txt` file, you can install everything with:

```bash
pip install -r requirements.txt
```
## Input Excel File

Create a file named:

```text
database.xlsx
```

The input Excel file should contain at least these columns:

| Column     | Description                             |
| ---------- | --------------------------------------- |
| `Supplier` | Supplier webpage URL or local HTML file |
| `Quantity` | Quantity required for the item          |

The application validates that the required columns are present before processing the file.

Example:

| Supplier                     | Quantity |
| ---------------------------- | -------: |
| https://example.com/product1 |        5 |
| https://example.com/product2 |       10 |

## Usage

Run the Python application:

```bash
python main.py
```

The application will:

1. Load `database.xlsx`
2. Read supplier links
3. Download and parse webpages
4. Extract prices
5. Calculate total prices
6. Process suppliers concurrently
7. Generate `output.xlsx`
8. Update `price_history.xlsx`
9. Open the generated Excel file automatically when supported by the operating system

## Output

The generated Excel report contains information such as:

```text
Supplier | Quantity | Status | Price | Total Price
```

A grand total is also added at the bottom of the report.

If a previous run exists, the report can additionally show:

```text
Grand Total
Previous Total
Difference
```

## Status Values

| Status  | Meaning                                         |
| ------- | ----------------------------------------------- |
| `OK`    | Price was successfully found                    |
| `NO`    | No price was found                              |
| `ERROR` | An error occurred while processing the supplier |

## Currency Handling

The application supports prices represented using Persian currency notation.

When the extracted currency is `تومان`, the value is multiplied by `10` to convert it to Rial.

## Error Handling

The scraper includes:

* Request timeouts
* Retry attempts
* Exception handling per supplier
* Status reporting
* Continued processing of other suppliers when an individual supplier fails

This means a failure on one website does not necessarily stop the entire scraping process.

## Performance

Supplier pages are processed concurrently using multiple worker threads.

The current default is:

```python
MAX_WORKERS = 10
```

This value can be adjusted depending on the number of suppliers and the limits of the target websites.

## Price History Example

Every successful run can add a record similar to:

```text
Date / Time          Grand Total
2026-08-13 15:20:00  12500000
2026-08-14 15:20:00  12800000
```

This allows changes in total supplier costs to be tracked over multiple runs.

## Important Notes

* Supplier websites may change their HTML structure, which can affect price extraction.
* The custom scraper modules in `scrapers/` are responsible for identifying prices on different websites.
* The number of concurrent workers should be configured responsibly.
* Always make sure you have permission to scrape the websites you target and follow their terms of service and applicable rules.
* Keep sensitive supplier information and private credentials out of the repository.

## Future Improvements

Possible future improvements include:

* Automatic scheduled scraping
* Email or Telegram notifications when prices change
* Support for additional currencies
* More supplier-specific scrapers
* Price-change percentage calculations
* Historical price charts
* Database storage instead of Excel
* Web dashboard
* Automatic detection of product availability
* Configurable scraping intervals
* Logging system

## License

```text
GNU GENERAL PUBLIC LICENSE
```

## Author

**Ahmadelectronic@gmail.com**

If you found this project useful, feel free to ⭐ the repository.
