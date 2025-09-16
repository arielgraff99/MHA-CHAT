from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from email import policy
from email.parser import BytesParser

from app.extractors.base import BaseExtractor, make_extracted_row, generate_source_id_from_path


class EmailExtractor(BaseExtractor):
    def extract(self, source_path: Path) -> Dict[str, Any]:
        with open(source_path, 'rb') as fp:
            msg = BytesParser(policy=policy.default).parse(fp)
        body_text = msg.get_body(preferencelist=('plain',))
        body_str = body_text.get_content() if body_text else ""
        subject = msg.get('subject', '')
        sender = msg.get('from', '')
        sent_dt_raw = msg.get('date', '')

        return make_extracted_row(
            source_id=generate_source_id_from_path(source_path),
            source_type="email",
            source_path_or_uid=str(source_path),
            extracted_text=body_str,
            detected_language=None,
            extracted_datetime_raw=sent_dt_raw,
            extracted_datetime_iso=None,
            author_or_sender=sender,
            title_or_subject=subject,
            parse_method="rfc5322",
        )