import os
import re
import json
from typing import Dict, Any, Optional
from datetime import datetime
from .base import BaseExtractor

class TextExtractor(BaseExtractor):
    """Extractor for text files (.txt, .md, .csv, .json)"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.txt', '.md', '.csv', '.json']
        self.extractor_type = "text_file"
        self.encoding_fallbacks = ['utf-8', 'latin-1', 'cp1252']
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from text file"""
        try:
            # Try different encodings
            content = None
            encoding_used = None
            
            for encoding in self.encoding_fallbacks:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("Could not decode file with any supported encoding")
            
            # Extract datetime from filename or content
            datetime_info = self._extract_datetime_from_text(content, file_path)
            
            # Detect language
            detected_language = self._detect_language(content)
            
            # Extract title/subject from content
            title = self._extract_title(content, file_path)
            
            # Extract author if available
            author = self._extract_author(content)
            
            return {
                'extracted_text': content,
                'detected_language': detected_language,
                'extracted_datetime_raw': datetime_info['raw'],
                'extracted_datetime_iso': datetime_info['datetime'],
                'datetime_confidence': datetime_info['confidence'],
                'author_or_sender': author,
                'title_or_subject': title,
                'parse_method': f'text_decode_{encoding_used}',
                'metadata': {
                    'encoding_used': encoding_used,
                    'file_extension': os.path.splitext(file_path)[1],
                    'line_count': len(content.split('\n')),
                    'character_count': len(content)
                }
            }
            
        except Exception as e:
            return {
                'extracted_text': f"Error extracting text file: {str(e)}",
                'detected_language': 'unknown',
                'extracted_datetime_raw': '',
                'extracted_datetime_iso': None,
                'datetime_confidence': 0.0,
                'author_or_sender': '',
                'title_or_subject': os.path.basename(file_path),
                'parse_method': 'error',
                'metadata': {'error': str(e)}
            }
    
    def _extract_datetime_from_text(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract datetime from text content or filename"""
        datetime_patterns = [
            # ISO format
            r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)\b',
            # Date formats
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'\b(\d{1,2}-\d{1,2}-\d{4})\b',
            # Timestamp formats
            r'\b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\b',
            # Human readable dates
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b'
        ]
        
        # Check filename first
        filename = os.path.basename(file_path)
        for pattern in datetime_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                datetime_str = match.group(1)
                dt, confidence = self.normalize_datetime(datetime_str, 0.8)
                if dt:
                    return {
                        'raw': datetime_str,
                        'datetime': dt,
                        'confidence': confidence,
                        'source': 'filename'
                    }
        
        # Check content (first 1000 characters)
        content_sample = content[:1000]
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
                        'source': 'content'
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
    
    def _extract_title(self, content: str, file_path: str) -> str:
        """Extract title from content or use filename"""
        lines = content.split('\n')
        
        # Look for markdown headers
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('#'):
                return line.lstrip('#').strip()
            elif line and not line.startswith(' ') and len(line) < 100:
                # First non-empty, non-indented short line might be title
                return line
        
        # Fallback to filename without extension
        return os.path.splitext(os.path.basename(file_path))[0]
    
    def _extract_author(self, content: str) -> str:
        """Extract author from content"""
        # Look for common author patterns
        author_patterns = [
            r'Author:\s*(.+?)(?:\n|$)',
            r'By:\s*(.+?)(?:\n|$)',
            r'Written by:\s*(.+?)(?:\n|$)',
            r'Created by:\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            from langdetect import detect
            if len(text.strip()) < 10:
                return 'unknown'
            return detect(text)
        except Exception:
            return 'en'  # Default to English