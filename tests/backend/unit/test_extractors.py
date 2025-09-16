"""
Comprehensive tests for all file extractors in TimelineNarrator
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone
import uuid

# Import extractors
from backend.extractors.base import BaseExtractor
from backend.extractors.email_extractor import EmailExtractor
from backend.extractors.text_extractor import TextExtractor
from backend.extractors.pdf_extractor import PDFExtractor
from backend.extractors.image_extractor import ImageExtractor
from backend.extractors.factory import ExtractorFactory


class TestBaseExtractor:
    """Test the base extractor functionality"""
    
    def test_abstract_methods(self):
        """Test that BaseExtractor is abstract"""
        with pytest.raises(TypeError):
            BaseExtractor()
    
    def test_can_handle_method(self):
        """Test the can_handle method logic"""
        # Create a concrete implementation for testing
        class TestExtractor(BaseExtractor):
            def __init__(self):
                super().__init__()
                self.supported_extensions = ['.txt', '.md']
                
            def extract(self, file_path: str):
                return {}
        
        extractor = TestExtractor()
        assert extractor.can_handle("test.txt")
        assert extractor.can_handle("document.md")
        assert not extractor.can_handle("image.jpg")
        assert not extractor.can_handle("file_without_extension")
    
    def test_get_file_hash(self, temp_dir):
        """Test file hash calculation"""
        class TestExtractor(BaseExtractor):
            def extract(self, file_path: str):
                return {}
        
        extractor = TestExtractor()
        
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test content")
        
        hash1 = extractor.get_file_hash(str(test_file))
        hash2 = extractor.get_file_hash(str(test_file))
        
        assert hash1 == hash2  # Same file should have same hash
        assert len(hash1) == 64  # SHA256 hash length
    
    def test_get_file_info(self, temp_dir):
        """Test file info extraction"""
        class TestExtractor(BaseExtractor):
            def extract(self, file_path: str):
                return {}
        
        extractor = TestExtractor()
        
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_content = "test content"
        test_file.write_text(test_content)
        
        info = extractor.get_file_info(str(test_file))
        
        assert info["file_size_bytes"] == len(test_content.encode())
        assert info["file_hash"] is not None
        assert info["file_extension"] == ".txt"
    
    def test_normalize_datetime(self):
        """Test datetime normalization"""
        class TestExtractor(BaseExtractor):
            def extract(self, file_path: str):
                return {}
        
        extractor = TestExtractor()
        
        # Test various datetime formats
        test_cases = [
            ("2024-01-15 10:30:00", 0.9),
            ("Jan 15, 2024 10:30 AM", 0.8),
            ("15/01/2024", 0.7),
            ("invalid date", 0.0)
        ]
        
        for date_str, expected_min_confidence in test_cases:
            dt, confidence = extractor.normalize_datetime(date_str)
            if expected_min_confidence > 0:
                assert dt is not None
                assert confidence >= expected_min_confidence
            else:
                assert dt is None
                assert confidence == 0.0


class TestEmailExtractor:
    """Test email extraction functionality"""
    
    def setup_method(self):
        """Set up email extractor"""
        self.extractor = EmailExtractor()
    
    def test_supported_extensions(self):
        """Test supported email extensions"""
        assert self.extractor.can_handle("email.eml")
        assert self.extractor.can_handle("message.msg")
        assert not self.extractor.can_handle("document.txt")
    
    def test_eml_extraction(self, temp_dir):
        """Test .eml file extraction"""
        # Create sample .eml file
        eml_content = """From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 15 Jan 2024 10:30:00 +0000
Message-ID: <test123@example.com>

This is the email body content.
It contains important information for testing.
"""
        eml_file = Path(temp_dir) / "test.eml"
        eml_file.write_text(eml_content)
        
        result = self.extractor.extract(str(eml_file))
        
        assert result["email_from"] == "sender@example.com"
        assert result["email_to"] == "recipient@example.com"
        assert result["email_subject"] == "Test Email"
        assert "This is the email body content" in result["extracted_text"]
        assert result["confidence"] > 0.8
    
    def test_html_email_extraction(self, temp_dir):
        """Test HTML email content extraction"""
        html_eml_content = """From: sender@example.com
To: recipient@example.com
Subject: HTML Test Email
Date: Mon, 15 Jan 2024 10:30:00 +0000
Content-Type: text/html

