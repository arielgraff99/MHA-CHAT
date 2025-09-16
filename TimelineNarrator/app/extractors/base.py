from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
import hashlib
from datetime import datetime
from typing import Dict, Any

from app.utils.time_utils import now_iso


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, source_path: Path) -> Dict[str, Any]:
        ...


def generate_source_id_from_path(path: Path) -> str:
    h = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    return f"SRC-{h}"


def make_extracted_row(
    source_id: str,
    source_type: str,
    source_path_or_uid: str,
    extracted_text: str,
    detected_language: str | None,
    extracted_datetime_raw: str | None,
    extracted_datetime_iso: str | None,
    author_or_sender: str | None,
    title_or_subject: str | None,
    parse_method: str,
) -> Dict[str, Any]:
    return {
        "source_id": source_id,
        "source_type": source_type,
        "source_path_or_uid": source_path_or_uid,
        "extracted_text": extracted_text,
        "detected_language": detected_language or "unknown",
        "extracted_datetime_raw": extracted_datetime_raw or "",
        "extracted_datetime_iso": extracted_datetime_iso or "",
        "datetime_confidence": 0.5 if extracted_datetime_iso else 0.0,
        "author_or_sender": author_or_sender or "",
        "title_or_subject": title_or_subject or "",
        "parse_method": parse_method,
        "ingest_timestamp_iso": now_iso(),
    }