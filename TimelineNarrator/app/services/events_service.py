from __future__ import annotations
from typing import List, Dict, Any
from uuid import uuid4
from rapidfuzz import fuzz

from app.utils.time_utils import bucket_label, iso_start_end_for_bucket


def build_events(subject: str, extracted_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for row in extracted_rows:
        text = row.get("extracted_text", "")
        title = row.get("title_or_subject") or text[:80]
        event_id = f"EVT-{uuid4()}"
        dt_iso = row.get("extracted_datetime_iso") or row.get("ingest_timestamp_iso")
        event = {
            "event_id": event_id,
            "subject_of_investigation": subject,
            "event_datetime_iso": dt_iso,
            "event_datetime_end_iso": dt_iso,
            "timezone": "America/Toronto",
            "event_title": title,
            "event_summary": text[:280],
            "entities_people": "",
            "entities_orgs": "",
            "entities_locations": "",
            "keywords": "",
            "source_id": row.get("source_id"),
            "source_excerpt": text[:200],
            "confidence_overall": row.get("datetime_confidence", 0.5),
            "inference_notes": "",
        }
        events.append(event)

    # Sort chronologically
    events.sort(key=lambda e: e.get("event_datetime_iso", ""))

    # Deduplication placeholder: keep all for now
    return events


def attach_buckets(events: List[Dict[str, Any]], resolution: str) -> List[Dict[str, Any]]:
    for ev in events:
        dt_iso = ev.get("event_datetime_iso", "")
        label = bucket_label(dt_iso, resolution)
        start_iso, end_iso = iso_start_end_for_bucket(dt_iso, resolution)
        ev["time_bucket_label"] = label
        ev["bucket_start_iso"] = start_iso
        ev["bucket_end_iso"] = end_iso
    return events