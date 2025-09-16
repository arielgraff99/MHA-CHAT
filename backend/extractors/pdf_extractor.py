import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import PyPDF2
import pdfplumber
from .base import BaseExtractor

class PDFExtractor(BaseExtractor):
    """Extractor for PDF files with text layer and OCR support"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.pdf']
        self.extractor_type = "pdf"
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from PDF file"""
        try:
            # Try text layer extraction first
            text_result = self._extract_text_layer(file_path)
            
            # If text layer extraction fails or yields little text, try OCR
            if not text_result['extracted_text'] or len(text_result['extracted_text'].strip()) < 50:
                ocr_result = self._extract_with_ocr(file_path)
                if ocr_result['extracted_text']:
                    # Merge results, preferring OCR text but keeping metadata
                    text_result['extracted_text'] = ocr_result['extracted_text']
                    text_result['parse_method'] = 'ocr_fallback'
                    text_result['metadata'].update(ocr_result['metadata'])
            
            return text_result
            
        except Exception as e:
            return {
                'extracted_text': f"Error extracting PDF: {str(e)}",
                'detected_language': 'unknown',
                'extracted_datetime_raw': '',
                'extracted_datetime_iso': None,
                'datetime_confidence': 0.0,
                'author_or_sender': '',
                'title_or_subject': os.path.basename(file_path),
                'parse_method': 'error',
                'metadata': {'error': str(e)}
            }
    
    def _extract_text_layer(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF text layer using pdfplumber"""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract metadata
                metadata = pdf.metadata or {}
                
                # Extract text from all pages
                pages_text = []
                page_metadata = []
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    pages_text.append(page_text)
                    
                    page_meta = {
                        'page_number': page_num + 1,
                        'page_width': page.width,
                        'page_height': page.height,
                        'text_length': len(page_text)
                    }
                    page_metadata.append(page_meta)
                
                full_text = '\n\n'.join(pages_text)
                
                # Extract datetime from metadata or content
                datetime_info = self._extract_datetime_from_pdf(metadata, full_text, file_path)
                
                # Extract author and title from metadata
                author = metadata.get('Author', '') or metadata.get('Creator', '')
                title = metadata.get('Title', '') or self._extract_title_from_content(full_text, file_path)
                
                # Detect language
                detected_language = self._detect_language(full_text)
                
                return {
                    'extracted_text': full_text,
                    'detected_language': detected_language,
                    'extracted_datetime_raw': datetime_info['raw'],
                    'extracted_datetime_iso': datetime_info['datetime'],
                    'datetime_confidence': datetime_info['confidence'],
                    'author_or_sender': author,
                    'title_or_subject': title,
                    'parse_method': 'text_layer',
                    'metadata': {
                        'pdf_metadata': metadata,
                        'page_count': len(pdf.pages),
                        'pages_metadata': page_metadata,
                        'total_characters': len(full_text)
                    }
                }
                
        except Exception as e:
            raise ValueError(f"Text layer extraction failed: {str(e)}")
    
    def _extract_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """Extract text using OCR as fallback"""
        try:
            import pytesseract
            from PIL import Image
            import fitz  # PyMuPDF for PDF to image conversion
            
            # Convert PDF pages to images and OCR
            doc = fitz.open(file_path)
            pages_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("ppm")
                
                # Convert to PIL Image
                from io import BytesIO
                img = Image.open(BytesIO(img_data))
                
                # Perform OCR
                page_text = pytesseract.image_to_string(img, lang='eng')
                pages_text.append(page_text)
            
            doc.close()
            full_text = '\n\n'.join(pages_text)
            
            return {
                'extracted_text': full_text,
                'metadata': {
                    'ocr_method': 'tesseract',
                    'pages_processed': len(pages_text)
                }
            }
            
        except Exception as e:
            return {
                'extracted_text': '',
                'metadata': {'ocr_error': str(e)}
            }
    
    def _extract_datetime_from_pdf(self, metadata: Dict, content: str, file_path: str) -> Dict[str, Any]:
        """Extract datetime from PDF metadata or content"""
        # Check PDF metadata first
        for key in ['CreationDate', 'ModDate', 'CreatedDate', 'ModifiedDate']:
            if key in metadata and metadata[key]:
                date_str = str(metadata[key])
                # PDF dates are often in format: D:20231201120000Z
                if date_str.startswith('D:'):
                    date_str = date_str[2:]  # Remove 'D:' prefix
                
                dt, confidence = self.normalize_datetime(date_str, 0.8)
                if dt:
                    return {
                        'raw': str(metadata[key]),
                        'datetime': dt,
                        'confidence': confidence,
                        'source': f'pdf_metadata_{key}'
                    }
        
        # Check content for dates
        datetime_patterns = [
            r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
        ]
        
        content_sample = content[:2000]  # Check first 2000 characters
        for pattern in datetime_patterns:
            match = re.search(pattern, content_sample, re.IGNORECASE)
            if match:
                datetime_str = match.group(1)
                dt, confidence = self.normalize_datetime(datetime_str, 0.6)
                if dt:
                    return {
                        'raw': datetime_str,
                        'datetime': dt,
                        'confidence': confidence,
                        'source': 'pdf_content'
                    }
        
        # Fallback to file modification time
        stat = os.stat(file_path)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        return {
            'raw': str(mod_time),
            'datetime': mod_time,
            'confidence': 0.3,
            'source': 'file_mtime'
        }
    
    def _extract_title_from_content(self, content: str, file_path: str) -> str:
        """Extract title from PDF content"""
        lines = content.split('\n')
        
        # Look for title-like text in first few lines
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) > 5 and len(line) < 100:
                # Check if line looks like a title (not too long, not too short)
                if not re.match(r'^\d+$', line) and not line.startswith('Page '):
                    return line
        
        # Fallback to filename
        return os.path.splitext(os.path.basename(file_path))[0]
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            from langdetect import detect
            if len(text.strip()) < 10:
                return 'unknown'
            return detect(text)
        except Exception:
            return 'en'  # Default to English