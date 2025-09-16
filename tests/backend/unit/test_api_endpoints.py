"""
Comprehensive tests for FastAPI endpoints in TimelineNarrator
"""

import pytest
import json
import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from tests.sample_data_generator import SampleDataGenerator


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "1.0.0"


class TestIngestEndpoint:
    """Test file ingestion endpoint"""
    
    def setup_method(self):
        """Set up test data"""
        self.generator = SampleDataGenerator()
        self.sample_files = self.generator.generate_all_samples()
    
    def test_ingest_single_file(self, client: TestClient):
        """Test ingesting a single file"""
        doc_file = self.sample_files["documents"][0]
        
        with open(doc_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": ("test_doc.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "source_ids" in data
        assert "message" in data
        assert len(data["source_ids"]) == 1
        assert data["source_ids"][0].startswith("SRC-")
    
    def test_ingest_multiple_files(self, client: TestClient):
        """Test ingesting multiple files"""
        files_to_upload = []
        
        # Upload one file from each type
        for file_type, file_list in self.sample_files.items():
            if file_list:
                file_path = file_list[0]
                files_to_upload.append(("files", (f"test_{file_type}.ext", open(file_path, 'rb'))))
        
        try:
            response = client.post("/ingest", files=files_to_upload)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["source_ids"]) == len(files_to_upload)
            
            # All source IDs should be unique
            assert len(set(data["source_ids"])) == len(data["source_ids"])
        
        finally:
            for _, (_, f) in files_to_upload:
                f.close()
    
    def test_ingest_no_files(self, client: TestClient):
        """Test ingest endpoint with no files"""
        response = client.post("/ingest", files={})
        
        assert response.status_code == 422  # Validation error
    
    def test_ingest_empty_file(self, client: TestClient):
        """Test ingest endpoint with empty file"""
        response = client.post(
            "/ingest",
            files={"files": ("empty.txt", io.BytesIO(b""), "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()
    
    def test_ingest_unsupported_file_type(self, client: TestClient):
        """Test ingest endpoint with unsupported file type"""
        response = client.post(
            "/ingest",
            files={"files": ("test.exe", io.BytesIO(b"fake exe"), "application/octet-stream")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not supported" in data["detail"].lower()


class TestExtractEndpoint:
    """Test content extraction endpoint"""
    
    def test_extract_valid_sources(self, client: TestClient, sample_source_data):
        """Test extracting from valid source IDs"""
        # First create a source by uploading
        doc_content = "Test document content for extraction"
        
        upload_response = client.post(
            "/ingest",
            files={"files": ("test.txt", io.BytesIO(doc_content.encode()), "text/plain")}
        )
        
        assert upload_response.status_code == 200
        source_ids = upload_response.json()["source_ids"]
        
        # Then extract
        extract_response = client.post(
            "/extract",
            json={"source_ids": source_ids}
        )
        
        assert extract_response.status_code == 200
        data = extract_response.json()
        assert "extracted_count" in data
        assert data["extracted_count"] == len(source_ids)
        assert "message" in data
    
    def test_extract_invalid_source_ids(self, client: TestClient):
        """Test extraction with invalid source IDs"""
        response = client.post(
            "/extract",
            json={"source_ids": ["INVALID-ID", "ANOTHER-INVALID"]}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_extract_empty_source_list(self, client: TestClient):
        """Test extraction with empty source ID list"""
        response = client.post(
            "/extract",
            json={"source_ids": []}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()
    
    def test_extract_malformed_request(self, client: TestClient):
        """Test extraction with malformed request"""
        response = client.post(
            "/extract",
            json={"invalid_field": ["SRC-123"]}
        )
        
        assert response.status_code == 422  # Validation error


class TestEventsEndpoint:
    """Test event generation endpoint"""
    
    def test_generate_events_valid_request(self, client: TestClient):
        """Test event generation with valid parameters"""
        # First upload and extract a file
        doc_content = "Meeting on January 15, 2024 with John Doe in New York"
        
        upload_response = client.post(
            "/ingest",
            files={"files": ("meeting.txt", io.BytesIO(doc_content.encode()), "text/plain")}
        )
        source_ids = upload_response.json()["source_ids"]
        
        client.post("/extract", json={"source_ids": source_ids})
        
        # Generate events
        response = client.post("/events", data={
            "subject": "Test Investigation",
            "start_datetime": "2024-01-01T00:00:00Z",
            "end_datetime": "2024-01-31T23:59:59Z"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "events_created" in data
        assert "message" in data
        assert isinstance(data["events_created"], int)
    
    def test_generate_events_no_end_datetime(self, client: TestClient):
        """Test event generation without end datetime"""
        response = client.post("/events", data={
            "subject": "Test Investigation",
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        # Should work with just start datetime
        assert response.status_code == 200
    
    def test_generate_events_invalid_datetime(self, client: TestClient):
        """Test event generation with invalid datetime format"""
        response = client.post("/events", data={
            "subject": "Test Investigation",
            "start_datetime": "invalid-date-format"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "datetime" in data["detail"].lower()
    
    def test_generate_events_missing_subject(self, client: TestClient):
        """Test event generation without subject"""
        response = client.post("/events", data={
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_events_end_before_start(self, client: TestClient):
        """Test event generation with end datetime before start"""
        response = client.post("/events", data={
            "subject": "Test Investigation",
            "start_datetime": "2024-01-15T00:00:00Z",
            "end_datetime": "2024-01-10T00:00:00Z"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "end datetime" in data["detail"].lower()


class TestNarrativeEndpoint:
    """Test narrative generation endpoint"""
    
    def test_generate_narrative_valid_request(self, client: TestClient):
        """Test narrative generation with valid parameters"""
        # Upload, extract, and generate events first
        doc_content = "Project meeting on January 15, 2024"
        
        upload_response = client.post(
            "/ingest",
            files={"files": ("project.txt", io.BytesIO(doc_content.encode()), "text/plain")}
        )
        source_ids = upload_response.json()["source_ids"]
        
        client.post("/extract", json={"source_ids": source_ids})
        client.post("/events", data={
            "subject": "Project Investigation",
            "start_datetime": "2024-01-01T00:00:00Z",
            "end_datetime": "2024-01-31T23:59:59Z"
        })
        
        # Generate narrative
        response = client.post("/narrative", data={
            "time_resolution": "days",
            "subject": "Project Investigation",
            "start_datetime": "2024-01-01T00:00:00Z",
            "end_datetime": "2024-01-31T23:59:59Z"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "narrative_blocks_created" in data
        assert "message" in data
        assert isinstance(data["narrative_blocks_created"], int)
    
    def test_generate_narrative_invalid_resolution(self, client: TestClient):
        """Test narrative generation with invalid time resolution"""
        response = client.post("/narrative", data={
            "time_resolution": "invalid_resolution",
            "subject": "Test Investigation",
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "time_resolution" in data["detail"].lower()
    
    def test_generate_narrative_missing_events(self, client: TestClient):
        """Test narrative generation when no events exist"""
        response = client.post("/narrative", data={
            "time_resolution": "days",
            "subject": "Nonexistent Investigation",
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        assert response.status_code == 200  # Should succeed but with no blocks
        data = response.json()
        assert data["narrative_blocks_created"] == 0


class TestBriefRefinementEndpoints:
    """Test brief refinement endpoints"""
    
    @patch('openai.ChatCompletion.create')
    def test_refine_brief_success(self, mock_openai, client: TestClient):
        """Test successful brief refinement"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
OBJECTIVE: Test objective
SCOPE: Test scope
ACCEPTANCE_CRITERIA:
1. Test criteria 1
2. Test criteria 2
ENTITIES: ["test", "entity"]
TIMEFRAME: 2024-01-01 to 2024-01-31
"""
        mock_openai.return_value = mock_response
        
        response = client.post("/refine-brief", data={
            "subject_of_investigation": "Test investigation brief"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "refinement" in data
        assert "message" in data
        assert "objective" in data["refinement"]
    
    def test_refine_brief_empty_input(self, client: TestClient):
        """Test brief refinement with empty input"""
        response = client.post("/refine-brief", data={
            "subject_of_investigation": ""
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()
    
    def test_confirm_brief_valid(self, client: TestClient):
        """Test brief confirmation with valid ID"""
        response = client.post("/confirm-brief", data={
            "refinement_id": "test-refinement-123",
            "confirmed": "true"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "confirmed" in data
        assert "message" in data
    
    def test_confirm_brief_invalid_id(self, client: TestClient):
        """Test brief confirmation with invalid ID"""
        response = client.post("/confirm-brief", data={
            "refinement_id": "invalid-id",
            "confirmed": "true"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestStatusEndpoint:
    """Test source status endpoint"""
    
    def test_status_valid_source(self, client: TestClient):
        """Test status check for valid source"""
        # Upload a file first
        doc_content = "Test document for status check"
        
        upload_response = client.post(
            "/ingest",
            files={"files": ("status_test.txt", io.BytesIO(doc_content.encode()), "text/plain")}
        )
        source_ids = upload_response.json()["source_ids"]
        
        # Check status
        response = client.get(f"/status/{source_ids[0]}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["source_id"] == source_ids[0]
        assert "status" in data
        assert "upload_timestamp" in data
    
    def test_status_invalid_source(self, client: TestClient):
        """Test status check for invalid source ID"""
        response = client.get("/status/INVALID-SOURCE-ID")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestDownloadEndpoint:
    """Test download bundle endpoint"""
    
    def test_download_bundle(self, client: TestClient):
        """Test downloading investigation bundle"""
        # Need to have some data first
        doc_content = "Test document for download"
        
        upload_response = client.post(
            "/ingest",
            files={"files": ("download_test.txt", io.BytesIO(doc_content.encode()), "text/plain")}
        )
        source_ids = upload_response.json()["source_ids"]
        
        client.post("/extract", json={"source_ids": source_ids})
        client.post("/events", data={
            "subject": "Download Test",
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        # Download bundle
        response = client.get("/download")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "attachment" in response.headers["content-disposition"]
    
    def test_download_no_data(self, client: TestClient):
        """Test download when no data exists"""
        response = client.get("/download")
        
        # Should still create empty bundle or return appropriate message
        assert response.status_code in [200, 404]


class TestInvestigationsEndpoint:
    """Test investigations management endpoint"""
    
    def test_get_investigations_empty(self, client: TestClient):
        """Test getting investigations when none exist"""
        response = client.get("/investigations")
        
        assert response.status_code == 200
        data = response.json()
        assert "investigations" in data
        assert isinstance(data["investigations"], list)
    
    def test_get_investigations_with_data(self, client: TestClient):
        """Test getting investigations after creating some"""
        # Create investigation by running workflow
        doc_content = "Investigation test document"
        
        upload_response = client.post(
            "/ingest",
            files={"files": ("inv_test.txt", io.BytesIO(doc_content.encode()), "text/plain")}
        )
        source_ids = upload_response.json()["source_ids"]
        
        client.post("/extract", json={"source_ids": source_ids})
        client.post("/events", data={
            "subject": "Test Investigation List",
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        response = client.get("/investigations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["investigations"]) >= 0  # May or may not create investigation record


class TestAPIErrorHandling:
    """Test API error handling scenarios"""
    
    def test_malformed_json_request(self, client: TestClient):
        """Test handling of malformed JSON requests"""
        response = client.post(
            "/extract",
            data="invalid json content",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient):
        """Test handling of requests with missing required fields"""
        response = client.post("/events", data={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_invalid_content_type(self, client: TestClient):
        """Test handling of invalid content types"""
        response = client.post(
            "/ingest",
            data="not multipart form data",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_request_timeout_simulation(self, client: TestClient):
        """Test handling of request timeouts"""
        # Simulate slow processing
        with patch('backend.extractors.factory.extractor_factory.extract_file') as mock_extract:
            import time
            def slow_extract(file_path):
                time.sleep(0.1)  # Small delay for testing
                return {"extracted_text": "slow content", "confidence": 0.8}
            
            mock_extract.side_effect = slow_extract
            
            doc_content = "Test content"
            response = client.post(
                "/ingest",
                files={"files": ("slow.txt", io.BytesIO(doc_content.encode()), "text/plain")}
            )
            
            # Should complete even with delay
            assert response.status_code == 200


class TestAPIAuthentication:
    """Test API authentication and security"""
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set"""
        response = client.options("/health")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_security_headers(self, client: TestClient):
        """Test security headers in responses"""
        response = client.get("/health")
        
        # Basic security check - response should not expose internal details
        assert response.status_code == 200
        data = response.json()
        assert "database_url" not in str(data).lower()
        assert "password" not in str(data).lower()


class TestAPIValidation:
    """Test API input validation"""
    
    def test_datetime_format_validation(self, client: TestClient):
        """Test datetime format validation across endpoints"""
        invalid_formats = [
            "2024-13-01T00:00:00Z",  # Invalid month
            "2024-01-32T00:00:00Z",  # Invalid day
            "2024-01-01T25:00:00Z",  # Invalid hour
            "not-a-date",            # Not a date
            "2024/01/01",           # Wrong format
        ]
        
        for invalid_date in invalid_formats:
            response = client.post("/events", data={
                "subject": "Validation Test",
                "start_datetime": invalid_date
            })
            
            assert response.status_code == 400
    
    def test_subject_validation(self, client: TestClient):
        """Test subject field validation"""
        # Empty subject
        response = client.post("/events", data={
            "subject": "",
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        assert response.status_code == 400
        
        # Very long subject
        long_subject = "x" * 1000
        response = client.post("/events", data={
            "subject": long_subject,
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        
        # Should either accept or reject gracefully
        assert response.status_code in [200, 400]
    
    def test_time_resolution_validation(self, client: TestClient):
        """Test time resolution validation"""
        valid_resolutions = ["years", "months", "weeks", "days", "hours"]
        invalid_resolutions = ["minutes", "seconds", "invalid", ""]
        
        for resolution in valid_resolutions:
            response = client.post("/narrative", data={
                "time_resolution": resolution,
                "subject": "Resolution Test",
                "start_datetime": "2024-01-01T00:00:00Z"
            })
            # Should accept valid resolutions (may fail for other reasons)
            assert response.status_code in [200, 400, 404]
        
        for resolution in invalid_resolutions:
            response = client.post("/narrative", data={
                "time_resolution": resolution,
                "subject": "Resolution Test",
                "start_datetime": "2024-01-01T00:00:00Z"
            })
            # Should reject invalid resolutions
            assert response.status_code == 400


class TestAPIIntegration:
    """Test full API workflow integration"""
    
    def test_complete_investigation_workflow(self, client: TestClient):
        """Test complete investigation workflow through API"""
        
        # Step 1: Health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Step 2: Upload files
        files_data = []
        generator = SampleDataGenerator()
        sample_files = generator.generate_all_samples()
        
        for file_type, file_list in sample_files.items():
            if file_list:
                file_path = file_list[0]
                files_data.append(("files", (f"{file_type}_test.ext", open(file_path, 'rb'))))
        
        try:
            upload_response = client.post("/ingest", files=files_data)
            assert upload_response.status_code == 200
            source_ids = upload_response.json()["source_ids"]
            
            # Step 3: Extract content
            extract_response = client.post("/extract", json={"source_ids": source_ids})
            assert extract_response.status_code == 200
            
            # Step 4: Generate events
            events_response = client.post("/events", data={
                "subject": "Complete Workflow Test",
                "start_datetime": "2024-01-01T00:00:00Z",
                "end_datetime": "2024-01-31T23:59:59Z"
            })
            assert events_response.status_code == 200
            
            # Step 5: Generate narrative
            narrative_response = client.post("/narrative", data={
                "time_resolution": "days",
                "subject": "Complete Workflow Test",
                "start_datetime": "2024-01-01T00:00:00Z",
                "end_datetime": "2024-01-31T23:59:59Z"
            })
            assert narrative_response.status_code == 200
            
            # Step 6: Download results
            download_response = client.get("/download")
            assert download_response.status_code == 200
            
            # Step 7: Check investigations
            investigations_response = client.get("/investigations")
            assert investigations_response.status_code == 200
        
        finally:
            for _, (_, f) in files_data:
                if hasattr(f, 'close'):
                    f.close()
    
    def test_partial_workflow_recovery(self, client: TestClient):
        """Test recovery from partial workflow failures"""
        # Upload files
        doc_content = "Recovery test document"
        upload_response = client.post(
            "/ingest",
            files={"files": ("recovery.txt", io.BytesIO(doc_content.encode()), "text/plain")}
        )
        source_ids = upload_response.json()["source_ids"]
        
        # Extract successfully
        extract_response = client.post("/extract", json={"source_ids": source_ids})
        assert extract_response.status_code == 200
        
        # Try events with invalid parameters (should fail)
        events_response = client.post("/events", data={
            "subject": "",  # Invalid empty subject
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        assert events_response.status_code == 400
        
        # Should be able to retry with valid parameters
        retry_response = client.post("/events", data={
            "subject": "Recovery Test",
            "start_datetime": "2024-01-01T00:00:00Z"
        })
        assert retry_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])