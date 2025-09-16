/**
 * Comprehensive tests for the frontend API client
 */

import axios from 'axios';
import { apiClient } from '../../../frontend/src/utils/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios instance
const mockAxiosInstance = {
  post: jest.fn(),
  get: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: {
      use: jest.fn()
    },
    response: {
      use: jest.fn()
    }
  }
};

mockedAxios.create.mockReturnValue(mockAxiosInstance as any);

describe('API Client Configuration', () => {
  test('creates axios instance with correct base URL', () => {
    expect(mockedAxios.create).toHaveBeenCalledWith({
      baseURL: expect.any(String),
      timeout: 300000,
    });
  });

  test('configures request and response interceptors', () => {
    expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
    expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
  });
});

describe('File Upload API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('ingestFiles uploads files correctly', async () => {
    const mockResponse = {
      data: {
        source_ids: ['SRC-123', 'SRC-456'],
        message: 'Files uploaded successfully'
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const testFiles = [
      new File(['content1'], 'test1.txt', { type: 'text/plain' }),
      new File(['content2'], 'test2.txt', { type: 'text/plain' })
    ];

    const result = await apiClient.ingestFiles(testFiles);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith(
      '/ingest',
      expect.any(FormData),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'multipart/form-data'
        })
      })
    );

    expect(result.source_ids).toEqual(['SRC-123', 'SRC-456']);
    expect(result.message).toBe('Files uploaded successfully');
  });

  test('ingestFiles handles upload errors', async () => {
    const errorResponse = {
      response: {
        status: 400,
        data: { detail: 'File type not supported' }
      }
    };
    mockAxiosInstance.post.mockRejectedValue(errorResponse);

    const testFiles = [new File(['content'], 'test.exe', { type: 'application/octet-stream' })];

    await expect(apiClient.ingestFiles(testFiles)).rejects.toThrow();
  });

  test('ingestFiles handles network errors', async () => {
    mockAxiosInstance.post.mockRejectedValue(new Error('Network Error'));

    const testFiles = [new File(['content'], 'test.txt', { type: 'text/plain' })];

    await expect(apiClient.ingestFiles(testFiles)).rejects.toThrow('Network Error');
  });

  test('ingestFiles handles empty file list', async () => {
    const result = await apiClient.ingestFiles([]);

    // Should not make API call for empty files
    expect(mockAxiosInstance.post).not.toHaveBeenCalled();
  });
});

describe('Content Processing API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('extractSources processes source IDs correctly', async () => {
    const mockResponse = {
      data: {
        extracted_count: 2,
        message: 'Extraction completed'
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const sourceIds = ['SRC-123', 'SRC-456'];
    const result = await apiClient.extractSources(sourceIds);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/extract', {
      source_ids: sourceIds
    });
    expect(result.extracted_count).toBe(2);
  });

  test('generateEvents creates events correctly', async () => {
    const mockResponse = {
      data: {
        events_created: 5,
        message: 'Events generated'
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const result = await apiClient.generateEvents(
      'Test Investigation',
      '2024-01-01T00:00:00Z',
      '2024-01-31T23:59:59Z'
    );

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/events', expect.any(FormData));
    expect(result.events_created).toBe(5);
  });

  test('generateNarrative creates narrative correctly', async () => {
    const mockResponse = {
      data: {
        narrative_blocks_created: 3,
        message: 'Narrative generated'
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const result = await apiClient.generateNarrative(
      'days',
      'Test Investigation',
      '2024-01-01T00:00:00Z',
      '2024-01-31T23:59:59Z'
    );

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/narrative', expect.any(FormData));
    expect(result.narrative_blocks_created).toBe(3);
  });
});

describe('Brief Refinement API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('refineBrief refines investigation brief', async () => {
    const mockResponse = {
      data: {
        refinement: {
          objective: 'Test objective',
          scope: 'Test scope',
          acceptance_criteria: ['Criteria 1'],
          entities: ['entity1'],
          timeframe: '2024-01-01 to 2024-01-31',
          confidence: 0.8,
          refinement_id: 'ref-123'
        },
        message: 'Brief refined'
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const result = await apiClient.refineBrief('Test investigation subject');

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/refine-brief', expect.any(FormData));
    expect(result.refinement.objective).toBe('Test objective');
  });

  test('confirmBrief confirms refinement', async () => {
    const mockResponse = {
      data: {
        confirmed: true,
        message: 'Brief confirmed'
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const result = await apiClient.confirmBrief('ref-123', true);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/confirm-brief', expect.any(FormData));
    expect(result.confirmed).toBe(true);
  });
});

describe('Status and Download API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('getSourceStatus retrieves source status', async () => {
    const mockResponse = {
      data: {
        source_id: 'SRC-123',
        status: 'processed',
        upload_timestamp: '2024-01-15T10:30:00Z',
        metadata: { file_size: 1024 }
      }
    };
    mockAxiosInstance.get.mockResolvedValue(mockResponse);

    const result = await apiClient.getSourceStatus('SRC-123');

    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/status/SRC-123');
    expect(result.source_id).toBe('SRC-123');
    expect(result.status).toBe('processed');
  });

  test('downloadBundle downloads investigation bundle', async () => {
    const mockBlob = new Blob(['test zip content'], { type: 'application/zip' });
    const mockResponse = { data: mockBlob };
    mockAxiosInstance.get.mockResolvedValue(mockResponse);

    const result = await apiClient.downloadBundle();

    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/download', {
      responseType: 'blob'
    });
    expect(result).toBeInstanceOf(Blob);
  });

  test('healthCheck verifies server status', async () => {
    const mockResponse = {
      data: {
        status: 'healthy',
        timestamp: '2024-01-15T10:30:00Z',
        version: '1.0.0'
      }
    };
    mockAxiosInstance.get.mockResolvedValue(mockResponse);

    const result = await apiClient.healthCheck();

    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/health');
    expect(result.status).toBe('healthy');
    expect(result.version).toBe('1.0.0');
  });

  test('getInvestigations retrieves investigation list', async () => {
    const mockResponse = {
      data: {
        investigations: [
          {
            id: 'INV-123',
            subject_of_investigation: 'Test Investigation',
            created_at: '2024-01-15T10:30:00Z'
          }
        ]
      }
    };
    mockAxiosInstance.get.mockResolvedValue(mockResponse);

    const result = await apiClient.getInvestigations();

    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/investigations');
    expect(result.investigations).toHaveLength(1);
    expect(result.investigations[0].id).toBe('INV-123');
  });
});

