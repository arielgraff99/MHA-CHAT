import re
import hashlib
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from ..config import config
import os

class SecurityManager:
    """Handle security, encryption, and PII protection"""
    
    def __init__(self):
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        }
        
        # Initialize encryption if key is provided
        self.cipher = None
        if config.ENCRYPTION_KEY:
            try:
                self.cipher = Fernet(config.ENCRYPTION_KEY.encode())
            except Exception:
                print("Warning: Invalid encryption key provided")
    
    def hash_pii(self, text: str, pii_type: str) -> str:
        """Hash PII for privacy protection"""
        if not text:
            return text
        
        # Create a consistent hash
        hash_input = f"{pii_type}:{text}".encode('utf-8')
        hash_value = hashlib.sha256(hash_input).hexdigest()[:8]
        
        if pii_type == 'email':
            return f"***@***.*** (hash: {hash_value})"
        elif pii_type == 'phone':
            return f"***-***-**** (hash: {hash_value})"
        elif pii_type == 'ssn':
            return f"***-**-**** (hash: {hash_value})"
        elif pii_type == 'credit_card':
            return f"****-****-****-**** (hash: {hash_value})"
        else:
            return f"[REDACTED:{pii_type}] (hash: {hash_value})"
    
    def redact_pii_in_text(self, text: str, hash_pii: bool = True) -> Dict[str, Any]:
        """
        Redact or hash PII in text
        
        Args:
            text: Input text
            hash_pii: If True, hash PII; if False, redact with placeholders
        
        Returns:
            Dict containing redacted text and PII mapping
        """
        if not text:
            return {'text': text, 'pii_found': {}}
        
        redacted_text = text
        pii_found = {}
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                pii_found[pii_type] = matches
                
                for match in matches:
                    if isinstance(match, tuple):
                        match = ''.join(match)  # For phone numbers with groups
                    
                    if hash_pii:
                        replacement = self.hash_pii(match, pii_type)
                    else:
                        replacement = f"[REDACTED:{pii_type.upper()}]"
                    
                    redacted_text = redacted_text.replace(match, replacement)
        
        return {
            'text': redacted_text,
            'pii_found': pii_found
        }
    
    def encrypt_sensitive_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self.cipher or not data:
            return data
        
        try:
            encrypted = self.cipher.encrypt(data.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            print(f"Encryption failed: {e}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self.cipher or not encrypted_data:
            return encrypted_data
        
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Decryption failed: {e}")
            return encrypted_data
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized
    
    def validate_file_type(self, filename: str, content: bytes) -> bool:
        """Validate file type matches extension"""
        try:
            import magic
            
            # Get MIME type from content
            mime_type = magic.from_buffer(content, mime=True)
            
            # Get extension
            _, ext = os.path.splitext(filename.lower())
            
            # Define expected MIME types for extensions
            expected_mimes = {
                '.pdf': ['application/pdf'],
                '.txt': ['text/plain'],
                '.jpg': ['image/jpeg'],
                '.jpeg': ['image/jpeg'],
                '.png': ['image/png'],
                '.tiff': ['image/tiff'],
                '.bmp': ['image/bmp'],
                '.gif': ['image/gif'],
                '.eml': ['message/rfc822', 'text/plain'],
                '.msg': ['application/vnd.ms-outlook'],
                '.md': ['text/plain', 'text/markdown'],
                '.csv': ['text/csv', 'text/plain'],
                '.json': ['application/json', 'text/plain']
            }
            
            if ext in expected_mimes:
                return mime_type in expected_mimes[ext]
            
            return True  # Allow unknown extensions
            
        except Exception:
            # If magic is not available, skip validation
            return True
    
    def create_audit_hash(self, content: str) -> str:
        """Create hash for audit logging"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def mask_sensitive_fields_for_ui(self, data: Dict[str, Any], reveal_pii: bool = False) -> Dict[str, Any]:
        """Mask sensitive fields in data for UI display"""
        if reveal_pii:
            return data
        
        masked_data = data.copy()
        
        # Fields that might contain PII
        sensitive_fields = ['author_or_sender', 'extracted_text', 'event_summary', 'source_excerpt']
        
        for field in sensitive_fields:
            if field in masked_data and masked_data[field]:
                redaction_result = self.redact_pii_in_text(masked_data[field], hash_pii=True)
                masked_data[field] = redaction_result['text']
                
                # Add PII info to metadata
                if 'pii_info' not in masked_data:
                    masked_data['pii_info'] = {}
                masked_data['pii_info'][field] = redaction_result['pii_found']
        
        return masked_data