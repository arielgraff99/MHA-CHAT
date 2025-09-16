import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import pytesseract
from .base import BaseExtractor

class ImageExtractor(BaseExtractor):
    """Extractor for image files with OCR and EXIF support"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']
        self.extractor_type = "image"
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from image file"""
        try:
            # Open image
            with Image.open(file_path) as img:
                # Extract EXIF data
                exif_data = self._extract_exif_data(img)
                
                # Perform OCR
                ocr_text = self._extract_text_with_ocr(img)
                
                # Extract datetime from EXIF or filename
                datetime_info = self._extract_datetime_from_image(exif_data, file_path)
                
                # Extract author from EXIF
                author = exif_data.get('Artist', '') or exif_data.get('Author', '')
                
                # Generate title from filename or OCR content
                title = self._extract_title_from_image(ocr_text, file_path)
                
                # Detect language of OCR text
                detected_language = self._detect_language(ocr_text)
                
                return {
                    'extracted_text': ocr_text,
                    'detected_language': detected_language,
                    'extracted_datetime_raw': datetime_info['raw'],
                    'extracted_datetime_iso': datetime_info['datetime'],
                    'datetime_confidence': datetime_info['confidence'],
                    'author_or_sender': author,
                    'title_or_subject': title,
                    'parse_method': 'ocr_tesseract',
                    'metadata': {
                        'image_format': img.format,
                        'image_mode': img.mode,
                        'image_size': img.size,
                        'exif_data': exif_data,
                        'ocr_confidence': self._get_ocr_confidence(img)
                    }
                }
                
        except Exception as e:
            return {
                'extracted_text': f"Error extracting image: {str(e)}",
                'detected_language': 'unknown',
                'extracted_datetime_raw': '',
                'extracted_datetime_iso': None,
                'datetime_confidence': 0.0,
                'author_or_sender': '',
                'title_or_subject': os.path.basename(file_path),
                'parse_method': 'error',
                'metadata': {'error': str(e)}
            }
    
    def _extract_exif_data(self, img: Image.Image) -> Dict[str, Any]:
        """Extract EXIF metadata from image"""
        exif_data = {}
        
        try:
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
        except Exception:
            pass
        
        return exif_data
    
    def _extract_text_with_ocr(self, img: Image.Image) -> str:
        """Extract text from image using OCR"""
        try:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(img, lang='eng')
            return text.strip()
            
        except Exception as e:
            return f"OCR failed: {str(e)}"
    
    def _get_ocr_confidence(self, img: Image.Image) -> float:
        """Get OCR confidence score"""
        try:
            # Get detailed OCR data with confidence scores
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            
            if confidences:
                return sum(confidences) / len(confidences) / 100.0
            else:
                return 0.0
                
        except Exception:
            return 0.5  # Default confidence
    
    def _extract_datetime_from_image(self, exif_data: Dict, file_path: str) -> Dict[str, Any]:
        """Extract datetime from image EXIF or filename"""
        # Check EXIF data for datetime
        datetime_tags = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
        
        for tag in datetime_tags:
            if tag in exif_data and exif_data[tag]:
                datetime_str = str(exif_data[tag])
                dt, confidence = self.normalize_datetime(datetime_str, 0.9)
                if dt:
                    return {
                        'raw': datetime_str,
                        'datetime': dt,
                        'confidence': confidence,
                        'source': f'exif_{tag}'
                    }
        
        # Check filename for datetime patterns
        filename = os.path.basename(file_path)
        datetime_patterns = [
            r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b(\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2})\b',  # Common camera format
            r'\b(\d{8}_\d{6})\b'  # YYYYMMDD_HHMMSS
        ]
        
        for pattern in datetime_patterns:
            match = re.search(pattern, filename)
            if match:
                datetime_str = match.group(1)
                # Handle camera format
                if '_' in datetime_str and len(datetime_str) == 15:  # YYYYMMDD_HHMMSS
                    formatted_str = f"{datetime_str[:4]}-{datetime_str[4:6]}-{datetime_str[6:8]} {datetime_str[9:11]}:{datetime_str[11:13]}:{datetime_str[13:15]}"
                    dt, confidence = self.normalize_datetime(formatted_str, 0.8)
                else:
                    dt, confidence = self.normalize_datetime(datetime_str, 0.7)
                
                if dt:
                    return {
                        'raw': datetime_str,
                        'datetime': dt,
                        'confidence': confidence,
                        'source': 'filename'
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
    
    def _extract_title_from_image(self, ocr_text: str, file_path: str) -> str:
        """Extract title from OCR text or use filename"""
        if ocr_text:
            lines = ocr_text.split('\n')
            # Look for title-like text in first few lines
            for line in lines[:5]:
                line = line.strip()
                if line and len(line) > 3 and len(line) < 80:
                    return line
        
        # Fallback to filename without extension
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