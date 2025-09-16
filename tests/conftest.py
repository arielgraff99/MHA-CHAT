"""
Shared pytest fixtures and configuration for TimelineNarrator tests
"""
import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch
import asyncio
from datetime import datetime, timezone

# Add backend to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.models.database import Base, get_db
from backend.app import app
from backend.config import Config

# Test configuration
class TestConfig(Config):
    DATABASE_URL = "sqlite:///test_timeline_narrator.db"
    UPLOAD_FOLDER = "test_data/uploads"
    EXPORT_FOLDER = "test_data/exports"
    TEMP_FOLDER = "test_data/temp"
    OPENAI_API_KEY = "test-key"
    DEBUG = True
    LOG_LEVEL = "DEBUG"

@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return TestConfig()

@pytest.fixture(scope="session")
def test_engine(test_config):
    """Create test database engine"""
    engine = create_engine(test_config.DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture(scope="function")
def sample_files(temp_dir):
    """Create sample test files"""
    files = {}
    
    # Sample email file
    email_content = """From: test@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 01 Jan 2024 10:00:00 +0000

This is a test email content.
"""
    email_file = Path(temp_dir) / "test_email.eml"
    email_file.write_text(email_content)
    files['email'] = str(email_file)
    
    # Sample text file
    text_content = """Test Document
Created: 2024-01-01 10:00:00
Author: Test Author

This is a sample text document for testing.
It contains some important information about the investigation.
"""
    text_file = Path(temp_dir) / "test_document.txt"
    text_file.write_text(text_content)
    files['text'] = str(text_file)
    
    # Sample PDF placeholder (empty file for testing)
    pdf_file = Path(temp_dir) / "test_document.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF")
    files['pdf'] = str(pdf_file)
    
    return files

@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mocked LLM response"
        mock_create.return_value = mock_response
        yield mock_create

@pytest.fixture
def mock_spacy():
    """Mock spaCy NLP model"""
    with patch('spacy.load') as mock_load:
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([])
        mock_nlp.return_value = mock_doc
        mock_load.return_value = mock_nlp
        yield mock_nlp

@pytest.fixture
def sample_investigation_data():
    """Sample investigation data for testing"""
    return {
        "subject_of_investigation": "Test Investigation",
        "start_datetime": "2024-01-01T00:00:00Z",
        "end_datetime": "2024-01-31T23:59:59Z",
        "time_resolution": "days"
    }

@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "id": "EVT-test123",
        "subject_of_investigation": "Test Investigation",
        "event_datetime_iso": datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        "event_text": "Test event occurred",
        "source_id": "SRC-test123",
        "entities": {"people": ["John Doe"], "locations": ["New York"]},
        "confidence": 0.8
    }

@pytest.fixture
def sample_source_data():
    """Sample source data for testing"""
    return {
        "id": "SRC-test123",
        "source_type": "text_file",
        "source_path_or_uid": "/test/path/document.txt",
        "original_filename": "document.txt",
        "file_size_bytes": 1024,
        "file_hash": "abcd1234",
        "upload_timestamp": datetime.now(timezone.utc)
    }

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()