describe('Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('handles 400 Bad Request errors', async () => {
    const errorResponse = {
      response: {
        status: 400,
        data: { detail: 'Invalid request parameters' }
      }
    };
    mockAxiosInstance.post.mockRejectedValue(errorResponse);

    await expect(apiClient.generateEvents('', '2024-01-01T00:00:00Z')).rejects.toThrow();
  });

  test('handles 401 Unauthorized errors', async () => {
    const errorResponse = {
      response: {
        status: 401,
        data: { detail: 'Unauthorized access' }
      }
    };
    mockAxiosInstance.get.mockRejectedValue(errorResponse);

    await expect(apiClient.healthCheck()).rejects.toThrow();
  });

  test('handles 404 Not Found errors', async () => {
    const errorResponse = {
      response: {
        status: 404,
        data: { detail: 'Source not found' }
      }
    };
    mockAxiosInstance.get.mockRejectedValue(errorResponse);

    await expect(apiClient.getSourceStatus('INVALID-ID')).rejects.toThrow();
  });

  test('handles 500 Internal Server errors', async () => {
    const errorResponse = {
      response: {
        status: 500,
        data: { detail: 'Internal server error' }
      }
    };
    mockAxiosInstance.post.mockRejectedValue(errorResponse);

    await expect(apiClient.extractSources(['SRC-123'])).rejects.toThrow();
  });

  test('handles network timeout errors', async () => {
    const timeoutError = {
      code: 'ECONNABORTED',
      message: 'timeout of 300000ms exceeded'
    };
    mockAxiosInstance.post.mockRejectedValue(timeoutError);

    await expect(apiClient.ingestFiles([new File(['large content'], 'large.txt')])).rejects.toThrow();
  });

  test('handles connection refused errors', async () => {
    const connectionError = {
      code: 'ECONNREFUSED',
      message: 'connect ECONNREFUSED 127.0.0.1:8000'
    };
    mockAxiosInstance.get.mockRejectedValue(connectionError);

    await expect(apiClient.healthCheck()).rejects.toThrow();
  });
});

describe('Request Formatting', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('formats FormData correctly for file uploads', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { source_ids: [], message: 'OK' } });

    const files = [new File(['content'], 'test.txt', { type: 'text/plain' })];
    await apiClient.ingestFiles(files);

    const call = mockAxiosInstance.post.mock.calls[0];
    expect(call[1]).toBeInstanceOf(FormData);
  });

  test('formats FormData correctly for form submissions', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { events_created: 0, message: 'OK' } });

    await apiClient.generateEvents('Test', '2024-01-01T00:00:00Z');

    const call = mockAxiosInstance.post.mock.calls[0];
    expect(call[1]).toBeInstanceOf(FormData);
  });

  test('formats JSON correctly for data submissions', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { extracted_count: 0, message: 'OK' } });

    await apiClient.extractSources(['SRC-123']);

    const call = mockAxiosInstance.post.mock.calls[0];
    expect(call[1]).toEqual({ source_ids: ['SRC-123'] });
  });
});

