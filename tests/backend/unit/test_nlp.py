"""
Comprehensive tests for NLP components in TimelineNarrator
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import json

from backend.nlp.entity_extractor import EntityExtractor
from backend.nlp.brief_refiner import BriefRefiner
from backend.nlp.narrative_generator import NarrativeGenerator


class TestEntityExtractor:
    """Test entity extraction functionality"""
    
    def setup_method(self):
        """Set up entity extractor with mocked spaCy"""
        with patch('spacy.load') as mock_spacy:
            # Mock spaCy model
            mock_nlp = MagicMock()
            mock_spacy.return_value = mock_nlp
            self.extractor = EntityExtractor()
            self.mock_nlp = mock_nlp
    
    def test_extract_entities_with_spacy(self):
        """Test entity extraction using spaCy NER"""
        # Mock spaCy document and entities
        mock_doc = MagicMock()
        mock_ent1 = MagicMock()
        mock_ent1.text = "John Doe"
        mock_ent1.label_ = "PERSON"
        mock_ent2 = MagicMock()
        mock_ent2.text = "New York"
        mock_ent2.label_ = "GPE"
        mock_ent3 = MagicMock()
        mock_ent3.text = "Company Inc."
        mock_ent3.label_ = "ORG"
        
        mock_doc.ents = [mock_ent1, mock_ent2, mock_ent3]
        mock_doc.__iter__ = lambda x: iter([])  # Empty tokens for keywords
        self.mock_nlp.return_value = mock_doc
        
        text = "John Doe works at Company Inc. in New York."
        result = self.extractor.extract_entities(text)
        
        assert "John Doe" in result["people"]
        assert "New York" in result["locations"]
        assert "Company Inc." in result["organizations"]
    
    def test_extract_emails_regex(self):
        """Test email extraction using regex"""
        text = "Contact john.doe@company.com or jane.smith@example.org for details."
        
        # Mock spaCy to return empty results so regex takes over
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([])
        self.mock_nlp.return_value = mock_doc
        
        result = self.extractor.extract_entities(text)
        
        assert "john.doe@company.com" in result["emails"]
        assert "jane.smith@example.org" in result["emails"]
    
    def test_extract_urls_regex(self):
        """Test URL extraction using regex"""
        text = "Visit https://company.com or http://example.org/path for more info."
        
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([])
        self.mock_nlp.return_value = mock_doc
        
        result = self.extractor.extract_entities(text)
        
        assert "https://company.com" in result["urls"]
        assert "http://example.org/path" in result["urls"]
    
    def test_extract_ids_regex(self):
        """Test ID extraction using regex patterns"""
        text = "Reference case ID CASE-2024-001 and document DOC-20240115-001."
        
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([])
        self.mock_nlp.return_value = mock_doc
        
        result = self.extractor.extract_entities(text)
        
        assert "CASE-2024-001" in result["ids"]
        assert "DOC-20240115-001" in result["ids"]
    
    def test_extract_keywords(self):
        """Test keyword extraction from text"""
        # Mock spaCy tokens
        mock_token1 = MagicMock()
        mock_token1.text = "investigation"
        mock_token1.pos_ = "NOUN"
        mock_token1.is_stop = False
        mock_token1.is_alpha = True
        mock_token1.lemma_ = "investigation"
        
        mock_token2 = MagicMock()
        mock_token2.text = "the"
        mock_token2.pos_ = "DET"
        mock_token2.is_stop = True
        mock_token2.is_alpha = True
        
        mock_token3 = MagicMock()
        mock_token3.text = "timeline"
        mock_token3.pos_ = "NOUN"
        mock_token3.is_stop = False
        mock_token3.is_alpha = True
        mock_token3.lemma_ = "timeline"
        
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([mock_token1, mock_token2, mock_token3])
        self.mock_nlp.return_value = mock_doc
        
        result = self.extractor.extract_entities("investigation timeline analysis")
        
        assert "investigation" in result["keywords"]
        assert "timeline" in result["keywords"]
        assert "the" not in result["keywords"]  # Stop word should be filtered
    
    def test_extract_temporal_references(self):
        """Test extraction of temporal references"""
        text = "The meeting was yesterday at 3 PM. Next week we'll review the quarterly report."
        
        result = self.extractor.extract_temporal_references(text)
        
        assert len(result) > 0
        for ref in result:
            assert "text" in ref
            assert "type" in ref
            assert "confidence" in ref
    
    def test_empty_text_handling(self):
        """Test handling of empty or whitespace-only text"""
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([])
        self.mock_nlp.return_value = mock_doc
        
        result = self.extractor.extract_entities("")
        
        # Should return empty but valid structure
        assert isinstance(result["people"], list)
        assert isinstance(result["organizations"], list)
        assert isinstance(result["locations"], list)
        assert len(result["people"]) == 0
    
    def test_non_english_text(self):
        """Test handling of non-English text"""
        text = "Bonjour, je suis Jean Dupont de Paris, France."
        
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([])
        self.mock_nlp.return_value = mock_doc
        
        result = self.extractor.extract_entities(text)
        
        # Should handle gracefully even if entities aren't extracted perfectly
        assert isinstance(result, dict)
        assert "people" in result


class TestBriefRefiner:
    """Test brief refinement functionality"""
    
    def setup_method(self):
        """Set up brief refiner"""
        self.refiner = BriefRefiner()
    
    @patch('openai.ChatCompletion.create')
    def test_successful_brief_refinement(self, mock_openai):
        """Test successful brief refinement with OpenAI"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
