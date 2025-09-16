from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from pdfminer.high_level import extract_text as pdf_extract_text

from app.extractors.base import BaseExtractor, make_extracted_row, generate_source_id_from_path


class PDFExtractor(BaseExtractor):
    def extract(self, source_path: Path) -> Dict[str, Any]:
        text = ""
        parse_method = "text_layer"
        try:
            text = pdf_extract_text(str(source_path)) or ""
        except Exception:
            # Placeholder for OCR path; in a fuller build use pytesseract
            parse_method = "ocr"
            text = ""  # OCR not implemented in this stub

        return make_extracted_row(
            source_id=generate_source_id_from_path(source_path),
            source_type="pdf",
            source_path_or_uid=str(source_path),
            extracted_text=text,
            detected_language=None,
            extracted_datetime_raw=None,
            extracted_datetime_iso=None,
            author_or_sender=None,
            title_or_subject=source_path.name,
            parse_method=parse_method,
        )