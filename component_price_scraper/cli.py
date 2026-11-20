"""Command-line entry point."""

import argparse

from . import PriceMonitor, ScraperConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape electronic-component supplier prices.")
    parser.add_argument("--input", default="database.xlsx", help="Input workbook")
    parser.add_argument("--output", default="output.xlsx", help="Output workbook")
    parser.add_argument("--history", default="price_history.xlsx", help="Price-history workbook")
    parser.add_argument("--workers", type=int, default=10, help="Concurrent workers")
    parser.add_argument("--timeout", type=float, default=15, help="HTTP timeout in seconds")
    parser.add_argument("--no-open", action="store_true", help="Do not open the output workbook")
    args = parser.parse_args()

    config = ScraperConfig(
        input_file=args.input,
        output_file=args.output,
        history_file=args.history,
        max_workers=args.workers,
        timeout=args.timeout,
        auto_open=not args.no_open,
    )
    summary = PriceMonitor(config).run()
    print(
        f"Done: {summary.successful} OK, {summary.not_found} not found, "
        f"{summary.errors} errors. Grand total: {summary.grand_total:,}"
    )
    print(f"Output: {summary.output_file}")
