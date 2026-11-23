"""Batch processing API for the Excel price monitor."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ScraperConfig
from .models import RunSummary, ScrapeResult
from .report import open_file, write_report
from .scraper import PriceScraper


class PriceMonitor:
    """Read supplier rows, scrape them concurrently and create an Excel report."""

    def __init__(self, config: ScraperConfig | None = None) -> None:
        self.config = config or ScraperConfig()
        self.scraper = PriceScraper(self.config)

    def run(self) -> RunSummary:
        dataframe = pd.read_excel(self.config.input_file)
        dataframe.columns = dataframe.columns.map(lambda name: str(name).strip())
        required = {"Supplier", "Quantity"}
        missing = required.difference(dataframe.columns)
        if missing:
            raise ValueError(
                f"Excel file must contain {sorted(missing)} columns. "
                f"Found: {list(dataframe.columns)}"
            )

        results: list[ScrapeResult | None] = [None] * len(dataframe)
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self.scraper.scrape, supplier, quantity): index
                for index, (supplier, quantity) in enumerate(
                    zip(dataframe["Supplier"], dataframe["Quantity"])
                )
            }
            completed = as_completed(futures)
            if self.config.show_progress:
                try:
                    from tqdm import tqdm
                    completed = tqdm(completed, total=len(futures), desc="Scraping sites", unit="site")
                except ImportError:
                    pass

            for future in completed:
                index = futures[future]
                try:
                    results[index] = future.result()
                except Exception as exc:  # Defensive: retain row order even on an unexpected worker failure.
                    results[index] = ScrapeResult(status="ERROR", error=str(exc), content=f"ERROR: {exc}")

        final_results = [item or ScrapeResult(status="ERROR", error="No result") for item in results]
        grand_total = write_report(
            dataframe,
            final_results,
            self.config.output_file,
            self.config.history_file,
        )

        if self.config.auto_open:
            open_file(self.config.output_file)

        return RunSummary(
            total_records=len(final_results),
            successful=sum(item.status == "OK" for item in final_results),
            not_found=sum(item.status == "NO" for item in final_results),
            errors=sum(item.status == "ERROR" for item in final_results),
            grand_total=grand_total,
            output_file=Path(self.config.output_file),
            history_file=Path(self.config.history_file),
        )
