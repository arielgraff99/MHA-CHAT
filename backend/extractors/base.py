from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import os

class BaseExtractor(ABC):
    """Base class for all file extractors"""
    
    def __init__(self):
        self.supported_extensions = []
        self.extractor_type = ""
    
    @abstractmethod
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and metadata from file
        
        Returns:
            Dict containing:
            - extracted_text: str
            - detected_language: str
            - extracted_datetime_raw: str
            - extracted_datetime_iso: datetime
            - datetime_confidence: float (0.0-1.0)
            - author_or_sender: str
            - title_or_subject: str
            - parse_method: str
            - metadata: dict
        """
        pass
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this extractor can handle the given file"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.supported_extensions
    
    def get_file_hash(self, file_path: str) -> str:
        """Generate hash of file content for deduplication"""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic file information"""
        stat = os.stat(file_path)
        return {
            'file_size_bytes': stat.st_size,
            'modified_timestamp': datetime.fromtimestamp(stat.st_mtime),
            'created_timestamp': datetime.fromtimestamp(stat.st_ctime),
            'file_hash': self.get_file_hash(file_path)
        }
    
    def normalize_datetime(self, datetime_str: str, confidence: float = 0.5) -> Tuple[Optional[datetime], float]:
        """
        Normalize datetime string to datetime object
        
        Returns:
            Tuple of (datetime_obj, confidence_score)
        """
        from dateutil import parser
        import pytz
        from ..config import config
        
        if not datetime_str:
            return None, 0.0
        
        try:
            # Try to parse the datetime
            dt = parser.parse(datetime_str, fuzzy=True)
            
            # If no timezone info, assume default timezone
            if dt.tzinfo is None:
                tz = pytz.timezone(config.DEFAULT_TIMEZONE)
                dt = tz.localize(dt)
            
            # Convert to UTC for storage
            dt_utc = dt.astimezone(pytz.UTC)
            
            return dt_utc, min(confidence + 0.2, 1.0)  # Boost confidence for successful parse
            
        except Exception as e:
            return None, 0.0