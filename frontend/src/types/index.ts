// Investigation types
export interface Investigation {
  id: string;
  subject_of_investigation: string;
  refined_brief?: string;
  start_datetime: string;
  end_datetime?: string;
  time_resolution: TimeResolution;
  status: 'created' | 'ingesting' | 'processing' | 'completed' | 'failed';
  created_timestamp: string;
  updated_timestamp: string;
}

export type TimeResolution = 'years' | 'months' | 'weeks' | 'days' | 'hours';

// Source types
export interface Source {
  id: string;
  source_type: 'email' | 'text_file' | 'pdf' | 'image';
  source_path_or_uid: string;
  original_filename: string;
  file_size_bytes: number;
  mime_type?: string;
  upload_timestamp: string;
  extraction_status: 'pending' | 'processing' | 'completed' | 'failed';
  extraction_metadata?: any;
}

// Extracted text types
export interface ExtractedText {
  id: number;
  source_id: string;
  extracted_text: string;
  detected_language: string;
  extracted_datetime_raw?: string;
  extracted_datetime_iso?: string;
  datetime_confidence: number;
  author_or_sender?: string;
  title_or_subject?: string;
  parse_method: string;
  ingest_timestamp_iso: string;
}

// Event types
export interface Event {
  id: string;
  subject_of_investigation: string;
  event_datetime_iso: string;
  event_datetime_end_iso?: string;
  timezone: string;
  event_title?: string;
  event_summary?: string;
  entities_people: string[];
  entities_orgs: string[];
  entities_locations: string[];
  keywords: string[];
  source_id: string;
  source_excerpt?: string;
  confidence_overall: number;
  inference_notes?: string;
  created_timestamp: string;
}

// Narrative types
export interface NarrativeBlock {
  id: string;
  subject_of_investigation: string;
  time_bucket_label: string;
  start_datetime_iso: string;
  end_datetime_iso: string;
  narrative_text: string;
  event_ids_included: string[];
  evidence_source_ids: string[];
  aggregation_level: TimeResolution;
  llm_model?: string;
  llm_temperature?: number;
  created_timestamp_iso: string;
}

// API response types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}

export interface UploadResponse {
  source_ids: string[];
  message: string;
}

export interface ExtractionResponse {
  extraction_results: Array<{
    source_id: string;
    status: 'completed' | 'failed';
    extracted_text_length?: number;
    detected_language?: string;
    datetime_found?: boolean;
    error?: string;
  }>;
  message: string;
}

export interface EventsResponse {
  events_created: string[];
  message: string;
}

export interface NarrativeResponse {
  narrative_blocks: string[];
  message: string;
}

// UI state types
export interface OnboardingState {
  subject_of_investigation: string;
  start_datetime: string;
  end_datetime: string;
  time_resolution: TimeResolution;
  directory_path: string;
  discovered_files: DiscoveredFile[];
  refined_brief?: {
    original_input: string;
    refined_brief: string;
    acceptance_criteria: string[];
    confidence: number;
    needs_confirmation: boolean;
  };
}

export interface DiscoveredFile {
  name: string;
  path: string;
  type: string;
  size: number;
  extension: string;
  supported: boolean;
}

export interface ProcessingProgress {
  stage: 'ingestion' | 'extraction' | 'normalization' | 'aggregation' | 'narrative';
  progress: number;
  message: string;
  completed_stages: string[];
}

// Brief refinement types
export interface BriefRefinement {
  original_input: string;
  refined_brief: string;
  acceptance_criteria: string[];
  confidence: number;
  refinement_method: 'llm' | 'basic';
  needs_confirmation: boolean;
  confirmed?: boolean;
  status?: 'pending' | 'confirmed' | 'rejected';
}