from __future__ import annotations
from typing import List, Dict, Any
import re


def refine_subject(subject: str) -> Dict[str, Any]:
    refined = subject.strip()
    refined = re.sub(r"\s+", " ", refined)
    acceptance = [
        "Subject is objective and concise",
        "Time range is respected",
        "Only verifiable claims with sources",
    ]
    return {"refined": refined, "acceptance_criteria": acceptance}


def extract_entities(text: str) -> Dict[str, List[str]]:
    # Minimal regex-based placeholder
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    urls = re.findall(r"https?://[^\s]+", text)
    return {
        "people": [],
        "organizations": [],
        "locations": [],
        "dates": [],
        "times": [],
        "emails": list(set(emails)),
        "urls": list(set(urls)),
        "ids": [],
        "topics": [],
        "keywords": [],
    }


def summarize_events_to_narrative(events: List[Dict[str, Any]], resolution: str) -> List[Dict[str, Any]]:
    # Very basic: concatenate event titles and summaries per bucket
    buckets: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        bucket = ev.get("time_bucket_label", "unknown")
        if bucket not in buckets:
            buckets[bucket] = {
                "block_id": f"BLK-{len(buckets)+1:04d}",
                "time_bucket_label": bucket,
                "start_datetime_iso": ev.get("bucket_start_iso", ev.get("event_datetime_iso", "")),
                "end_datetime_iso": ev.get("bucket_end_iso", ev.get("event_datetime_iso", "")),
                "narrative_text": "",
                "event_ids_included": [],
                "evidence_source_ids": set(),
                "aggregation_level": resolution,
                "llm_model": "stub",
                "llm_temperature": 0.0,
            }
        title = ev.get("event_title") or ev.get("event_summary") or "Event"
        buckets[bucket]["narrative_text"] += f"- {title}\n"
        buckets[bucket]["event_ids_included"].append(ev.get("event_id"))
        src = ev.get("source_id")
        if src:
            buckets[bucket]["evidence_source_ids"].add(src)

    results: List[Dict[str, Any]] = []
    for bucket, data in buckets.items():
        data["evidence_source_ids"] = ",".join(sorted(list(data["evidence_source_ids"])))
        results.append(data)
    results.sort(key=lambda x: x.get("start_datetime_iso", ""))
    return results