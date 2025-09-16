import spacy
import re
from typing import Dict, List, Any
from datetime import datetime
from ..config import config

class EntityExtractor:
    """Extract entities from text using spaCy NLP"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load(config.SPACY_MODEL)
        except OSError:
            # Fallback to basic English model or download
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # If no model available, use blank model
                self.nlp = spacy.blank("en")
                print("Warning: No spaCy model available. Entity extraction will be limited.")
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text
        
        Returns:
            Dict with entity types as keys and lists of entities as values
        """
        if not text or len(text.strip()) < 10:
            return self._empty_entities()
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            entities = {
                'people': [],
                'organizations': [],
                'locations': [],
                'dates': [],
                'times': [],
                'emails': [],
                'urls': [],
                'ids': [],
                'topics': [],
                'keywords': []
            }
            
            # Extract named entities
            for ent in doc.ents:
                entity_text = ent.text.strip()
                if len(entity_text) < 2:
                    continue
                
                if ent.label_ in ['PERSON']:
                    entities['people'].append(entity_text)
                elif ent.label_ in ['ORG']:
                    entities['organizations'].append(entity_text)
                elif ent.label_ in ['GPE', 'LOC']:  # Geopolitical entities, locations
                    entities['locations'].append(entity_text)
                elif ent.label_ in ['DATE']:
                    entities['dates'].append(entity_text)
                elif ent.label_ in ['TIME']:
                    entities['times'].append(entity_text)
            
            # Extract emails using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            entities['emails'].extend(emails)
            
            # Extract URLs using regex
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, text)
            entities['urls'].extend(urls)
            
            # Extract potential IDs (alphanumeric strings that look like identifiers)
            id_pattern = r'\b[A-Z0-9]{3,}-[A-Z0-9]{3,}\b|\b[A-Z]{2,}\d{3,}\b'
            ids = re.findall(id_pattern, text)
            entities['ids'].extend(ids)
            
            # Extract keywords using noun phrases
            keywords = self._extract_keywords(doc)
            entities['keywords'].extend(keywords)
            
            # Extract topics using simple heuristics
            topics = self._extract_topics(doc)
            entities['topics'].extend(topics)
            
            # Deduplicate and clean
            for key in entities:
                entities[key] = list(set([item.strip() for item in entities[key] if item.strip()]))
            
            return entities
            
        except Exception as e:
            print(f"Entity extraction error: {str(e)}")
            return self._empty_entities()
    
    def _extract_keywords(self, doc) -> List[str]:
        """Extract keywords from spaCy doc"""
        keywords = []
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text) > 3 and len(chunk.text) < 50:
                keywords.append(chunk.text.strip())
        
        # Extract important single tokens
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 3):
                keywords.append(token.text)
        
        return keywords[:20]  # Limit to top 20 keywords
    
    def _extract_topics(self, doc) -> List[str]:
        """Extract potential topics from text"""
        topics = []
        
        # Look for patterns that indicate topics
        topic_patterns = [
            r'regarding\s+(.+?)(?:\.|,|\n)',
            r'about\s+(.+?)(?:\.|,|\n)',
            r'concerning\s+(.+?)(?:\.|,|\n)',
            r'subject:\s*(.+?)(?:\n|$)',
            r're:\s*(.+?)(?:\n|$)'
        ]
        
        text = doc.text
        for pattern in topic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            topics.extend([match.strip() for match in matches])
        
        return topics[:10]  # Limit to top 10 topics
    
    def _empty_entities(self) -> Dict[str, List[str]]:
        """Return empty entities structure"""
        return {
            'people': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'times': [],
            'emails': [],
            'urls': [],
            'ids': [],
            'topics': [],
            'keywords': []
        }
    
    def extract_temporal_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract temporal references with context"""
        temporal_refs = []
        
        # Patterns for temporal expressions
        temporal_patterns = [
            (r'\b(yesterday|today|tomorrow)\b', 'relative_day'),
            (r'\b(last|this|next)\s+(week|month|year)\b', 'relative_period'),
            (r'\b(morning|afternoon|evening|night)\b', 'time_of_day'),
            (r'\b(\d{1,2}:\d{2}\s*(?:AM|PM)?)\b', 'time'),
            (r'\b(before|after|during|while)\s+(.+?)(?:\.|,|\n)', 'temporal_relation')
        ]
        
        for pattern, ref_type in temporal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                temporal_refs.append({
                    'text': match.group(0),
                    'type': ref_type,
                    'start_pos': match.start(),
                    'end_pos': match.end(),
                    'context': text[max(0, match.start()-50):match.end()+50]
                })
        
        return temporal_refs

# Global entity extractor instance
entity_extractor = EntityExtractor()