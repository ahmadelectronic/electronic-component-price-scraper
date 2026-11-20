from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(slots=True)
class ScraperConfig:
    """Runtime options for scraping and Excel report generation."""

    input_file: str | Path = Path("database.xlsx")
    output_file: str | Path = Path("output.xlsx")
    history_file: str | Path = Path("price_history.xlsx")
    max_workers: int = 10
    timeout: float = 15
    retries: int = 2  # Total attempts, matching the original application.
    retry_delay: float = 1
    auto_open: bool = True
    show_progress: bool = True
    headers: dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS.copy())

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        if self.retries < 1:
            raise ValueError("retries must be at least 1")
        if self.retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")
