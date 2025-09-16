from __future__ import annotations
from pathlib import Path
from datetime import datetime
import csv

from app.config import (
    OUTPUTS_DIR,
    EXTRACTED_TEXT_FILENAME_PATTERN,
    EVENTS_FILENAME_PATTERN,
    NARRATIVE_FILENAME_PATTERN,
)


def timestamp_for_filename() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    # Preserve column order as given by first row
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class CSVWriter:
    def __init__(self, base_dir: Path = OUTPUTS_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_extracted_text(self, rows: list[dict]) -> Path:
        filename = EXTRACTED_TEXT_FILENAME_PATTERN.format(timestamp=timestamp_for_filename())
        path = self.base_dir / filename
        write_csv(path, rows)
        return path

    def write_events(self, rows: list[dict]) -> Path:
        filename = EVENTS_FILENAME_PATTERN.format(timestamp=timestamp_for_filename())
        path = self.base_dir / filename
        write_csv(path, rows)
        return path

    def write_narrative(self, rows: list[dict]) -> Path:
        filename = NARRATIVE_FILENAME_PATTERN.format(timestamp=timestamp_for_filename())
        path = self.base_dir / filename
        write_csv(path, rows)
        return path