<html>
<body>
<h1>Important Notice</h1>
<p>This is an <strong>HTML email</strong> with formatting.</p>
<p>Contact: <a href="mailto:support@example.com">support@example.com</a></p>
</body>
</html>
"""
        eml_file = Path(temp_dir) / "html_test.eml"
        eml_file.write_text(html_eml_content)
        
        result = self.extractor.extract(str(eml_file))
        
        assert "Important Notice" in result["extracted_text"]
        assert "HTML email" in result["extracted_text"]
        assert "support@example.com" in result["extracted_text"]
        # HTML tags should be stripped
        assert "<html>" not in result["extracted_text"]
        assert "<strong>" not in result["extracted_text"]
    
    def test_multipart_email_extraction(self, temp_dir):
        """Test multipart email extraction"""
        multipart_content = """From: sender@example.com
To: recipient@example.com
Subject: Multipart Email
Date: Mon, 15 Jan 2024 10:30:00 +0000
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain

This is the plain text part.

--boundary123
Content-Type: text/html

<html><body><p>This is the HTML part.</p></body></html>

--boundary123--
"""
        eml_file = Path(temp_dir) / "multipart.eml"
        eml_file.write_text(multipart_content)
        
        result = self.extractor.extract(str(eml_file))
        
        assert "plain text part" in result["extracted_text"]
        assert "HTML part" in result["extracted_text"]
    
    def test_email_with_quoted_reply(self, temp_dir):
        """Test email with quoted reply extraction"""
        quoted_content = """From: sender@example.com
To: recipient@example.com
Subject: RE: Previous Discussion
Date: Mon, 15 Jan 2024 10:30:00 +0000

Thank you for your message. I agree with your points.

> -----Original Message-----
> From: recipient@example.com
> Sent: Sunday, January 14, 2024
> Subject: Previous Discussion
> 
> I wanted to discuss the project timeline.
> What are your thoughts on the proposed dates?
"""
        eml_file = Path(temp_dir) / "quoted.eml"
        eml_file.write_text(quoted_content)
        
        result = self.extractor.extract(str(eml_file))
        
        assert "Thank you for your message" in result["extracted_text"]
        assert "Previous Discussion" in result["extracted_text"]
        # Should preserve quoted content but identify it
    
    def test_malformed_email_handling(self, temp_dir):
        """Test handling of malformed email files"""
        malformed_content = "This is not a valid email format"
        eml_file = Path(temp_dir) / "malformed.eml"
        eml_file.write_text(malformed_content)
        
        result = self.extractor.extract(str(eml_file))
        
        # Should handle gracefully
        assert "extracted_text" in result
        assert result["confidence"] < 0.5  # Low confidence for malformed


class TestTextExtractor:
    """Test text document extraction functionality"""
    
    def setup_method(self):
        """Set up text extractor"""
        self.extractor = TextExtractor()
    
    def test_supported_extensions(self):
        """Test supported text extensions"""
        assert self.extractor.can_handle("document.txt")
        assert self.extractor.can_handle("readme.md")
        assert self.extractor.can_handle("data.csv")
        assert self.extractor.can_handle("config.json")
        assert not self.extractor.can_handle("image.jpg")
    
    def test_plain_text_extraction(self, temp_dir):
        """Test plain text file extraction"""
        text_content = """Meeting Notes
Date: January 15, 2024
Author: John Doe

Discussion points:
1. Project timeline review
2. Budget allocation
3. Team assignments

Next meeting: January 22, 2024
Contact: john.doe@example.com
"""
        text_file = Path(temp_dir) / "notes.txt"
        text_file.write_text(text_content)
        
        result = self.extractor.extract(str(text_file))
        
        assert result["extracted_text"] == text_content
        assert "detected_language" in result
        assert result["confidence"] > 0.8
        assert "extracted_datetime" in result
        assert "extracted_title" in result
        assert "extracted_author" in result
    
    def test_markdown_extraction(self, temp_dir):
        """Test Markdown file extraction"""
        md_content = """# Project Report
**Date:** January 15, 2024  
**Author:** Jane Smith  

## Executive Summary
This report summarizes the project status as of January 2024.

### Key Findings
- Budget on track: $45,000 spent of $50,000
- Timeline ahead of schedule
- Team performance excellent

