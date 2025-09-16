import axios from 'axios';
import { 
  UploadResponse, 
  ExtractionResponse, 
  EventsResponse, 
  NarrativeResponse,
  BriefRefinement,
  Investigation 
} from '../types';

// Configure axios defaults
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000',
  timeout: 300000, // 5 minutes for large file uploads
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiClient = {
  // File ingestion (legacy)
  async ingestFiles(files: File[]): Promise<UploadResponse> {
    if (files.length === 0) {
      return { source_ids: [], message: 'No files provided' };
    }

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post('/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Directory ingestion
  async ingestDirectory(directoryPath: string, discoveredFiles: any[]): Promise<UploadResponse> {
    const response = await api.post('/ingest-directory', {
      directory_path: directoryPath,
      discovered_files: discoveredFiles,
    });
    return response.data;
  },

  // Text extraction
  async extractSources(sourceIds: string[]): Promise<ExtractionResponse> {
    const response = await api.post('/extract', sourceIds);
    return response.data;
  },

  // Event generation
  async generateEvents(
    subject: string,
    startDatetime: string,
    endDatetime?: string
  ): Promise<EventsResponse> {
    const formData = new FormData();
    formData.append('subject', subject);
    formData.append('start_datetime', startDatetime);
    if (endDatetime) {
      formData.append('end_datetime', endDatetime);
    }

    const response = await api.post('/events', formData);
    return response.data;
  },

  // Narrative generation
  async generateNarrative(
    timeResolution: string,
    subject: string,
    startDatetime: string,
    endDatetime?: string
  ): Promise<NarrativeResponse> {
    const formData = new FormData();
    formData.append('time_resolution', timeResolution);
    formData.append('subject', subject);
    formData.append('start_datetime', startDatetime);
    if (endDatetime) {
      formData.append('end_datetime', endDatetime);
    }

    const response = await api.post('/narrative', formData);
    return response.data;
  },

  // Brief refinement
  async refineBrief(
    subjectOfInvestigation: string,
    additionalContext?: string
  ): Promise<{ refinement: BriefRefinement; message: string }> {
    const formData = new FormData();
    formData.append('subject_of_investigation', subjectOfInvestigation);
    if (additionalContext) {
      formData.append('additional_context', additionalContext);
    }

    const response = await api.post('/refine-brief', formData);
    return response.data;
  },

  // Brief confirmation
  async confirmBrief(
    refinementId: string,
    confirmed: boolean
  ): Promise<{ confirmed: boolean; message: string }> {
    const formData = new FormData();
    formData.append('refinement_id', refinementId);
    formData.append('confirmed', confirmed.toString());

    const response = await api.post('/confirm-brief', formData);
    return response.data;
  },

  // Status checking
  async getSourceStatus(sourceId: string): Promise<{
    source_id: string;
    status: string;
    metadata?: any;
    upload_timestamp: string;
  }> {
    const response = await api.get(`/status/${sourceId}`);
    return response.data;
  },

  // Download bundle
  async downloadBundle(): Promise<Blob> {
    const response = await api.get('/download', {
      params: { bundle: true },
      responseType: 'blob',
    });
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{
    status: string;
    timestamp: string;
    version: string;
  }> {
    const response = await api.get('/health');
    return response.data;
  },

  // List investigations
  async getInvestigations(): Promise<{ investigations: Investigation[] }> {
    const response = await api.get('/investigations');
    return response.data;
  },
};

export default apiClient;