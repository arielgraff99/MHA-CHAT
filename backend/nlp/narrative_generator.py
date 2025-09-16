import openai
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..config import config

class NarrativeGenerator:
    """Generate timeline narratives from events using LLM"""
    
    def __init__(self):
        if config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
        
        self.system_prompt = """You are creating a timeline narrative from extracted events. Your task is to summarize events for the specified subject while respecting the date range and preserving chronology.

Guidelines:
- Include only claims supported by the provided sources
- Maintain chronological order
- Attach source IDs for every claim using format [SRC-xxxxx]
- Be objective and factual
- Connect related events when appropriate
- Highlight significant patterns or developments
- Use clear, professional language

Format your response as a coherent narrative paragraph that flows naturally while maintaining source attribution."""
    
    def generate_narrative(self, 
                         events: List[Dict[str, Any]], 
                         time_bucket: str,
                         subject_of_investigation: str,
                         aggregation_level: str) -> Dict[str, Any]:
        """
        Generate narrative for a time bucket of events
        
        Args:
            events: List of event dictionaries
            time_bucket: Time bucket label (e.g., "2023-12", "2023-W50")
            subject_of_investigation: Subject being investigated
            aggregation_level: Level of aggregation (years, months, weeks, days, hours)
        
        Returns:
            Dict containing narrative text, metadata, and source references
        """
        if not events:
            return {
                'narrative_text': f"No events found for {subject_of_investigation} in {time_bucket}.",
                'event_ids_included': [],
                'evidence_source_ids': [],
                'confidence': 0.0,
                'generation_method': 'empty'
            }
        
        try:
            if not config.OPENAI_API_KEY:
                return self._basic_narrative_generation(events, time_bucket, subject_of_investigation)
            
            # Prepare events summary for LLM
            events_summary = self._prepare_events_for_llm(events)
            
            # Create prompt
            prompt = f"""Subject of Investigation: {subject_of_investigation}
Time Period: {time_bucket}
Aggregation Level: {aggregation_level}

Events to summarize:
{events_summary}

Generate a coherent narrative that summarizes these events chronologically, ensuring every claim is attributed to a source ID."""
            
            # Call LLM (compatible with both old and new OpenAI API)
            try:
                # Try new API first (OpenAI v1.0+)
                from openai import OpenAI
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                narrative_text = response.choices[0].message.content.strip()
            except ImportError:
                # Fallback to legacy API
                response = openai.ChatCompletion.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                narrative_text = response.choices[0].message.content.strip()
            
            # Extract source IDs mentioned in narrative
            source_ids = self._extract_source_ids_from_narrative(narrative_text)
            event_ids = [event['id'] for event in events]
            
            return {
                'narrative_text': narrative_text,
                'event_ids_included': event_ids,
                'evidence_source_ids': list(set(source_ids)),
                'confidence': self._calculate_narrative_confidence(narrative_text, events),
                'generation_method': 'llm',
                'llm_model': config.LLM_MODEL,
                'llm_temperature': config.LLM_TEMPERATURE
            }
            
        except Exception as e:
            print(f"LLM narrative generation failed: {str(e)}")
            return self._basic_narrative_generation(events, time_bucket, subject_of_investigation)
    
    def _prepare_events_for_llm(self, events: List[Dict[str, Any]]) -> str:
        """Prepare events summary for LLM input"""
        event_summaries = []
        
        for event in events:
            summary = f"[{event['id']}] {event['event_datetime_iso']}: {event['event_title']}"
            if event.get('event_summary'):
                summary += f" - {event['event_summary']}"
            if event.get('source_excerpt'):
                summary += f" (Source: {event['source_id']})"
            event_summaries.append(summary)
        
        return '\n'.join(event_summaries)
    
    def _extract_source_ids_from_narrative(self, narrative: str) -> List[str]:
        """Extract source IDs mentioned in narrative text"""
        import re
        pattern = r'\[SRC-[a-zA-Z0-9]+\]'
        matches = re.findall(pattern, narrative)
        return [match.strip('[]') for match in matches]
    
    def _calculate_narrative_confidence(self, narrative: str, events: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for generated narrative"""
        if not narrative or not events:
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Boost for source attribution
        source_ids_in_narrative = self._extract_source_ids_from_narrative(narrative)
        if source_ids_in_narrative:
            confidence += 0.3
        
        # Boost for comprehensive coverage
        events_mentioned = len(source_ids_in_narrative)
        total_events = len(events)
        if total_events > 0:
            coverage_ratio = events_mentioned / total_events
            confidence += coverage_ratio * 0.2
        
        return min(confidence, 1.0)
    
    def _basic_narrative_generation(self, events: List[Dict[str, Any]], time_bucket: str, subject: str) -> Dict[str, Any]:
        """Generate basic narrative without LLM"""
        if not events:
            return {
                'narrative_text': f"No events found for {subject} in {time_bucket}.",
                'event_ids_included': [],
                'evidence_source_ids': [],
                'confidence': 0.0,
                'generation_method': 'basic_empty'
            }
        
        # Sort events chronologically
        sorted_events = sorted(events, key=lambda x: x['event_datetime_iso'])
        
        # Create basic narrative
        narrative_parts = []
        narrative_parts.append(f"During {time_bucket}, the following events occurred regarding {subject}:")
        
        for event in sorted_events:
            event_text = f"On {event['event_datetime_iso'].strftime('%Y-%m-%d')}"
            if event.get('event_title'):
                event_text += f", {event['event_title']}"
            if event.get('event_summary'):
                event_text += f": {event['event_summary']}"
            event_text += f" [SRC-{event['source_id']}]"
            narrative_parts.append(event_text)
        
        narrative = '. '.join(narrative_parts) + '.'
        
        return {
            'narrative_text': narrative,
            'event_ids_included': [event['id'] for event in events],
            'evidence_source_ids': list(set([event['source_id'] for event in events])),
            'confidence': 0.6,
            'generation_method': 'basic_template'
        }

# Global narrative generator instance
narrative_generator = NarrativeGenerator()