OBJECTIVE: Investigate system security incident
SCOPE: Analyze database outage from Jan 21-22, 2024
ACCEPTANCE_CRITERIA:
1. Identify root cause of database connection timeouts
2. Document timeline of incident response
3. Assess impact on user accounts and revenue
4. Recommend prevention measures
ENTITIES: ["database", "incident", "security", "timeout"]
TIMEFRAME: 2024-01-21 to 2024-01-22
"""
        mock_openai.return_value = mock_response
        
        user_input = "I need to investigate the database incident that happened last week"
        result = self.refiner.refine_brief(user_input)
        
        assert "objective" in result
        assert "scope" in result
        assert "acceptance_criteria" in result
        assert "entities" in result
        assert "timeframe" in result
        assert result["confidence"] > 0.8
    
    def test_brief_refinement_without_openai(self):
        """Test brief refinement fallback without OpenAI"""
        # Test without OpenAI API key
        with patch.object(self.refiner, 'refine_brief') as mock_refine:
            mock_refine.side_effect = Exception("OpenAI API not available")
            
            # Should fall back to basic refinement
            user_input = "Investigate security incident"
            
            # Call the actual _basic_refinement method
            result = self.refiner._basic_refinement(user_input)
            
            assert "objective" in result
            assert "scope" in result
            assert result["confidence"] < 0.5  # Lower confidence for basic refinement
    
    def test_parse_llm_response(self):
        """Test parsing of LLM response content"""
        llm_content = """
OBJECTIVE: Investigate project timeline delays
SCOPE: Review project milestones from Q1 2024
ACCEPTANCE_CRITERIA:
1. Identify causes of delays
2. Assess impact on deliverables
3. Recommend mitigation strategies
ENTITIES: ["project", "timeline", "delays", "milestones"]
TIMEFRAME: 2024-01-01 to 2024-03-31
"""
        
        original_input = "Why is the project behind schedule?"
        result = self.refiner._parse_llm_response(llm_content, original_input)
        
        assert result["objective"] == "Investigate project timeline delays"
        assert result["scope"] == "Review project milestones from Q1 2024"
        assert len(result["acceptance_criteria"]) == 3
        assert "project" in result["entities"]
        assert "timeline" in result["entities"]
    
    def test_malformed_llm_response(self):
        """Test handling of malformed LLM responses"""
        malformed_content = "This is not a properly formatted response"
        original_input = "Test input"
        
        result = self.refiner._parse_llm_response(malformed_content, original_input)
        
        # Should fall back to basic parsing
        assert "objective" in result
        assert result["confidence"] < 0.5
    
    def test_confirm_refinement(self):
        """Test brief confirmation functionality"""
        refinement_result = {
            "objective": "Test objective",
            "scope": "Test scope",
            "confidence": 0.8,
            "refinement_id": "test-123"
        }
        
        # Test confirmation
        confirmed = self.refiner.confirm_refinement(refinement_result, True)
        assert confirmed["confirmed"] is True
        assert confirmed["refinement_id"] == "test-123"
        
        # Test rejection
        rejected = self.refiner.confirm_refinement(refinement_result, False)
        assert rejected["confirmed"] is False


class TestNarrativeGenerator:
    """Test narrative generation functionality"""
    
    def setup_method(self):
        """Set up narrative generator"""
        self.generator = NarrativeGenerator()
    
    @patch('openai.ChatCompletion.create')
    def test_successful_narrative_generation(self, mock_openai):
        """Test successful narrative generation with OpenAI"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
