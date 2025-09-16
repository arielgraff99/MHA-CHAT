from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from app.extractors.base import BaseExtractor, make_extracted_row, generate_source_id_from_path


class ImageExtractor(BaseExtractor):
    def extract(self, source_path: Path) -> Dict[str, Any]:
        # Placeholder text; integrate OCR engine like pytesseract in a full build
        text = ""
        return make_extracted_row(
            source_id=generate_source_id_from_path(source_path),
            source_type="image",
            source_path_or_uid=str(source_path),
            extracted_text=text,
            detected_language=None,
            extracted_datetime_raw=None,
            extracted_datetime_iso=None,
            author_or_sender=None,
            title_or_subject=source_path.name,
            parse_method="ocr",
        )