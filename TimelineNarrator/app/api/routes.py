from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
import shutil
import zipfile
import json
import csv

from app.config import (
    UPLOADS_DIR,
    OUTPUTS_DIR,
    BUNDLE_FILENAME,
    SCHEMA_README_FILENAME,
    PROVENANCE_MANIFEST_FILENAME,
)
from app.models.schemas import IngestResponse, ExtractRequest, EventsRequest, NarrativeRequest
from app.extractors.text_extractor import TextFileExtractor
from app.extractors.pdf_extractor import PDFExtractor
from app.extractors.image_extractor import ImageExtractor
from app.extractors.email_extractor import EmailExtractor
from app.extractors.base import generate_source_id_from_path
from app.utils.csv_utils import CSVWriter
from app.services.events_service import build_events, attach_buckets
from app.nlp.pipeline import summarize_events_to_narrative

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths: List[Path] = []
    for f in files:
        dest = UPLOADS_DIR / f.filename
        with dest.open("wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        saved_paths.append(dest)
    source_ids = [generate_source_id_from_path(p) for p in saved_paths]
    return {"source_ids": source_ids}


@router.post("/extract")
async def extract(req: ExtractRequest):
    writer = CSVWriter()
    rows = []
    target_paths = []
    if not req.source_ids:
        target_paths = [p for p in UPLOADS_DIR.glob("**/*") if p.is_file()]
    else:
        for src_id in req.source_ids:
            matched_path = None
            for p in UPLOADS_DIR.glob("**/*"):
                if p.is_file() and generate_source_id_from_path(p) == src_id:
                    matched_path = p
                    break
            if matched_path:
                target_paths.append(matched_path)
    for matched_path in target_paths:
        ext = matched_path.suffix.lower()
        if ext in {".txt", ".md", ".log"}:
            row = TextFileExtractor().extract(matched_path)
        elif ext in {".pdf"}:
            row = PDFExtractor().extract(matched_path)
        elif ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
            row = ImageExtractor().extract(matched_path)
        elif ext in {".eml"}:
            row = EmailExtractor().extract(matched_path)
        else:
            row = TextFileExtractor().extract(matched_path)
        rows.append(row)
    path = writer.write_extracted_text(rows)
    return {"csv_path": str(path)}


@router.post("/events")
async def events(req: EventsRequest):
    extracted = sorted(OUTPUTS_DIR.glob("extracted_text_*.csv"))
    if not extracted:
        raise HTTPException(status_code=400, detail="No extracted text available. Run /extract first.")
    latest = extracted[-1]
    from dateutil import parser
    with latest.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Filter by date range
    def within_range(r: dict) -> bool:
        try:
            ts = parser.isoparse(r.get("ingest_timestamp_iso", ""))
        except Exception:
            return False
        if req.start_datetime:
            try:
                if ts < parser.isoparse(req.start_datetime):
                    return False
            except Exception:
                pass
        if req.end_datetime:
            try:
                if ts > parser.isoparse(req.end_datetime):
                    return False
            except Exception:
                pass
        return True
    rows = [r for r in rows if within_range(r)]
    events_rows = build_events(req.subject, rows)
    events_rows = attach_buckets(events_rows, resolution="days")
    writer = CSVWriter()
    path = writer.write_events(events_rows)
    return {"csv_path": str(path)}


@router.post("/narrative")
async def narrative(req: NarrativeRequest):
    events_files = sorted(OUTPUTS_DIR.glob("events_*.csv"))
    if not events_files:
        raise HTTPException(status_code=400, detail="No events available. Run /events first.")
    with events_files[-1].open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        events = list(reader)
    narrative_rows = summarize_events_to_narrative(events, req.time_resolution)
    writer = CSVWriter()
    path = writer.write_narrative(narrative_rows)
    return {"csv_path": str(path)}


@router.get("/download")
async def download(bundle: bool = True):
    if not bundle:
        raise HTTPException(status_code=400, detail="Only bundle download is supported")
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path = OUTPUTS_DIR / BUNDLE_FILENAME
    # Write schema readme and provenance manifest
    schema_readme = OUTPUTS_DIR / SCHEMA_README_FILENAME
    schema_readme.write_text("See app/schemas in product spec; columns documented in code.")
    prov_manifest = OUTPUTS_DIR / PROVENANCE_MANIFEST_FILENAME
    prov_manifest.write_text(json.dumps({"policy": "Every narrative sentence must map to >=1 source_id"}))

    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for p in OUTPUTS_DIR.glob("*.csv"):
            zipf.write(p, arcname=p.name)
        zipf.write(schema_readme, arcname=schema_readme.name)
        zipf.write(prov_manifest, arcname=prov_manifest.name)
    return FileResponse(path=bundle_path, filename=bundle_path.name, media_type="application/zip")