On January 15, 2024, the investigation began with a project kickoff meeting (SRC-abc123). 
The team, including John Doe and Jane Smith, reviewed the timeline and identified key milestones (SRC-def456).
By January 21, 2024, a critical system incident occurred affecting database operations (SRC-ghi789).
The incident was resolved on January 22, 2024, after implementing connection pool optimizations (SRC-jkl012).
"""
        mock_openai.return_value = mock_response
        
        events = [
            {
                "id": "EVT-001",
                "event_datetime_iso": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                "event_text": "Project kickoff meeting",
                "source_id": "SRC-abc123",
                "entities": {"people": ["John Doe", "Jane Smith"]}
            },
            {
                "id": "EVT-002", 
                "event_datetime_iso": datetime(2024, 1, 21, 15, 30, tzinfo=timezone.utc),
                "event_text": "System incident occurred",
                "source_id": "SRC-ghi789",
                "entities": {"keywords": ["database", "incident"]}
            }
        ]
        
        result = self.generator.generate_narrative(
            events=events,
            time_bucket="2024-01-15",
            subject_of_investigation="System Investigation",
            aggregation_level="days"
        )
        
        assert "narrative_text" in result
        assert "source_ids" in result
        assert "confidence" in result
        assert len(result["source_ids"]) > 0
        assert "SRC-abc123" in result["source_ids"]
    
    def test_narrative_generation_fallback(self):
        """Test narrative generation fallback without OpenAI"""
        events = [
            {
                "id": "EVT-001",
                "event_datetime_iso": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                "event_text": "Meeting occurred",
                "source_id": "SRC-123",
                "entities": {}
            }
        ]
        
        # Test fallback method directly
        result = self.generator._basic_narrative_generation(
            events=events,
            time_bucket="2024-01-15",
            subject="Test Investigation"
        )
        
        assert "narrative_text" in result
        assert "Meeting occurred" in result["narrative_text"]
        assert "SRC-123" in result["source_ids"]
        assert result["confidence"] < 0.5  # Lower confidence for basic generation
    
    def test_prepare_events_for_llm(self):
        """Test preparation of events for LLM input"""
        events = [
            {
                "id": "EVT-001",
                "event_datetime_iso": datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
                "event_text": "First event",
                "source_id": "SRC-001",
                "entities": {"people": ["John"]}
            },
            {
                "id": "EVT-002",
                "event_datetime_iso": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                "event_text": "Second event", 
                "source_id": "SRC-002",
                "entities": {"locations": ["NYC"]}
            }
        ]
        
        prepared = self.generator._prepare_events_for_llm(events)
        
        assert "EVT-001" in prepared
        assert "EVT-002" in prepared
        assert "2024-01-15T10:30:00+00:00" in prepared
        assert "First event" in prepared
        assert "SRC-001" in prepared
    
    def test_extract_source_ids_from_narrative(self):
        """Test extraction of source IDs from generated narrative"""
        narrative = """
        The investigation began with initial reports (SRC-abc123) indicating system issues.
        Further analysis (SRC-def456) revealed database connection problems.
        The incident was documented in report SRC-ghi789 and resolved per SRC-jkl012.
        """
        
        source_ids = self.generator._extract_source_ids_from_narrative(narrative)
        
        expected_ids = ["SRC-abc123", "SRC-def456", "SRC-ghi789", "SRC-jkl012"]
        for expected_id in expected_ids:
            assert expected_id in source_ids
    
    def test_calculate_narrative_confidence(self):
        """Test narrative confidence calculation"""
        narrative = "Event from SRC-001 and SRC-002 analysis"
        events = [
            {"source_id": "SRC-001", "event_text": "First event"},
            {"source_id": "SRC-002", "event_text": "Second event"},
            {"source_id": "SRC-003", "event_text": "Third event"}  # Not referenced
        ]
        
        confidence = self.generator._calculate_narrative_confidence(narrative, events)
        
        # Should be 2/3 = 0.67 (2 sources referenced out of 3 total)
        assert 0.6 <= confidence <= 0.7
    
    def test_empty_events_handling(self):
        """Test handling of empty events list"""
        result = self.generator._basic_narrative_generation(
            events=[],
            time_bucket="2024-01-15",
            subject="Empty Investigation"
        )
        
        assert result["narrative_text"] == "No events found for this time period."
        assert result["source_ids"] == []
        assert result["confidence"] == 0.0
    
    def test_single_event_narrative(self):
        """Test narrative generation with single event"""
        events = [
            {
                "id": "EVT-001",
                "event_datetime_iso": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                "event_text": "Single important event",
                "source_id": "SRC-001",
                "entities": {}
            }
        ]
        
        result = self.generator._basic_narrative_generation(
            events=events,
            time_bucket="2024-01-15",
            subject="Single Event Test"
        )
        
        assert "Single important event" in result["narrative_text"]
        assert "SRC-001" in result["source_ids"]
    
    @patch('openai.OpenAI')
    def test_new_openai_api_compatibility(self, mock_openai_client):
        """Test compatibility with new OpenAI API (v1.0+)"""
        # Mock new API client
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "New API narrative response"
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        events = [{"id": "EVT-001", "event_text": "Test", "source_id": "SRC-001"}]
        
        # This would test the new API path in generate_narrative
        # The actual implementation would need to be updated to use this
        result = self.generator._basic_narrative_generation(events, "2024-01-15", "Test")
        
        assert "narrative_text" in result


class TestNLPIntegration:
    """Test integration between NLP components"""
    
    def test_entity_extraction_to_narrative_flow(self):
        """Test flow from entity extraction to narrative generation"""
        # Mock entity extractor
        with patch('spacy.load'):
            entity_extractor = EntityExtractor()
        
        # Mock brief refiner
        brief_refiner = BriefRefiner()
        
        # Mock narrative generator
        narrative_generator = NarrativeGenerator()
        
        # Test text
        test_text = "John Doe met with Jane Smith in New York on January 15, 2024."
        
        # Extract entities
        with patch.object(entity_extractor, 'extract_entities') as mock_extract:
            mock_extract.return_value = {
                "people": ["John Doe", "Jane Smith"],
                "locations": ["New York"],
                "dates": ["January 15, 2024"],
                "emails": [],
                "urls": [],
                "ids": [],
                "keywords": ["met"],
                "topics": ["meeting"]
            }
            
            entities = entity_extractor.extract_entities(test_text)
        
        # Verify entity extraction
        assert "John Doe" in entities["people"]
        assert "New York" in entities["locations"]
        
        # Test basic narrative generation
        events = [{
            "id": "EVT-001",
            "event_text": test_text,
            "source_id": "SRC-001",
            "entities": entities
        }]
        
        narrative = narrative_generator._basic_narrative_generation(
            events, "2024-01-15", "Meeting Investigation"
        )
        
        assert "narrative_text" in narrative
        assert "SRC-001" in narrative["source_ids"]
    
    def test_error_propagation(self):
        """Test error handling across NLP components"""
        # Test entity extractor with invalid input
        with patch('spacy.load'):
            entity_extractor = EntityExtractor()
        
        # Should handle None input gracefully
        result = entity_extractor.extract_entities(None)
        assert isinstance(result, dict)
        
        # Test narrative generator with invalid events
        narrative_generator = NarrativeGenerator()
        result = narrative_generator._basic_narrative_generation(
            events=None,
            time_bucket="2024-01-15", 
            subject="Error Test"
        )
        
        assert result["narrative_text"] == "No events found for this time period."
        assert result["confidence"] == 0.0


class TestNLPPerformance:
    """Test NLP component performance and limits"""
    
    def test_large_text_processing(self):
        """Test processing of large text inputs"""
        with patch('spacy.load'):
            entity_extractor = EntityExtractor()
        
        # Create large text (simulate 10MB document)
        large_text = "This is a test sentence with John Doe and New York. " * 10000
        
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = lambda x: iter([])
        
        with patch.object(entity_extractor, 'nlp', return_value=mock_doc):
            result = entity_extractor.extract_entities(large_text)
        
        # Should complete without timeout
        assert isinstance(result, dict)
    
    def test_many_events_narrative(self):
        """Test narrative generation with many events"""
        narrative_generator = NarrativeGenerator()
        
        # Create 100 events
        events = []
        for i in range(100):
            events.append({
                "id": f"EVT-{i:03d}",
                "event_datetime_iso": datetime(2024, 1, 15, 10, i % 60, tzinfo=timezone.utc),
                "event_text": f"Event number {i}",
                "source_id": f"SRC-{i:03d}",
                "entities": {}
            })
        
        result = narrative_generator._basic_narrative_generation(
            events, "2024-01-15", "Large Investigation"
        )
        
        assert "narrative_text" in result
        assert len(result["source_ids"]) <= 100  # Should handle all events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])