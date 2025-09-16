from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz
from dateutil import parser

from app.config import DEFAULT_TIMEZONE, TIME_BUCKET_RULES


def parse_to_timezone_iso(dt_str: str, tz_name: str = DEFAULT_TIMEZONE) -> str:
    tz = pytz.timezone(tz_name)
    dt = parser.parse(dt_str)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    else:
        dt = dt.astimezone(tz)
    return dt.isoformat()


def now_iso(tz_name: str = DEFAULT_TIMEZONE) -> str:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).isoformat()


def bucket_label(dt_iso: str, resolution: str) -> str:
    tz_dt = parser.isoparse(dt_iso)
    if resolution == "weeks":
        iso_year, iso_week, _ = tz_dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    fmt = TIME_BUCKET_RULES.get(resolution, "%Y-%m-%d")
    return tz_dt.strftime(fmt)


def iso_start_end_for_bucket(dt_iso: str, resolution: str) -> tuple[str, str]:
    dt = parser.isoparse(dt_iso)
    if resolution == "years":
        start = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1) - timedelta(microseconds=1)
    elif resolution == "months":
        start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end_candidate = start.replace(year=start.year + 1, month=1)
        else:
            end_candidate = start.replace(month=start.month + 1)
        end = end_candidate - timedelta(microseconds=1)
    elif resolution == "weeks":
        start = dt - timedelta(days=dt.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7) - timedelta(microseconds=1)
    elif resolution == "days":
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1) - timedelta(microseconds=1)
    elif resolution == "hours":
        start = dt.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1) - timedelta(microseconds=1)
    else:
        start = dt
        end = dt
    return start.isoformat(), end.isoformat()