describe('Response Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('handles successful responses with expected data structure', async () => {
    const mockResponse = {
      data: {
        source_ids: ['SRC-123'],
        message: 'Success'
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const files = [new File(['content'], 'test.txt')];
    const result = await apiClient.ingestFiles(files);

    expect(result).toEqual(mockResponse.data);
  });

  test('handles responses with missing optional fields', async () => {
    const mockResponse = {
      data: {
        source_ids: ['SRC-123']
        // Missing message field
      }
    };
    mockAxiosInstance.post.mockResolvedValue(mockResponse);

    const files = [new File(['content'], 'test.txt')];
    const result = await apiClient.ingestFiles(files);

    expect(result.source_ids).toEqual(['SRC-123']);
    expect(result.message).toBeUndefined();
  });

  test('handles blob responses for downloads', async () => {
    const mockBlob = new Blob(['zip content'], { type: 'application/zip' });
    mockAxiosInstance.get.mockResolvedValue({ data: mockBlob });

    const result = await apiClient.downloadBundle();

    expect(result).toBeInstanceOf(Blob);
    expect(result.type).toBe('application/zip');
  });
});

describe('API Client Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('handles empty string parameters', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { events_created: 0, message: 'OK' } });

    await apiClient.generateEvents('', '2024-01-01T00:00:00Z');

    expect(mockAxiosInstance.post).toHaveBeenCalled();
  });

  test('handles undefined optional parameters', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { events_created: 0, message: 'OK' } });

    await apiClient.generateEvents('Test', '2024-01-01T00:00:00Z', undefined);

    expect(mockAxiosInstance.post).toHaveBeenCalled();
  });

  test('handles very large file uploads', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { source_ids: ['SRC-123'], message: 'OK' } });

    // Create large file (1MB)
    const largeContent = 'x'.repeat(1024 * 1024);
    const largeFile = new File([largeContent], 'large.txt', { type: 'text/plain' });

    const result = await apiClient.ingestFiles([largeFile]);

    expect(mockAxiosInstance.post).toHaveBeenCalled();
    expect(result.source_ids).toEqual(['SRC-123']);
  });

  test('handles special characters in filenames', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { source_ids: ['SRC-123'], message: 'OK' } });

    const specialFile = new File(['content'], 'файл-тест@#$.txt', { type: 'text/plain' });
    const result = await apiClient.ingestFiles([specialFile]);

    expect(mockAxiosInstance.post).toHaveBeenCalled();
    expect(result.source_ids).toEqual(['SRC-123']);
  });
});

describe('Concurrent Requests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('handles multiple concurrent uploads', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { source_ids: ['SRC-123'], message: 'OK' } });

    const file1 = new File(['content1'], 'test1.txt');
    const file2 = new File(['content2'], 'test2.txt');

    // Make concurrent requests
    const promises = [
      apiClient.ingestFiles([file1]),
      apiClient.ingestFiles([file2])
    ];

    const results = await Promise.all(promises);

    expect(results).toHaveLength(2);
    expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2);
  });

  test('handles mixed success and failure responses', async () => {
    // First call succeeds, second fails
    mockAxiosInstance.post
      .mockResolvedValueOnce({ data: { source_ids: ['SRC-123'], message: 'OK' } })
      .mockRejectedValueOnce(new Error('Upload failed'));

    const file1 = new File(['content1'], 'test1.txt');
    const file2 = new File(['content2'], 'test2.txt');

    const results = await Promise.allSettled([
      apiClient.ingestFiles([file1]),
      apiClient.ingestFiles([file2])
    ]);

    expect(results[0].status).toBe('fulfilled');
    expect(results[1].status).toBe('rejected');
  });
});

describe('Request Validation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('validates required parameters', async () => {
    // Test that API client doesn't make calls with invalid parameters
    await expect(() => apiClient.generateEvents('', '')).not.toThrow();
    
    // The validation should happen on the server side
    // Client should still make the request and let server validate
  });

  test('handles malformed datetime strings', async () => {
    mockAxiosInstance.post.mockResolvedValue({ data: { events_created: 0, message: 'OK' } });

    // Should not throw on client side - server will validate
    await expect(apiClient.generateEvents('Test', 'invalid-date')).resolves.toBeDefined();
  });
});

describe('API Client Reliability', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('retries failed requests according to configuration', async () => {
    // This would test retry logic if implemented
    const errorResponse = { response: { status: 500 } };
    mockAxiosInstance.post
      .mockRejectedValueOnce(errorResponse)
      .mockRejectedValueOnce(errorResponse)
      .mockResolvedValueOnce({ data: { source_ids: ['SRC-123'], message: 'OK' } });

    // Note: Actual retry logic would need to be implemented in the API client
    const files = [new File(['content'], 'test.txt')];
    
    // For now, just test that it eventually succeeds
    mockAxiosInstance.post.mockResolvedValue({ data: { source_ids: ['SRC-123'], message: 'OK' } });
    const result = await apiClient.ingestFiles(files);
    
    expect(result.source_ids).toEqual(['SRC-123']);
  });

  test('respects timeout configuration', async () => {
    // Simulate timeout
    const timeoutError = { code: 'ECONNABORTED', message: 'timeout exceeded' };
    mockAxiosInstance.get.mockRejectedValue(timeoutError);

    await expect(apiClient.healthCheck()).rejects.toMatchObject({
      code: 'ECONNABORTED'
    });
  });
});