### Recommendations
1. Continue current approach
2. Add two team members
3. Increase testing coverage

Contact: jane.smith@company.com
"""
        md_file = Path(temp_dir) / "report.md"
        md_file.write_text(md_content)
        
        result = self.extractor.extract(str(md_file))
        
        assert "Project Report" in result["extracted_text"]
        assert "jane.smith@company.com" in result["extracted_text"]
        assert result["extracted_title"] == "Project Report"
        assert "jane.smith" in result["extracted_author"].lower()
    
    def test_csv_extraction(self, temp_dir):
        """Test CSV file extraction"""
        csv_content = """Date,Event,Location,Participants
2024-01-15,Meeting,New York,John Doe
2024-01-18,Review,Virtual,Jane Smith
2024-01-22,Presentation,Boston,Team
"""
        csv_file = Path(temp_dir) / "events.csv"
        csv_file.write_text(csv_content)
        
        result = self.extractor.extract(str(csv_file))
        
        assert "Date,Event,Location" in result["extracted_text"]
        assert "John Doe" in result["extracted_text"]
        assert result["confidence"] > 0.7
    
    def test_json_extraction(self, temp_dir):
        """Test JSON file extraction"""
        json_content = """{
  "investigation": {
    "id": "INV-2024-001",
    "subject": "System Incident Analysis",
    "start_date": "2024-01-15T00:00:00Z",
    "participants": [
      "john.doe@company.com",
      "jane.smith@company.com"
    ],
    "locations": ["New York", "Boston"],
    "events": [
      {
        "timestamp": "2024-01-15T10:30:00Z",
        "description": "Initial incident reported",
        "severity": "high"
      }
    ]
  }
}"""
        json_file = Path(temp_dir) / "investigation.json"
        json_file.write_text(json_content)
        
        result = self.extractor.extract(str(json_file))
        
        assert "System Incident Analysis" in result["extracted_text"]
        assert "john.doe@company.com" in result["extracted_text"]
        assert result["confidence"] > 0.8
    
    def test_encoding_fallback(self, temp_dir):
        """Test encoding detection and fallback"""
        # Create file with non-UTF8 encoding
        latin1_content = "Café résumé naïve"
        latin1_file = Path(temp_dir) / "latin1.txt"
        
        with open(latin1_file, 'w', encoding='latin1') as f:
            f.write(latin1_content)
        
        result = self.extractor.extract(str(latin1_file))
        
        assert "extracted_text" in result
        assert result["confidence"] > 0.0  # Should handle encoding issues gracefully
    
    def test_empty_file_handling(self, temp_dir):
        """Test handling of empty files"""
        empty_file = Path(temp_dir) / "empty.txt"
        empty_file.write_text("")
        
        result = self.extractor.extract(str(empty_file))
        
        assert result["extracted_text"] == ""
        assert result["confidence"] == 0.0
    
    def test_large_file_handling(self, temp_dir):
        """Test handling of large text files"""
        # Create a large text file
        large_content = "Line of text\n" * 10000  # ~130KB
        large_file = Path(temp_dir) / "large.txt"
        large_file.write_text(large_content)
        
        result = self.extractor.extract(str(large_file))
        
        assert "Line of text" in result["extracted_text"]
        assert result["confidence"] > 0.5


class TestPDFExtractor:
    """Test PDF extraction functionality"""
    
    def setup_method(self):
        """Set up PDF extractor"""
        self.extractor = PDFExtractor()
    
    def test_supported_extensions(self):
        """Test PDF extension support"""
        assert self.extractor.can_handle("document.pdf")
        assert not self.extractor.can_handle("document.txt")
    
    @patch('pdfplumber.open')
    def test_text_layer_extraction(self, mock_pdfplumber, temp_dir):
        """Test PDF text layer extraction"""
        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF text content from layer"
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {
            "Title": "Test PDF Document",
            "Author": "Test Author",
            "CreationDate": "D:20240115103000+00'00'"
        }
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Create dummy PDF file
        pdf_file = Path(temp_dir) / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest content\n%%EOF")
        
        result = self.extractor.extract(str(pdf_file))
        
        assert "PDF text content from layer" in result["extracted_text"]
        assert result["pdf_metadata"]["Title"] == "Test PDF Document"
        assert result["pdf_metadata"]["Author"] == "Test Author"
        assert result["confidence"] > 0.8
    
    @patch('pdfplumber.open')
    @patch('fitz.open')
    @patch('pytesseract.image_to_string')
    def test_ocr_fallback(self, mock_tesseract, mock_fitz, mock_pdfplumber, temp_dir):
        """Test OCR fallback when text layer is empty"""
        # Mock pdfplumber to return empty text
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_doc_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.pil_tobytes.return_value = b"fake image data"
        mock_doc_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__.return_value = mock_doc_page
        mock_doc.__len__.return_value = 1
        mock_fitz.return_value = mock_doc
        
        # Mock tesseract
        mock_tesseract.return_value = "OCR extracted text content"
        
        pdf_file = Path(temp_dir) / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest content\n%%EOF")
        
        result = self.extractor.extract(str(pdf_file))
        
        assert "OCR extracted text content" in result["extracted_text"]
        assert result["extraction_method"] == "ocr"
        assert "ocr_confidence" in result
    
    def test_pdf_datetime_extraction(self, temp_dir):
        """Test datetime extraction from PDF metadata"""
        with patch('pdfplumber.open') as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = []
            mock_pdf.metadata = {
                "CreationDate": "D:20240115103000+00'00'",
                "ModDate": "D:20240115143000+00'00'"
            }
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
            
            pdf_file = Path(temp_dir) / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
            
            result = self.extractor.extract(str(pdf_file))
            
            assert "extracted_datetime" in result
            assert result["extracted_datetime"] is not None


class TestImageExtractor:
    """Test image extraction functionality"""
    
    def setup_method(self):
        """Set up image extractor"""
        self.extractor = ImageExtractor()
    
    def test_supported_extensions(self):
        """Test image extension support"""
        assert self.extractor.can_handle("photo.jpg")
        assert self.extractor.can_handle("scan.png")
        assert self.extractor.can_handle("document.tiff")
        assert not self.extractor.can_handle("document.pdf")
    
    @patch('pytesseract.image_to_string')
    @patch('PIL.Image.open')
    def test_ocr_extraction(self, mock_image_open, mock_tesseract, temp_dir):
        """Test OCR text extraction from images"""
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img._getexif.return_value = {
            306: "2024:01:15 10:30:00",  # DateTime
            270: "Test Image Description"  # ImageDescription
        }
        mock_image_open.return_value = mock_img
        
        # Mock tesseract
        mock_tesseract.return_value = "Text extracted from image via OCR"
        
        # Create dummy image file
        img_file = Path(temp_dir) / "test.jpg"
        img_file.write_bytes(b"\xff\xd8\xff\xe0")  # JPEG header
        
        result = self.extractor.extract(str(img_file))
        
        assert "Text extracted from image via OCR" in result["extracted_text"]
        assert "ocr_confidence" in result
        assert "exif_data" in result
    
    @patch('PIL.Image.open')
    def test_exif_data_extraction(self, mock_image_open, temp_dir):
        """Test EXIF metadata extraction"""
        mock_img = MagicMock()
        mock_img._getexif.return_value = {
            306: "2024:01:15 10:30:00",  # DateTime
            270: "Meeting minutes scan",   # ImageDescription
            271: "Canon EOS R5",          # Make
            272: "Canon",                 # Model
            274: 1,                       # Orientation
            282: (72, 1),                 # XResolution
            283: (72, 1)                  # YResolution
        }
        mock_image_open.return_value = mock_img
        
        img_file = Path(temp_dir) / "test.jpg"
        img_file.write_bytes(b"\xff\xd8\xff\xe0")
        
        with patch('pytesseract.image_to_string', return_value=""):
            result = self.extractor.extract(str(img_file))
        
        assert result["exif_data"]["DateTime"] == "2024:01:15 10:30:00"
        assert result["exif_data"]["ImageDescription"] == "Meeting minutes scan"
        assert result["extracted_title"] == "Meeting minutes scan"
    
    def test_no_exif_handling(self, temp_dir):
        """Test handling images without EXIF data"""
        with patch('PIL.Image.open') as mock_image_open:
            mock_img = MagicMock()
            mock_img._getexif.return_value = None
            mock_image_open.return_value = mock_img
            
            img_file = Path(temp_dir) / "no_exif.png"
            img_file.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG header
            
            with patch('pytesseract.image_to_string', return_value="Image text"):
                result = self.extractor.extract(str(img_file))
            
            assert result["exif_data"] == {}
            assert "Image text" in result["extracted_text"]


class TestExtractorFactory:
    """Test extractor factory functionality"""
    
    def setup_method(self):
        """Set up factory"""
        self.factory = ExtractorFactory()
    
    def test_get_correct_extractor(self):
        """Test factory returns correct extractor for file types"""
        assert isinstance(self.factory.get_extractor("test.eml"), EmailExtractor)
        assert isinstance(self.factory.get_extractor("test.txt"), TextExtractor)
        assert isinstance(self.factory.get_extractor("test.pdf"), PDFExtractor)
        assert isinstance(self.factory.get_extractor("test.jpg"), ImageExtractor)
        assert self.factory.get_extractor("test.unknown") is None
    
    def test_extract_file_method(self, temp_dir):
        """Test factory extract_file method"""
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test content for factory")
        
        result = self.factory.extract_file(str(test_file))
        
        assert "extracted_text" in result
        assert "file_size_bytes" in result
        assert "file_hash" in result
        assert "extractor_type" in result
        assert result["extractor_type"] == "text_file"
    
    def test_supported_extensions_list(self):
        """Test getting list of all supported extensions"""
        extensions = self.factory.get_supported_extensions()
        
        expected_extensions = ['.eml', '.msg', '.txt', '.md', '.csv', '.json', '.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']
        
        for ext in expected_extensions:
            assert ext in extensions
    
    def test_is_supported_method(self):
        """Test is_supported convenience method"""
        assert self.factory.is_supported("document.pdf")
        assert self.factory.is_supported("email.eml")
        assert not self.factory.is_supported("video.mp4")
        assert not self.factory.is_supported("archive.zip")
    
    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files"""
        with pytest.raises(FileNotFoundError):
            self.factory.extract_file("/nonexistent/file.txt")
    
    def test_permission_denied_handling(self, temp_dir):
        """Test handling of permission denied errors"""
        # Create file and remove read permissions
        test_file = Path(temp_dir) / "restricted.txt"
        test_file.write_text("restricted content")
        
        # This test might not work on all systems, so we'll mock it
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                self.factory.extract_file(str(test_file))


class TestExtractorEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_corrupted_file_handling(self, temp_dir):
        """Test handling of corrupted files"""
        # Create corrupted PDF
        corrupted_pdf = Path(temp_dir) / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"corrupted pdf content")
        
        extractor = PDFExtractor()
        
        # Should handle gracefully without crashing
        result = extractor.extract(str(corrupted_pdf))
        assert "extracted_text" in result
        assert result["confidence"] <= 0.5  # Low confidence for corrupted files
    
    def test_very_long_filename(self, temp_dir):
        """Test handling of very long filenames"""
        long_name = "a" * 255 + ".txt"
        long_file = Path(temp_dir) / long_name
        long_file.write_text("content")
        
        factory = ExtractorFactory()
        result = factory.extract_file(str(long_file))
        
        assert "extracted_text" in result
        assert result["original_filename"] == long_name
    
    def test_binary_file_as_text(self, temp_dir):
        """Test handling binary file with text extension"""
        binary_file = Path(temp_dir) / "binary.txt"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
        
        extractor = TextExtractor()
        result = extractor.extract(str(binary_file))
        
        # Should handle gracefully
        assert "extracted_text" in result
        assert result["confidence"] < 0.3  # Very low confidence
    
    def test_missing_dependencies_graceful_degradation(self):
        """Test graceful degradation when optional dependencies missing"""
        
        # Test spaCy missing
        with patch('spacy.load', side_effect=OSError("Model not found")):
            from backend.nlp.entity_extractor import EntityExtractor
            extractor = EntityExtractor()
            
            # Should create blank model as fallback
            assert extractor.nlp is not None
        
        # Test tesseract missing
        with patch('pytesseract.image_to_string', side_effect=FileNotFoundError("tesseract not found")):
            img_extractor = ImageExtractor()
            
            # Should handle OCR failure gracefully
            with patch('PIL.Image.open') as mock_img:
                mock_img.return_value = MagicMock()
                result = img_extractor.extract("fake_image.jpg")
                assert "extracted_text" in result
                assert result["ocr_confidence"] == 0.0


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])