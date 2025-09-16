import pandas as pd
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..config import config
from ..models.database import Source, ExtractedText, Event, NarrativeBlock

class CSVExporter:
    """Export data to CSV files according to specification"""
    
    def __init__(self):
        self.schemas = {
            'extracted_text': [
                "source_id", "source_type", "source_path_or_uid", "extracted_text",
                "detected_language", "extracted_datetime_raw", "extracted_datetime_iso",
                "datetime_confidence", "author_or_sender", "title_or_subject",
                "parse_method", "ingest_timestamp_iso"
            ],
            'events': [
                "event_id", "subject_of_investigation", "event_datetime_iso",
                "event_datetime_end_iso", "timezone", "event_title", "event_summary",
                "entities_people", "entities_orgs", "entities_locations", "keywords",
                "source_id", "source_excerpt", "confidence_overall", "inference_notes"
            ],
            'narrative': [
                "block_id", "time_bucket_label", "start_datetime_iso", "end_datetime_iso",
                "narrative_text", "event_ids_included", "evidence_source_ids",
                "aggregation_level", "llm_model", "llm_temperature", "created_timestamp_iso"
            ]
        }
    
    def export_extracted_text_csv(self, db: Session, timestamp: str, output_directory: str = None) -> str:
        """Export extracted text data to CSV"""
        # Query data
        query = db.query(ExtractedText, Source).join(Source, ExtractedText.source_id == Source.id)
        results = query.all()
        
        # Prepare data
        data = []
        for extracted_text, source in results:
            row = {
                "source_id": extracted_text.source_id,
                "source_type": source.source_type,
                "source_path_or_uid": source.source_path_or_uid,
                "extracted_text": extracted_text.extracted_text,
                "detected_language": extracted_text.detected_language,
                "extracted_datetime_raw": extracted_text.extracted_datetime_raw,
                "extracted_datetime_iso": extracted_text.extracted_datetime_iso.isoformat() if extracted_text.extracted_datetime_iso else None,
                "datetime_confidence": extracted_text.datetime_confidence,
                "author_or_sender": extracted_text.author_or_sender,
                "title_or_subject": extracted_text.title_or_subject,
                "parse_method": extracted_text.parse_method,
                "ingest_timestamp_iso": extracted_text.ingest_timestamp_iso.isoformat() if extracted_text.ingest_timestamp_iso else None
            }
            data.append(row)
        
        # Create DataFrame and export
        df = pd.DataFrame(data, columns=self.schemas['extracted_text'])
        filename = f"timeline_extracted_text_{timestamp}.csv"
        
        # Use output directory if provided, otherwise fallback to config
        export_dir = output_directory or config.OUTPUT_DIRECTORY or config.EXPORT_FOLDER
        os.makedirs(export_dir, exist_ok=True)
        
        filepath = os.path.join(export_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def export_events_csv(self, db: Session, timestamp: str) -> str:
        """Export events data to CSV"""
        # Query data
        events = db.query(Event).all()
        
        # Prepare data
        data = []
        for event in events:
            row = {
                "event_id": event.id,
                "subject_of_investigation": event.subject_of_investigation,
                "event_datetime_iso": event.event_datetime_iso.isoformat() if event.event_datetime_iso else None,
                "event_datetime_end_iso": event.event_datetime_end_iso.isoformat() if event.event_datetime_end_iso else None,
                "timezone": event.timezone,
                "event_title": event.event_title,
                "event_summary": event.event_summary,
                "entities_people": json.dumps(event.entities_people) if event.entities_people else "[]",
                "entities_orgs": json.dumps(event.entities_orgs) if event.entities_orgs else "[]",
                "entities_locations": json.dumps(event.entities_locations) if event.entities_locations else "[]",
                "keywords": json.dumps(event.keywords) if event.keywords else "[]",
                "source_id": event.source_id,
                "source_excerpt": event.source_excerpt,
                "confidence_overall": event.confidence_overall,
                "inference_notes": event.inference_notes
            }
            data.append(row)
        
        # Create DataFrame and export
        df = pd.DataFrame(data, columns=self.schemas['events'])
        filename = f"events_{timestamp}.csv"
        filepath = os.path.join(config.EXPORT_FOLDER, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def export_narrative_csv(self, db: Session, timestamp: str) -> str:
        """Export narrative blocks data to CSV"""
        # Query data
        narrative_blocks = db.query(NarrativeBlock).all()
        
        # Prepare data
        data = []
        for block in narrative_blocks:
            # Get associated event IDs and source IDs
            event_ids = [event.id for event in block.events]
            source_ids = list(set([event.source_id for event in block.events]))
            
            row = {
                "block_id": block.id,
                "time_bucket_label": block.time_bucket_label,
                "start_datetime_iso": block.start_datetime_iso.isoformat() if block.start_datetime_iso else None,
                "end_datetime_iso": block.end_datetime_iso.isoformat() if block.end_datetime_iso else None,
                "narrative_text": block.narrative_text,
                "event_ids_included": json.dumps(event_ids),
                "evidence_source_ids": json.dumps(source_ids),
                "aggregation_level": block.aggregation_level,
                "llm_model": block.llm_model,
                "llm_temperature": block.llm_temperature,
                "created_timestamp_iso": block.created_timestamp_iso.isoformat() if block.created_timestamp_iso else None
            }
            data.append(row)
        
        # Create DataFrame and export
        df = pd.DataFrame(data, columns=self.schemas['narrative'])
        filename = f"narrative_{timestamp}.csv"
        filepath = os.path.join(config.EXPORT_FOLDER, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def export_all_csvs(self, db: Session, timestamp: str) -> List[str]:
        """Export all CSV files"""
        csv_files = []
        
        try:
            csv_files.append(self.export_extracted_text_csv(db, timestamp))
        except Exception as e:
            print(f"Failed to export extracted text CSV: {e}")
        
        try:
            csv_files.append(self.export_events_csv(db, timestamp))
        except Exception as e:
            print(f"Failed to export events CSV: {e}")
        
        try:
            csv_files.append(self.export_narrative_csv(db, timestamp))
        except Exception as e:
            print(f"Failed to export narrative CSV: {e}")
        
        return csv_files
    
    def generate_schema_readme(self) -> str:
        """Generate schema documentation"""
        readme_content = """# TimelineNarrator Data Export Schema

This export contains three CSV files with the following schemas:

## extracted_text_{timestamp}.csv
Contains raw extracted text from all ingested sources.

Columns:
- source_id: Unique identifier for the source file
- source_type: Type of source (email, text_file, pdf, image)
- source_path_or_uid: Path or unique identifier of the source
- extracted_text: Full extracted text content
- detected_language: Language detected in the text
- extracted_datetime_raw: Raw datetime string found in source
- extracted_datetime_iso: Normalized datetime in ISO format
- datetime_confidence: Confidence score for datetime extraction (0.0-1.0)
- author_or_sender: Author or sender information
- title_or_subject: Title or subject of the content
- parse_method: Method used to extract the text
- ingest_timestamp_iso: When the file was ingested

## events_{timestamp}.csv
Contains timeline events extracted from the sources.

Columns:
- event_id: Unique identifier for the event
- subject_of_investigation: Subject being investigated
- event_datetime_iso: Event datetime in ISO format
- event_datetime_end_iso: Event end datetime (if applicable)
- timezone: Timezone of the event
- event_title: Title of the event
- event_summary: Summary description of the event
- entities_people: JSON array of people entities
- entities_orgs: JSON array of organization entities
- entities_locations: JSON array of location entities
- keywords: JSON array of extracted keywords
- source_id: Source that generated this event
- source_excerpt: Excerpt from source text
- confidence_overall: Overall confidence score
- inference_notes: Notes about how the event was inferred

## narrative_{timestamp}.csv
Contains generated narrative blocks for timeline periods.

Columns:
- block_id: Unique identifier for the narrative block
- time_bucket_label: Label for the time period (e.g., "2023-12")
- start_datetime_iso: Start of time period
- end_datetime_iso: End of time period
- narrative_text: Generated narrative text
- event_ids_included: JSON array of event IDs included
- evidence_source_ids: JSON array of source IDs referenced
- aggregation_level: Time resolution level
- llm_model: LLM model used for generation
- llm_temperature: Temperature setting used
- created_timestamp_iso: When the narrative was generated

## Source Traceability
Every narrative sentence maps to one or more source_ids. Source IDs are referenced in narrative text using the format [SRC-xxxxx].
"""
        return readme_content
    
    def generate_provenance_manifest(self, db: Session) -> Dict[str, Any]:
        """Generate provenance manifest with metadata"""
        sources = db.query(Source).all()
        events = db.query(Event).all()
        narratives = db.query(NarrativeBlock).all()
        
        manifest = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "application": "TimelineNarrator",
            "version": "1.0.0",
            "statistics": {
                "total_sources": len(sources),
                "total_events": len(events),
                "total_narrative_blocks": len(narratives),
                "source_types": {}
            },
            "source_summary": [],
            "processing_metadata": {
                "deduplication_window_seconds": config.DEDUPLICATION_WINDOW_SECONDS,
                "similarity_threshold": config.SIMILARITY_THRESHOLD,
                "llm_model": config.LLM_MODEL,
                "llm_temperature": config.LLM_TEMPERATURE
            }
        }
        
        # Count source types
        for source in sources:
            source_type = source.source_type
            if source_type not in manifest["statistics"]["source_types"]:
                manifest["statistics"]["source_types"][source_type] = 0
            manifest["statistics"]["source_types"][source_type] += 1
        
        # Add source summary
        for source in sources:
            manifest["source_summary"].append({
                "source_id": source.id,
                "source_type": source.source_type,
                "original_filename": source.original_filename,
                "file_size_bytes": source.file_size_bytes,
                "upload_timestamp": source.upload_timestamp.isoformat() if source.upload_timestamp else None,
                "extraction_status": source.extraction_status
            })
        
        return manifest