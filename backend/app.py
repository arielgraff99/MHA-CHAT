from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import shutil
from datetime import datetime, timezone
import zipfile
import pandas as pd
import uuid

from .config import config
from .models.database import get_db, create_tables, Source, ExtractedText, Event, NarrativeBlock, Investigation, AuditLog
from .extractors.factory import extractor_factory
from .nlp.entity_extractor import entity_extractor
from .nlp.brief_refiner import brief_refiner
from .nlp.narrative_generator import narrative_generator
from .utils.timeline import TimelineProcessor
from .utils.csv_exporter import CSVExporter
from .utils.security import SecurityManager

# FastAPI app created above with lifespan

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="TimelineNarrator",
    description="Extract information from documents and generate timeline narratives",
    version="1.0.0",
    lifespan=lifespan
)

# Dependency to get timeline processor
def get_timeline_processor():
    return TimelineProcessor()

# Dependency to get CSV exporter
def get_csv_exporter():
    return CSVExporter()

# Dependency to get security manager
def get_security_manager():
    return SecurityManager()

@app.post("/ingest")
async def ingest_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    security: SecurityManager = Depends(get_security_manager)
):
    """Ingest multiple files and return source IDs"""
    try:
        source_ids = []
        total_size = 0
        
        for file in files:
            # Validate file size
            file_size = 0
            content = await file.read()
            file_size = len(content)
            total_size += file_size
            
            if file_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} exceeds maximum size of {config.MAX_FILE_SIZE_MB}MB"
                )
            
            if total_size > config.MAX_TOTAL_SIZE_GB * 1024 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"Total upload size exceeds maximum of {config.MAX_TOTAL_SIZE_GB}GB"
                )
            
            # Validate file type
            if not extractor_factory.is_supported(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.filename}"
                )
            
            # Generate source ID and save file
            source_id = f"SRC-{uuid.uuid4().hex[:8]}"
            file_path = os.path.join(config.UPLOAD_FOLDER, f"{source_id}_{file.filename}")
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Determine source type
            _, ext = os.path.splitext(file.filename.lower())
            source_type = None
            for file_type, extensions in config.SUPPORTED_EXTENSIONS.items():
                if ext in extensions:
                    source_type = file_type
                    break
            
            # Create source record
            source = Source(
                id=source_id,
                source_type=source_type,
                source_path_or_uid=file_path,
                original_filename=file.filename,
                file_size_bytes=file_size,
                mime_type=file.content_type
            )
            
            db.add(source)
            source_ids.append(source_id)
        
        db.commit()
        
        # Log audit event
        audit_log = AuditLog(
            action="ingest_files",
            metadata={
                'file_count': len(files),
                'total_size_bytes': total_size,
                'source_ids': source_ids
            }
        )
        db.add(audit_log)
        db.commit()
        
        return {"source_ids": source_ids, "message": f"Successfully ingested {len(files)} files"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-directory")
async def ingest_directory(
    request: dict,
    db: Session = Depends(get_db),
    security: SecurityManager = Depends(get_security_manager)
):
    """Ingest files from a local directory"""
    try:
        directory_path = request.get("directory_path")
        discovered_files = request.get("discovered_files", [])
        
        if not directory_path:
            raise HTTPException(status_code=400, detail="No directory path provided")
        
        if not discovered_files:
            raise HTTPException(status_code=400, detail="No files discovered in directory")
        
        # Filter only supported files
        supported_files = [f for f in discovered_files if f.get("supported", False)]
        
        if not supported_files:
            raise HTTPException(status_code=400, detail="No supported files found in directory")
        
        source_ids = []
        total_size = 0
        
        # Store the directory path for output generation
        output_directory = directory_path
        
        for file_info in supported_files:
            file_path = os.path.join(directory_path, file_info["name"])
            
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                continue
                
            if not os.access(file_path, os.R_OK):
                continue
            
            file_size = file_info.get("size", 0)
            total_size += file_size
            
            # Validate file size
            if file_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
                continue  # Skip oversized files
            
            # Generate source ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            source_id = f"SRC-{timestamp}-{uuid.uuid4().hex[:8]}"
            
            # Determine source type
            _, ext = os.path.splitext(file_info["name"].lower())
            source_type = None
            for file_type, extensions in config.SUPPORTED_EXTENSIONS.items():
                if ext in extensions:
                    source_type = file_type
                    break
            
            # Create source record - store original path
            source = Source(
                id=source_id,
                source_type=source_type,
                source_path_or_uid=file_path,  # Store original file path
                original_filename=file_info["name"],
                file_size_bytes=file_size,
                mime_type=file_info.get("type", "unknown")
            )
            
            db.add(source)
            source_ids.append(source_id)
        
        if not source_ids:
            raise HTTPException(status_code=400, detail="No valid files could be processed")
        
        db.commit()
        
        # Store output directory in session/config for later use
        # This will be used by CSV exporter and other output generators
        config.OUTPUT_DIRECTORY = output_directory
        
        # Log audit event
        audit_log = AuditLog(
            action="ingest_directory",
            metadata={
                'directory_path': directory_path,
                'file_count': len(supported_files),
                'total_size_bytes': total_size,
                'source_ids': source_ids,
                'output_directory': output_directory
            }
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "source_ids": source_ids, 
            "message": f"Successfully registered {len(supported_files)} files from directory",
            "directory_path": directory_path,
            "output_directory": output_directory
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract")
async def extract_sources(
    source_ids: List[str],
    db: Session = Depends(get_db)
):
    """Extract text from ingested sources"""
    try:
        extraction_results = []
        
        for source_id in source_ids:
            # Get source record
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
            
            # Update status to processing
            source.extraction_status = 'processing'
            db.commit()
            
            try:
                # Extract content
                extraction_result = extractor_factory.extract_file(source.source_path_or_uid)
                
                # Create extracted text record
                extracted_text = ExtractedText(
                    source_id=source_id,
                    extracted_text=extraction_result['extracted_text'],
                    detected_language=extraction_result['detected_language'],
                    extracted_datetime_raw=extraction_result['extracted_datetime_raw'],
                    extracted_datetime_iso=extraction_result['extracted_datetime_iso'],
                    datetime_confidence=extraction_result['datetime_confidence'],
                    author_or_sender=extraction_result['author_or_sender'],
                    title_or_subject=extraction_result['title_or_subject'],
                    parse_method=extraction_result['parse_method']
                )
                
                db.add(extracted_text)
                
                # Update source status and metadata
                source.extraction_status = 'completed'
                source.extraction_metadata = extraction_result['metadata']
                
                extraction_results.append({
                    'source_id': source_id,
                    'status': 'completed',
                    'extracted_text_length': len(extraction_result['extracted_text']),
                    'detected_language': extraction_result['detected_language'],
                    'datetime_found': extraction_result['extracted_datetime_iso'] is not None
                })
                
            except Exception as e:
                source.extraction_status = 'failed'
                source.extraction_metadata = {'error': str(e)}
                extraction_results.append({
                    'source_id': source_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        db.commit()
        
        return {
            "extraction_results": extraction_results,
            "message": f"Processed {len(source_ids)} sources"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events")
async def generate_events(
    subject: str = Form(...),
    start_datetime: str = Form(...),
    end_datetime: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    timeline_processor: TimelineProcessor = Depends(get_timeline_processor)
):
    """Generate events from extracted texts"""
    try:
        # Parse datetime inputs
        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = None
        if end_datetime:
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now(timezone.utc)
        
        # Get all extracted texts
        extracted_texts = db.query(ExtractedText).all()
        
        events_created = []
        
        for extracted_text in extracted_texts:
            # Skip if no datetime or outside range
            if not extracted_text.extracted_datetime_iso:
                continue
                
            event_dt = extracted_text.extracted_datetime_iso
            if event_dt < start_dt or event_dt > end_dt:
                continue
            
            # Extract entities from text
            entities = entity_extractor.extract_entities(extracted_text.extracted_text)
            
            # Create event record
            event = Event(
                subject_of_investigation=subject,
                event_datetime_iso=event_dt,
                event_title=extracted_text.title_or_subject,
                event_summary=extracted_text.extracted_text[:500] + "..." if len(extracted_text.extracted_text) > 500 else extracted_text.extracted_text,
                entities_people=entities['people'],
                entities_orgs=entities['organizations'],
                entities_locations=entities['locations'],
                keywords=entities['keywords'],
                source_id=extracted_text.source_id,
                source_excerpt=extracted_text.extracted_text[:200],
                confidence_overall=extracted_text.datetime_confidence,
                inference_notes=f"Generated from {extracted_text.parse_method}"
            )
            
            db.add(event)
            events_created.append(event.id)
        
        db.commit()
        
        return {
            "events_created": events_created,
            "message": f"Generated {len(events_created)} events for '{subject}'"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/narrative")
async def generate_narrative(
    time_resolution: str = Form(...),
    subject: str = Form(...),
    start_datetime: str = Form(...),
    end_datetime: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    timeline_processor: TimelineProcessor = Depends(get_timeline_processor)
):
    """Generate timeline narrative from events"""
    try:
        # Parse datetime inputs
        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = None
        if end_datetime:
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now(timezone.utc)
        
        # Get events for subject and date range
        events_query = db.query(Event).filter(
            Event.subject_of_investigation == subject,
            Event.event_datetime_iso >= start_dt,
            Event.event_datetime_iso <= end_dt
        ).order_by(Event.event_datetime_iso)
        
        events = events_query.all()
        
        if not events:
            return {
                "narrative_blocks": [],
                "message": "No events found for the specified criteria"
            }
        
        # Group events by time buckets
        time_buckets = timeline_processor.group_events_by_time_resolution(
            [event.__dict__ for event in events], 
            time_resolution
        )
        
        narrative_blocks_created = []
        
        for bucket_label, bucket_events in time_buckets.items():
            if not bucket_events:
                continue
            
            # Generate narrative for this time bucket
            narrative_result = narrative_generator.generate_narrative(
                bucket_events,
                bucket_label,
                subject,
                time_resolution
            )
            
            # Create narrative block record
            narrative_block = NarrativeBlock(
                subject_of_investigation=subject,
                time_bucket_label=bucket_label,
                start_datetime_iso=min(event['event_datetime_iso'] for event in bucket_events),
                end_datetime_iso=max(event['event_datetime_iso'] for event in bucket_events),
                narrative_text=narrative_result['narrative_text'],
                aggregation_level=time_resolution,
                llm_model=config.LLM_MODEL,
                llm_temperature=config.LLM_TEMPERATURE
            )
            
            db.add(narrative_block)
            db.flush()  # Get the ID
            
            # Link events to narrative block
            for event_data in bucket_events:
                event = db.query(Event).filter(Event.id == event_data['id']).first()
                if event:
                    narrative_block.events.append(event)
            
            narrative_blocks_created.append(narrative_block.id)
        
        db.commit()
        
        return {
            "narrative_blocks": narrative_blocks_created,
            "message": f"Generated {len(narrative_blocks_created)} narrative blocks"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_bundle(
    bundle: bool = True,
    investigation_id: Optional[str] = None,
    db: Session = Depends(get_db),
    csv_exporter: CSVExporter = Depends(get_csv_exporter)
):
    """Download data bundle as ZIP file"""
    try:
        if bundle:
            # Create ZIP bundle with all data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"timeline_narrator_export_{timestamp}.zip"
            zip_path = os.path.join(config.EXPORT_FOLDER, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Export CSVs
                csv_files = csv_exporter.export_all_csvs(db, timestamp)
                
                for csv_file in csv_files:
                    zipf.write(csv_file, os.path.basename(csv_file))
                
                # Add schema readme
                schema_readme = csv_exporter.generate_schema_readme()
                readme_path = os.path.join(config.TEMP_FOLDER, "schema_readme.md")
                with open(readme_path, 'w') as f:
                    f.write(schema_readme)
                zipf.write(readme_path, "schema_readme.md")
                
                # Add provenance manifest
                manifest = csv_exporter.generate_provenance_manifest(db)
                manifest_path = os.path.join(config.TEMP_FOLDER, "provenance_manifest.json")
                with open(manifest_path, 'w') as f:
                    import json
                    json.dump(manifest, f, indent=2, default=str)
                zipf.write(manifest_path, "provenance_manifest.json")
            
            return FileResponse(
                zip_path,
                media_type='application/zip',
                filename=zip_filename
            )
        else:
            raise HTTPException(status_code=400, detail="Only bundle downloads are currently supported")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refine-brief")
async def refine_investigation_brief(
    subject_of_investigation: str = Form(...),
    additional_context: Optional[str] = Form(None)
):
    """Refine investigation brief using NLP"""
    try:
        context = {"additional_context": additional_context} if additional_context else None
        refinement_result = brief_refiner.refine_brief(subject_of_investigation, context)
        
        return {
            "refinement": refinement_result,
            "message": "Brief refined successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/confirm-brief")
async def confirm_refined_brief(
    refinement_id: str = Form(...),
    confirmed: bool = Form(...),
    db: Session = Depends(get_db)
):
    """Confirm or reject refined brief"""
    try:
        # In a real implementation, you'd store refinement results and retrieve by ID
        # For now, just return confirmation status
        return {
            "confirmed": confirmed,
            "message": "Brief confirmation recorded"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{source_id}")
async def get_source_status(
    source_id: str,
    db: Session = Depends(get_db)
):
    """Get processing status of a source"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return {
        "source_id": source_id,
        "status": source.extraction_status,
        "metadata": source.extraction_metadata,
        "upload_timestamp": source.upload_timestamp
    }

@app.get("/investigations")
async def list_investigations(db: Session = Depends(get_db)):
    """List all investigations"""
    investigations = db.query(Investigation).order_by(Investigation.created_timestamp.desc()).all()
    
    return {
        "investigations": [
            {
                "id": inv.id,
                "subject": inv.subject_of_investigation,
                "status": inv.status,
                "start_datetime": inv.start_datetime,
                "end_datetime": inv.end_datetime,
                "time_resolution": inv.time_resolution,
                "created_timestamp": inv.created_timestamp
            }
            for inv in investigations
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Serve static files for frontend
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React frontend"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        frontend_path = "frontend/build"
        file_path = os.path.join(frontend_path, full_path)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        else:
            # Serve index.html for React Router
            return FileResponse(os.path.join(frontend_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)