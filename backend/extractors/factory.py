from typing import Optional, Dict, Any, List
import os
from .base import BaseExtractor
from .email_extractor import EmailExtractor
from .text_extractor import TextExtractor
from .pdf_extractor import PDFExtractor
from .image_extractor import ImageExtractor

class ExtractorFactory:
    """Factory class to get appropriate extractor for file type"""
    
    def __init__(self):
        self.extractors = [
            EmailExtractor(),
            TextExtractor(),
            PDFExtractor(),
            ImageExtractor()
        ]
    
    def get_extractor(self, file_path: str) -> Optional[BaseExtractor]:
        """Get appropriate extractor for file"""
        for extractor in self.extractors:
            if extractor.can_handle(file_path):
                return extractor
        return None
    
    def extract_file(self, file_path: str) -> Dict[str, Any]:
        """Extract content from file using appropriate extractor"""
        extractor = self.get_extractor(file_path)
        
        if not extractor:
            _, ext = os.path.splitext(file_path)
            return {
                'extracted_text': f"Unsupported file type: {ext}",
                'detected_language': 'unknown',
                'extracted_datetime_raw': '',
                'extracted_datetime_iso': None,
                'datetime_confidence': 0.0,
                'author_or_sender': '',
                'title_or_subject': os.path.basename(file_path),
                'parse_method': 'unsupported',
                'metadata': {'error': f'No extractor available for {ext}'}
            }
        
        # Add file info to result
        result = extractor.extract(file_path)
        file_info = extractor.get_file_info(file_path)
        result['metadata'].update(file_info)
        
        return result
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions"""
        extensions = []
        for extractor in self.extractors:
            extensions.extend(extractor.supported_extensions)
        return list(set(extensions))
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file type is supported"""
        return self.get_extractor(file_path) is not None

# Global factory instance
extractor_factory = ExtractorFactory()