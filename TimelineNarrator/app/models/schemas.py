from typing import List, Optional
from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    source_ids: List[str]


class ExtractRequest(BaseModel):
    source_ids: List[str] = Field(default_factory=list)


class EventsRequest(BaseModel):
    subject: str
    start_datetime: str
    end_datetime: Optional[str] = None


class NarrativeRequest(BaseModel):
    time_resolution: str


class CSVConfig(BaseModel):
    filename: str
    path: str


class DownloadBundleResponse(BaseModel):
    bundle_path: str
    size_bytes: int