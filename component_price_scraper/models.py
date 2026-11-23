from dataclasses import dataclass
from pathlib import Path
from typing import Literal


ScrapeStatus = Literal["OK", "NO", "ERROR"]


@dataclass(frozen=True, slots=True)
class ScrapeResult:
    status: ScrapeStatus
    price: int | None = None
    total_price: int | None = None
    content: str = ""
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RunSummary:
    total_records: int
    successful: int
    not_found: int
    errors: int
    grand_total: int
    output_file: Path
    history_file: Path
