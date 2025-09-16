import os
from pathlib import Path

APP_NAME = "TimelineNarrator"
APP_VERSION = "1.0.0"
DEFAULT_TIMEZONE = "America/Toronto"

# I/O directories
BASE_DIR = Path("/workspace/TimelineNarrator")
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"

# Schema filenames
EXTRACTED_TEXT_FILENAME_PATTERN = "extracted_text_{timestamp}.csv"
EVENTS_FILENAME_PATTERN = "events_{timestamp}.csv"
NARRATIVE_FILENAME_PATTERN = "narrative_{timestamp}.csv"
BUNDLE_FILENAME = "timeline_narrator_bundle.zip"
SCHEMA_README_FILENAME = "schema_readme.md"
PROVENANCE_MANIFEST_FILENAME = "provenance_manifest.json"

# Deduplication
DEDUP_WINDOW_SECONDS = 120
SIMILARITY_THRESHOLD = 0.9
MERGE_STRATEGY = "keep_earliest_and_union_sources"

# Security and logging
PII_DEFAULT_REDACT = True
LOG_LEVEL = os.getenv("TN_LOG_LEVEL", "INFO")

# LLM configuration placeholders (non-calling in this stub)
LLM_MODEL = "gpt-5-thinking"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 2000
CONTENT_POLICY = "no fabrication; cite source_ids for every claim"

TIME_BUCKET_RULES = {
    "years": "%Y",
    "months": "%Y-%m",
    "weeks": "ISO_WEEK",  # handled specially
    "days": "%Y-%m-%d",
    "hours": "%Y-%m-%dT%H:00",
}

INGEST_SIZE_LIMIT_MB = 250
TOTAL_SIZE_LIMIT_GB = 5