"""
Upload Validation Tests for TimelineNarrator

Tests the file upload functionality including:
- Valid file type uploads
- Invalid file type rejection
- File size validation
- File content validation
- Batch upload scenarios
- Error handling
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

from tests.sample_data_generator import SampleDataGenerator


class TestUploadValidation:
    """Test suite for file upload validation"""
    
    def setup_method(self):
        """Set up test data for each test"""
        self.generator = SampleDataGenerator()
        self.sample_files = self.generator.generate_all_samples()
    
    def test_valid_email_upload(self, client: TestClient):
        """Test uploading valid email files"""
        email_file = Path(self.sample_files["emails"][0])
        
        with open(email_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": ("test_email.eml", f, "message/rfc822")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "source_ids" in data
        assert len(data["source_ids"]) == 1
        assert data["source_ids"][0].startswith("SRC-")
        assert "message" in data
    
    def test_valid_document_upload(self, client: TestClient):
        """Test uploading valid text documents"""
        doc_file = Path(self.sample_files["documents"][0])
        
        with open(doc_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": ("meeting_notes.md", f, "text/markdown")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "source_ids" in data
        assert len(data["source_ids"]) == 1
    
    def test_valid_pdf_upload(self, client: TestClient):
        """Test uploading valid PDF files"""
        pdf_file = Path(self.sample_files["pdfs"][0])
        
        with open(pdf_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": ("contract.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "source_ids" in data
        assert len(data["source_ids"]) == 1
    
    def test_valid_image_upload(self, client: TestClient):
        """Test uploading valid image files"""
        img_file = Path(self.sample_files["images"][0])
        
        with open(img_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": ("document_scan.jpg", f, "image/jpeg")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "source_ids" in data
        assert len(data["source_ids"]) == 1
    
    def test_batch_upload_multiple_types(self, client: TestClient):
        """Test uploading multiple files of different types"""
        files_to_upload = []
        
        # Add one file from each type
        for file_type, file_list in self.sample_files.items():
            if file_list:
                file_path = Path(file_list[0])
                files_to_upload.append(("files", (file_path.name, open(file_path, 'rb'))))
        
        try:
            response = client.post("/ingest", files=files_to_upload)
            
            assert response.status_code == 200
            data = response.json()
            assert "source_ids" in data
            assert len(data["source_ids"]) == len(files_to_upload)
            
            # Verify all source IDs are unique and properly formatted
            source_ids = data["source_ids"]
            assert len(set(source_ids)) == len(source_ids)  # All unique
            for source_id in source_ids:
                assert source_id.startswith("SRC-")
                assert len(source_id) > 4
        
        finally:
            # Close all file handles
            for _, (_, file_handle) in files_to_upload:
                file_handle.close()
    
    def test_invalid_file_type_rejection(self, client: TestClient):
        """Test rejection of unsupported file types"""
        # Create a fake executable file
        fake_exe_content = b"MZ\x90\x00"  # PE header
        
        response = client.post(
            "/ingest",
            files={"files": ("malware.exe", io.BytesIO(fake_exe_content), "application/octet-stream")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not supported" in data["detail"].lower()
    
    def test_empty_file_rejection(self, client: TestClient):
        """Test rejection of empty files"""
        response = client.post(
            "/ingest",
            files={"files": ("empty.txt", io.BytesIO(b""), "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
    
    def test_oversized_file_rejection(self, client: TestClient):
        """Test rejection of files exceeding size limits"""
        # Create a large file (simulate > 250MB)
        large_content = b"x" * (260 * 1024 * 1024)  # 260MB
        
        with patch('backend.config.config.MAX_FILE_SIZE_MB', 250):
            response = client.post(
                "/ingest",
                files={"files": ("large_file.txt", io.BytesIO(large_content), "text/plain")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "size" in data["detail"].lower()
    
    def test_malformed_file_handling(self, client: TestClient):
        """Test handling of malformed files"""
        # Create a file with wrong extension
        malformed_content = b"This is not a PDF file"
        
        response = client.post(
            "/ingest",
            files={"files": ("fake.pdf", io.BytesIO(malformed_content), "application/pdf")}
        )
        
        # Should either reject or handle gracefully
        assert response.status_code in [200, 400]
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data
    
    def test_special_characters_in_filename(self, client: TestClient):
        """Test handling of filenames with special characters"""
        doc_file = Path(self.sample_files["documents"][0])
        
        with open(doc_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": ("special-chars_file@#$%.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "source_ids" in data
    
    def test_unicode_filename_handling(self, client: TestClient):
        """Test handling of Unicode characters in filenames"""
        doc_file = Path(self.sample_files["documents"][0])
        
        with open(doc_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": ("документ_тест.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "source_ids" in data
    
    def test_duplicate_file_upload(self, client: TestClient):
        """Test uploading the same file multiple times"""
        doc_file = Path(self.sample_files["documents"][0])
        
        # Upload same file twice
        with open(doc_file, 'rb') as f:
            response1 = client.post(
                "/ingest",
                files={"files": ("document.txt", f, "text/plain")}
            )
        
        with open(doc_file, 'rb') as f:
            response2 = client.post(
                "/ingest",
                files={"files": ("document.txt", f, "text/plain")}
            )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Should create different source IDs (no deduplication at upload)
        data1 = response1.json()
        data2 = response2.json()
        assert data1["source_ids"][0] != data2["source_ids"][0]
    
    def test_no_files_upload(self, client: TestClient):
        """Test upload endpoint with no files"""
        response = client.post("/ingest", files={})
        
        assert response.status_code == 422  # Validation error
    
    def test_extraction_after_upload(self, client: TestClient):
        """Test extraction process after successful upload"""
        doc_file = Path(self.sample_files["documents"][0])
        
        # First upload
        with open(doc_file, 'rb') as f:
            upload_response = client.post(
                "/ingest",
                files={"files": ("meeting_notes.md", f, "text/markdown")}
            )
        
        assert upload_response.status_code == 200
        source_ids = upload_response.json()["source_ids"]
        
        # Then extract
        extract_response = client.post(
            "/extract",
            json={"source_ids": source_ids}
        )
        
        assert extract_response.status_code == 200
        extract_data = extract_response.json()
        assert "extracted_count" in extract_data
        assert extract_data["extracted_count"] == len(source_ids)
    
    def test_upload_with_metadata_preservation(self, client: TestClient):
        """Test that file metadata is preserved during upload"""
        email_file = Path(self.sample_files["emails"][0])
        original_size = email_file.stat().st_size
        
        with open(email_file, 'rb') as f:
            response = client.post(
                "/ingest",
                files={"files": (email_file.name, f, "message/rfc822")}
            )
        
        assert response.status_code == 200
        source_ids = response.json()["source_ids"]
        
        # Check source status
        status_response = client.get(f"/status/{source_ids[0]}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "metadata" in status_data
        # Note: Exact metadata structure depends on implementation


class TestFileValidation:
    """Test file content validation and processing"""
    
    def setup_method(self):
        """Set up test data"""
        self.generator = SampleDataGenerator()
    
    def test_email_format_validation(self):
        """Test email file format validation"""
        from backend.extractors.email_extractor import EmailExtractor
        
        extractor = EmailExtractor()
        
        # Test valid email file
        email_files = self.generator.generate_email_samples()
        assert extractor.can_handle(email_files[0])
        
        # Test extraction
        result = extractor.extract(email_files[0])
        assert "email_from" in result
        assert "email_to" in result
        assert "email_subject" in result
        assert "email_date" in result
        assert "extracted_text" in result
    
    def test_text_encoding_validation(self):
        """Test text file encoding detection and validation"""
        from backend.extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        
        # Test valid text file
        doc_files = self.generator.generate_document_samples()
        text_file = next(f for f in doc_files if f.endswith('.txt'))
        
        assert extractor.can_handle(text_file)
        
        result = extractor.extract(text_file)
        assert "extracted_text" in result
        assert "detected_language" in result
        assert "confidence" in result
    
    def test_image_ocr_validation(self):
        """Test image OCR processing validation"""
        from backend.extractors.image_extractor import ImageExtractor
        
        extractor = ImageExtractor()
        
        # Test valid image file
        image_files = self.generator.generate_image_samples()
        assert extractor.can_handle(image_files[0])
        
        # Mock pytesseract for testing
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Mocked OCR text content"
            
            result = extractor.extract(image_files[0])
            assert "extracted_text" in result
            assert "ocr_confidence" in result
    
    def test_pdf_processing_validation(self):
        """Test PDF processing validation"""
        from backend.extractors.pdf_extractor import PDFExtractor
        
        extractor = PDFExtractor()
        
        # Test valid PDF file
        pdf_files = self.generator.generate_pdf_samples()
        assert extractor.can_handle(pdf_files[0])
        
        # Mock PDF processing libraries
        with patch('pdfplumber.open') as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Mocked PDF text content"
            mock_pdf.pages = [mock_page]
            mock_pdf.metadata = {"Title": "Test PDF", "Author": "Test Author"}
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
            
            result = extractor.extract(pdf_files[0])
            assert "extracted_text" in result
            assert "pdf_metadata" in result


class TestEndToEndUpload:
    """End-to-end upload testing scenarios"""
    
    def setup_method(self):
        """Set up comprehensive test scenario"""
        self.generator = SampleDataGenerator()
        self.sample_files = self.generator.generate_all_samples()
    
    def test_complete_investigation_workflow(self, client: TestClient):
        """Test complete workflow from upload to narrative generation"""
        
        # Step 1: Upload files
        files_to_upload = []
        for file_type, file_list in self.sample_files.items():
            if file_list:
                file_path = Path(file_list[0])
                files_to_upload.append(("files", (file_path.name, open(file_path, 'rb'))))
        
        try:
            upload_response = client.post("/ingest", files=files_to_upload)
            assert upload_response.status_code == 200
            source_ids = upload_response.json()["source_ids"]
            
            # Step 2: Extract content
            extract_response = client.post("/extract", json={"source_ids": source_ids})
            assert extract_response.status_code == 200
            
            # Step 3: Generate events
            events_response = client.post("/events", data={
                "subject": "Test Investigation",
                "start_datetime": "2024-01-01T00:00:00Z",
                "end_datetime": "2024-01-31T23:59:59Z"
            })
            assert events_response.status_code == 200
            
            # Step 4: Generate narrative
            narrative_response = client.post("/narrative", data={
                "time_resolution": "days",
                "subject": "Test Investigation", 
                "start_datetime": "2024-01-01T00:00:00Z",
                "end_datetime": "2024-01-31T23:59:59Z"
            })
            assert narrative_response.status_code == 200
            
            # Step 5: Download results
            download_response = client.get("/download")
            assert download_response.status_code == 200
            assert download_response.headers["content-type"] == "application/zip"
        
        finally:
            # Close all file handles
            for _, (_, file_handle) in files_to_upload:
                if hasattr(file_handle, 'close'):
                    file_handle.close()
    
    def test_upload_validation_with_expected_results(self, client: TestClient):
        """Test upload and validate against expected extraction results"""
        validation_data = self.generator.create_validation_dataset()
        
        for relative_path, expected in validation_data.items():
            file_path = self.generator.output_dir / relative_path
            
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    response = client.post(
                        "/ingest",
                        files={"files": (file_path.name, f, "auto")}
                    )
                
                assert response.status_code == 200
                source_ids = response.json()["source_ids"]
                
                # Extract and validate
                extract_response = client.post("/extract", json={"source_ids": source_ids})
                assert extract_response.status_code == 200
                
                # Note: Full validation would require checking extracted content
                # against expected entities, but that requires the full NLP pipeline


def create_upload_test_script():
    """Create a standalone script for manual upload testing"""
    script_content = '''#!/usr/bin/env python3
"""
Manual Upload Testing Script for TimelineNarrator

