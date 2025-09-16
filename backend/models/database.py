from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from ..config import config

Base = declarative_base()

# Association table for many-to-many relationship between narrative blocks and events
narrative_events = Table(
    'narrative_events', Base.metadata,
    Column('narrative_block_id', String, ForeignKey('narrative_blocks.id'), primary_key=True),
    Column('event_id', String, ForeignKey('events.id'), primary_key=True)
)

class Source(Base):
    """Represents an ingested source file/document"""
    __tablename__ = 'sources'
    
    id = Column(String, primary_key=True)
    source_type = Column(String, nullable=False)  # email, text_file, pdf, image
    source_path_or_uid = Column(String, nullable=False)
    original_filename = Column(String)
    file_size_bytes = Column(Integer)
    mime_type = Column(String)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    extraction_status = Column(String, default='pending')  # pending, processing, completed, failed
    extraction_metadata = Column(JSON)
    
    # Relationships
    extracted_texts = relationship("ExtractedText", back_populates="source")
    events = relationship("Event", back_populates="source")

class ExtractedText(Base):
    """Represents extracted text from a source"""
    __tablename__ = 'extracted_texts'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(String, ForeignKey('sources.id'), nullable=False)
    extracted_text = Column(Text)
    detected_language = Column(String)
    extracted_datetime_raw = Column(String)
    extracted_datetime_iso = Column(DateTime)
    datetime_confidence = Column(Float)
    author_or_sender = Column(String)
    title_or_subject = Column(String)
    parse_method = Column(String)
    ingest_timestamp_iso = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source = relationship("Source", back_populates="extracted_texts")

class Event(Base):
    """Represents a timeline event extracted from sources"""
    __tablename__ = 'events'
    
    id = Column(String, primary_key=True)
    subject_of_investigation = Column(String, nullable=False)
    event_datetime_iso = Column(DateTime, nullable=False)
    event_datetime_end_iso = Column(DateTime)
    timezone = Column(String, default=config.DEFAULT_TIMEZONE)
    event_title = Column(String)
    event_summary = Column(Text)
    entities_people = Column(JSON)  # List of people entities
    entities_orgs = Column(JSON)    # List of organization entities
    entities_locations = Column(JSON)  # List of location entities
    keywords = Column(JSON)         # List of keywords
    source_id = Column(String, ForeignKey('sources.id'), nullable=False)
    source_excerpt = Column(Text)
    confidence_overall = Column(Float)
    inference_notes = Column(Text)
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source = relationship("Source", back_populates="events")
    narrative_blocks = relationship("NarrativeBlock", secondary="narrative_events", back_populates="events")

class NarrativeBlock(Base):
    """Represents a narrative block in the timeline"""
    __tablename__ = 'narrative_blocks'
    
    id = Column(String, primary_key=True)
    subject_of_investigation = Column(String, nullable=False)
    time_bucket_label = Column(String, nullable=False)
    start_datetime_iso = Column(DateTime, nullable=False)
    end_datetime_iso = Column(DateTime, nullable=False)
    narrative_text = Column(Text, nullable=False)
    aggregation_level = Column(String, nullable=False)  # years, months, weeks, days, hours
    llm_model = Column(String)
    llm_temperature = Column(Float)
    created_timestamp_iso = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    events = relationship("Event", secondary="narrative_events", back_populates="narrative_blocks")

# Association table already defined above

class Investigation(Base):
    """Represents an investigation session"""
    __tablename__ = 'investigations'
    
    id = Column(String, primary_key=True)
    subject_of_investigation = Column(String, nullable=False)
    refined_brief = Column(Text)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime)
    time_resolution = Column(String, nullable=False)  # years, months, weeks, days, hours
    status = Column(String, default='created')  # created, ingesting, processing, completed, failed
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    updated_timestamp = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String)  # For future multi-user support

class AuditLog(Base):
    """Audit log for tracking user actions"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source_id = Column(String)
    event_id = Column(String)
    hash_of_content = Column(String)
    metadata = Column(JSON)

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()