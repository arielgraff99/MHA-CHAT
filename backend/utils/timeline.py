from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
from ..config import config

class TimelineProcessor:
    """Process and organize events into timeline buckets"""
    
    def __init__(self):
        self.bucket_formatters = {
            'years': lambda dt: dt.strftime('%Y'),
            'months': lambda dt: dt.strftime('%Y-%m'),
            'weeks': lambda dt: f"{dt.strftime('%Y')}-W{dt.isocalendar()[1]:02d}",
            'days': lambda dt: dt.strftime('%Y-%m-%d'),
            'hours': lambda dt: dt.strftime('%Y-%m-%dT%H:00')
        }
    
    def group_events_by_time_resolution(self, events: List[Dict[str, Any]], time_resolution: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group events by time resolution buckets
        
        Args:
            events: List of event dictionaries
            time_resolution: One of 'years', 'months', 'weeks', 'days', 'hours'
        
        Returns:
            Dict mapping time bucket labels to lists of events
        """
        if time_resolution not in self.bucket_formatters:
            raise ValueError(f"Unsupported time resolution: {time_resolution}")
        
        formatter = self.bucket_formatters[time_resolution]
        buckets = defaultdict(list)
        
        for event in events:
            event_dt = event['event_datetime_iso']
            if isinstance(event_dt, str):
                event_dt = datetime.fromisoformat(event_dt.replace('Z', '+00:00'))
            
            bucket_label = formatter(event_dt)
            buckets[bucket_label].append(event)
        
        # Sort buckets by time
        sorted_buckets = {}
        for bucket_label in sorted(buckets.keys()):
            # Sort events within bucket by datetime
            bucket_events = sorted(buckets[bucket_label], key=lambda x: x['event_datetime_iso'])
            sorted_buckets[bucket_label] = bucket_events
        
        return sorted_buckets
    
    def deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate similar events within time window
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Deduplicated list of events
        """
        if not events:
            return events
        
        # Sort events by datetime
        sorted_events = sorted(events, key=lambda x: x['event_datetime_iso'])
        deduplicated = []
        
        for current_event in sorted_events:
            is_duplicate = False
            current_dt = current_event['event_datetime_iso']
            if isinstance(current_dt, str):
                current_dt = datetime.fromisoformat(current_dt.replace('Z', '+00:00'))
            
            # Check against recent events in deduplication window
            for existing_event in reversed(deduplicated):
                existing_dt = existing_event['event_datetime_iso']
                if isinstance(existing_dt, str):
                    existing_dt = datetime.fromisoformat(existing_dt.replace('Z', '+00:00'))
                
                # Check if within time window
                time_diff = abs((current_dt - existing_dt).total_seconds())
                if time_diff > config.DEDUPLICATION_WINDOW_SECONDS:
                    break  # Outside window, stop checking
                
                # Check similarity
                similarity = self._calculate_event_similarity(current_event, existing_event)
                if similarity >= config.SIMILARITY_THRESHOLD:
                    # Merge events (keep earliest, union sources)
                    self._merge_events(existing_event, current_event)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(current_event)
        
        return deduplicated
    
    def _calculate_event_similarity(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> float:
        """Calculate similarity between two events"""
        similarity_score = 0.0
        
        # Title similarity
        title1 = event1.get('event_title', '').lower()
        title2 = event2.get('event_title', '').lower()
        if title1 and title2:
            title_similarity = self._text_similarity(title1, title2)
            similarity_score += title_similarity * 0.4
        
        # Summary similarity
        summary1 = event1.get('event_summary', '').lower()
        summary2 = event2.get('event_summary', '').lower()
        if summary1 and summary2:
            summary_similarity = self._text_similarity(summary1, summary2)
            similarity_score += summary_similarity * 0.4
        
        # Source similarity (same source = higher similarity)
        if event1.get('source_id') == event2.get('source_id'):
            similarity_score += 0.2
        
        return min(similarity_score, 1.0)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple token overlap"""
        if not text1 or not text2:
            return 0.0
        
        # Simple token-based similarity
        tokens1 = set(re.findall(r'\w+', text1.lower()))
        tokens2 = set(re.findall(r'\w+', text2.lower()))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _merge_events(self, existing_event: Dict[str, Any], new_event: Dict[str, Any]) -> None:
        """Merge new event into existing event (keep earliest, union sources)"""
        # Keep the earliest datetime
        existing_dt = existing_event['event_datetime_iso']
        new_dt = new_event['event_datetime_iso']
        
        if isinstance(existing_dt, str):
            existing_dt = datetime.fromisoformat(existing_dt.replace('Z', '+00:00'))
        if isinstance(new_dt, str):
            new_dt = datetime.fromisoformat(new_dt.replace('Z', '+00:00'))
        
        if new_dt < existing_dt:
            existing_event['event_datetime_iso'] = new_event['event_datetime_iso']
        
        # Union source information
        if 'merged_source_ids' not in existing_event:
            existing_event['merged_source_ids'] = [existing_event.get('source_id')]
        
        if new_event.get('source_id') not in existing_event['merged_source_ids']:
            existing_event['merged_source_ids'].append(new_event.get('source_id'))
        
        # Combine summaries if different
        existing_summary = existing_event.get('event_summary', '')
        new_summary = new_event.get('event_summary', '')
        
        if new_summary and new_summary not in existing_summary:
            if existing_summary:
                existing_event['event_summary'] = f"{existing_summary}; {new_summary}"
            else:
                existing_event['event_summary'] = new_summary
        
        # Update confidence (average)
        existing_conf = existing_event.get('confidence_overall', 0.5)
        new_conf = new_event.get('confidence_overall', 0.5)
        existing_event['confidence_overall'] = (existing_conf + new_conf) / 2
    
    def get_time_bucket_boundaries(self, bucket_label: str, time_resolution: str) -> Tuple[datetime, datetime]:
        """
        Get start and end datetime for a time bucket
        
        Args:
            bucket_label: Time bucket label (e.g., "2023-12", "2023-W50")
            time_resolution: Time resolution used
        
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        try:
            if time_resolution == 'years':
                year = int(bucket_label)
                start_dt = datetime(year, 1, 1)
                end_dt = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            
            elif time_resolution == 'months':
                year, month = map(int, bucket_label.split('-'))
                start_dt = datetime(year, month, 1)
                if month == 12:
                    end_dt = datetime(year + 1, 1, 1) - timedelta(seconds=1)
                else:
                    end_dt = datetime(year, month + 1, 1) - timedelta(seconds=1)
            
            elif time_resolution == 'weeks':
                # Parse ISO week format: YYYY-WNN
                year_str, week_str = bucket_label.split('-W')
                year = int(year_str)
                week = int(week_str)
                
                # Get first day of year and find the week
                jan_1 = datetime(year, 1, 1)
                week_1_start = jan_1 - timedelta(days=jan_1.weekday())
                start_dt = week_1_start + timedelta(weeks=week - 1)
                end_dt = start_dt + timedelta(days=7) - timedelta(seconds=1)
            
            elif time_resolution == 'days':
                year, month, day = map(int, bucket_label.split('-'))
                start_dt = datetime(year, month, day)
                end_dt = start_dt + timedelta(days=1) - timedelta(seconds=1)
            
            elif time_resolution == 'hours':
                # Parse format: YYYY-MM-DDTHH:00
                dt_part, hour_part = bucket_label.split('T')
                year, month, day = map(int, dt_part.split('-'))
                hour = int(hour_part.split(':')[0])
                start_dt = datetime(year, month, day, hour)
                end_dt = start_dt + timedelta(hours=1) - timedelta(seconds=1)
            
            else:
                raise ValueError(f"Unsupported time resolution: {time_resolution}")
            
            return start_dt, end_dt
            
        except Exception as e:
            # Fallback: return current time
            now = datetime.now()
            return now, now

# Remove duplicate class definition