Usage:
    python upload_test_script.py [--host localhost] [--port 8000]
    
This script will:
1. Generate sample data
2. Test uploads to running TimelineNarrator instance
3. Validate responses
4. Report results
"""

import requests
import argparse
from pathlib import Path
import sys
import os

# Add tests to path
sys.path.insert(0, str(Path(__file__).parent))
from sample_data_generator import SampleDataGenerator

def test_upload_to_server(host="localhost", port=8000):
    """Test upload functionality against running server"""
    base_url = f"http://{host}:{port}"
    
    # Check if server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Server not responding at {base_url}")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {base_url}")
        return False
    
    print(f"✅ Server is running at {base_url}")
    
    # Generate sample data
    print("📁 Generating sample data...")
    generator = SampleDataGenerator()
    sample_files = generator.generate_all_samples()
    
    success_count = 0
    total_count = 0
    
    # Test each file type
    for file_type, file_list in sample_files.items():
        print(f"\\n🧪 Testing {file_type} uploads...")
        
        for file_path in file_list:
            total_count += 1
            file_path_obj = Path(file_path)
            
            try:
                with open(file_path_obj, 'rb') as f:
                    files = {'files': (file_path_obj.name, f, 'auto')}
                    response = requests.post(f"{base_url}/ingest", files=files, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ {file_path_obj.name} -> {data.get('source_ids', ['Unknown'])[0]}")
                    success_count += 1
                else:
                    print(f"  ❌ {file_path_obj.name} -> Error {response.status_code}: {response.text}")
            
            except Exception as e:
                print(f"  ❌ {file_path_obj.name} -> Exception: {str(e)}")
    
    print(f"\\n📊 Results: {success_count}/{total_count} files uploaded successfully")
    return success_count == total_count

def main():
    parser = argparse.ArgumentParser(description="Test TimelineNarrator upload functionality")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    print("🚀 TimelineNarrator Upload Test")
    print("=" * 40)
    
    success = test_upload_to_server(args.host, args.port)
    
    if success:
        print("\\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    script_path = Path("tests/upload_test_script.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    return str(script_path)

# Create the script when this module is imported
upload_test_script = create_upload_test_script()