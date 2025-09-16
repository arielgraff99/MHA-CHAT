import email
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
import re
from typing import Dict, Any, Optional
from datetime import datetime
from .base import BaseExtractor

class EmailExtractor(BaseExtractor):
    """Extractor for email files (.eml, .msg)"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.eml', '.msg']
        self.extractor_type = "email"
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from email file"""
        try:
            if file_path.lower().endswith('.eml'):
                return self._extract_eml(file_path)
            elif file_path.lower().endswith('.msg'):
                return self._extract_msg(file_path)
            else:
                raise ValueError(f"Unsupported email format: {file_path}")
        except Exception as e:
            return {
                'extracted_text': f"Error extracting email: {str(e)}",
                'detected_language': 'unknown',
                'extracted_datetime_raw': '',
                'extracted_datetime_iso': None,
                'datetime_confidence': 0.0,
                'author_or_sender': '',
                'title_or_subject': '',
                'parse_method': 'error',
                'metadata': {'error': str(e)}
            }
    
    def _extract_eml(self, file_path: str) -> Dict[str, Any]:
        """Extract from .eml file"""
        with open(file_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        
        # Extract headers
        sender = msg.get('From', '')
        recipients = {
            'to': msg.get('To', ''),
            'cc': msg.get('Cc', ''),
            'bcc': msg.get('Bcc', '')
        }
        subject = msg.get('Subject', '')
        date_header = msg.get('Date', '')
        
        # Parse datetime
        sent_datetime = None
        datetime_confidence = 0.0
        if date_header:
            try:
                sent_datetime = parsedate_to_datetime(date_header)
                datetime_confidence = 0.9  # High confidence for email headers
            except Exception:
                sent_datetime, datetime_confidence = self.normalize_datetime(date_header, 0.7)
        
        # Extract body text
        body_text = self._extract_body_text(msg)
        
        # Detect language
        detected_language = self._detect_language(body_text)
        
        return {
            'extracted_text': body_text,
            'detected_language': detected_language,
            'extracted_datetime_raw': date_header,
            'extracted_datetime_iso': sent_datetime,
            'datetime_confidence': datetime_confidence,
            'author_or_sender': sender,
            'title_or_subject': subject,
            'parse_method': 'rfc5322',
            'metadata': {
                'recipients': recipients,
                'message_id': msg.get('Message-ID', ''),
                'in_reply_to': msg.get('In-Reply-To', ''),
                'references': msg.get('References', ''),
                'attachments': self._get_attachments_info(msg)
            }
        }
    
    def _extract_msg(self, file_path: str) -> Dict[str, Any]:
        """Extract from .msg file (Outlook format)"""
        # For .msg files, we'll need a specialized library
        # For now, return a basic implementation
        try:
            # This would require python-msg-extract or similar library
            # For demo purposes, treating as text file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Try to decode as text (very basic approach)
            try:
                text_content = content.decode('utf-8', errors='ignore')
            except:
                text_content = content.decode('latin-1', errors='ignore')
            
            return {
                'extracted_text': text_content,
                'detected_language': 'unknown',
                'extracted_datetime_raw': '',
                'extracted_datetime_iso': None,
                'datetime_confidence': 0.0,
                'author_or_sender': '',
                'title_or_subject': '',
                'parse_method': 'binary_decode',
                'metadata': {'note': 'MSG format requires specialized parser'}
            }
        except Exception as e:
            raise ValueError(f"Failed to extract MSG file: {str(e)}")
    
    def _extract_body_text(self, msg: EmailMessage) -> str:
        """Extract body text from email message"""
        body_parts = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        body_parts.append(part.get_payload(decode=True).decode(charset, errors='ignore'))
                    except Exception:
                        body_parts.append(str(part.get_payload()))
                elif content_type == 'text/html' and not body_parts:
                    # Fallback to HTML if no plain text
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        html_content = part.get_payload(decode=True).decode(charset, errors='ignore')
                        # Basic HTML to text conversion
                        body_parts.append(self._html_to_text(html_content))
                    except Exception:
                        body_parts.append(str(part.get_payload()))
        else:
            # Single part message
            content_type = msg.get_content_type()
            if content_type in ['text/plain', 'text/html']:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    content = msg.get_payload(decode=True).decode(charset, errors='ignore')
                    if content_type == 'text/html':
                        content = self._html_to_text(content)
                    body_parts.append(content)
                except Exception:
                    body_parts.append(str(msg.get_payload()))
        
        # Join all parts and clean up
        full_text = '\n\n'.join(body_parts)
        return self._clean_email_text(full_text)
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        except Exception:
            # Fallback: basic HTML tag removal
            return re.sub(r'<[^>]+>', '', html_content)
    
    def _clean_email_text(self, text: str) -> str:
        """Clean up email text by removing quoted replies and signatures"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip common quote patterns
            if (line.strip().startswith('>') or 
                line.strip().startswith('On ') and 'wrote:' in line or
                line.strip().startswith('-----Original Message-----') or
                line.strip().startswith('From:') and '@' in line):
                break
            
            # Skip signature separators
            if line.strip() in ['--', '___', '***']:
                break
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _get_attachments_info(self, msg: EmailMessage) -> list:
        """Get information about email attachments"""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b'')
                        })
        
        return attachments
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            from langdetect import detect
            if len(text.strip()) < 10:
                return 'unknown'
            return detect(text)
        except Exception:
            return 'en'  # Default to English