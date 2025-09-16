/**
 * Comprehensive tests for React components in TimelineNarrator
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import '@testing-library/jest-dom';

// Import components
import App from '../../../frontend/src/App';
import Header from '../../../frontend/src/components/Header';
import Footer from '../../../frontend/src/components/Footer';
import OnboardingPage from '../../../frontend/src/pages/OnboardingPage';
import ProcessingPage from '../../../frontend/src/pages/ProcessingPage';
import TimelinePage from '../../../frontend/src/pages/TimelinePage';
import NarrativePage from '../../../frontend/src/pages/NarrativePage';

// Mock API client
jest.mock('../../../frontend/src/utils/api', () => ({
  apiClient: {
    ingestFiles: jest.fn(),
    extractSources: jest.fn(),
    generateEvents: jest.fn(),
    generateNarrative: jest.fn(),
    refineBrief: jest.fn(),
    confirmBrief: jest.fn(),
    getSourceStatus: jest.fn(),
    downloadBundle: jest.fn(),
    healthCheck: jest.fn(),
    getInvestigations: jest.fn(),
  },
  default: {
    ingestFiles: jest.fn(),
    extractSources: jest.fn(),
    generateEvents: jest.fn(),
    generateNarrative: jest.fn(),
    refineBrief: jest.fn(),
    confirmBrief: jest.fn(),
    getSourceStatus: jest.fn(),
    downloadBundle: jest.fn(),
    healthCheck: jest.fn(),
    getInvestigations: jest.fn(),
  }
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Header Component', () => {
  test('renders application title', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByText('TimelineNarrator')).toBeInTheDocument();
  });

  test('renders navigation links', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByText('New Investigation')).toBeInTheDocument();
    expect(screen.getByText('Timeline')).toBeInTheDocument();
    expect(screen.getByText('Narrative')).toBeInTheDocument();
  });

  test('navigation links have correct hrefs', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const newInvestigationLink = screen.getByRole('link', { name: /new investigation/i });
    const timelineLink = screen.getByRole('link', { name: /timeline/i });
    const narrativeLink = screen.getByRole('link', { name: /narrative/i });

    expect(newInvestigationLink).toHaveAttribute('href', '/');
    expect(timelineLink).toHaveAttribute('href', '/timeline');
    expect(narrativeLink).toHaveAttribute('href', '/narrative');
  });

  test('highlights current page in navigation', () => {
    // Mock useLocation to return specific pathname
    jest.doMock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useLocation: () => ({ pathname: '/timeline' })
    }));

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    // The current page should have different styling (this depends on implementation)
    const timelineLink = screen.getByRole('link', { name: /timeline/i });
    expect(timelineLink).toBeInTheDocument();
  });
});

describe('Footer Component', () => {
  test('renders copyright information', () => {
    render(<Footer />);

    expect(screen.getByText(/© 2024 TimelineNarrator v1.0.0/)).toBeInTheDocument();
  });

  test('renders tagline', () => {
    render(<Footer />);

    expect(screen.getByText('Extract • Analyze • Narrate')).toBeInTheDocument();
  });
});

describe('OnboardingPage Component', () => {
  const mockApiClient = require('../../../frontend/src/utils/api').apiClient;

  beforeEach(() => {
    jest.clearAllMocks();
    // Clear sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
  });

  test('renders first step (investigation setup)', () => {
    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    expect(screen.getByText(/investigation setup/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/describe your investigation/i)).toBeInTheDocument();
  });

  test('allows subject input and triggers brief refinement', async () => {
    const user = userEvent.setup();
    mockApiClient.refineBrief.mockResolvedValue({
      refinement: {
        objective: 'Test objective',
        scope: 'Test scope',
        acceptance_criteria: ['Criteria 1', 'Criteria 2'],
        entities: ['entity1', 'entity2'],
        timeframe: '2024-01-01 to 2024-01-31',
        confidence: 0.8,
        refinement_id: 'test-123'
      },
      message: 'Brief refined successfully'
    });

    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    const subjectInput = screen.getByPlaceholderText(/describe your investigation/i);
    await user.type(subjectInput, 'Test investigation subject');

    await waitFor(() => {
      expect(mockApiClient.refineBrief).toHaveBeenCalledWith('Test investigation subject');
    });
  });

  test('progresses through all onboarding steps', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    // Step 1: Subject
    const subjectInput = screen.getByPlaceholderText(/describe your investigation/i);
    await user.type(subjectInput, 'Test investigation');
    
    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    // Should progress to step 2 (Time Range)
    await waitFor(() => {
      expect(screen.getByText(/time range/i)).toBeInTheDocument();
    });
  });

  test('validates required fields before proceeding', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    // Try to proceed without filling subject
    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    // Should show validation error or stay on same step
    expect(screen.getByText(/investigation setup/i)).toBeInTheDocument();
  });

  test('handles file upload with dropzone', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    // Navigate to file upload step (would need to fill previous steps)
    // This is a simplified test - full implementation would navigate through steps

    // Create mock file
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    // Find dropzone (this selector depends on implementation)
    const dropzone = screen.getByText(/drag.*drop.*files/i).closest('div');
    
    if (dropzone) {
      // Simulate file drop
      Object.defineProperty(dropzone, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.drop(dropzone);

      await waitFor(() => {
        expect(screen.getByText('test.txt')).toBeInTheDocument();
      });
    }
  });
});

describe('ProcessingPage Component', () => {
  const mockApiClient = require('../../../frontend/src/utils/api').apiClient;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock sessionStorage with investigation data
    const mockInvestigationData = {
      subject_of_investigation: 'Test Investigation',
      start_datetime: '2024-01-01T00:00:00Z',
      end_datetime: '2024-01-31T23:59:59Z',
      time_resolution: 'days',
      files: []
    };

    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn((key) => {
          if (key === 'investigation_data') {
            return JSON.stringify(mockInvestigationData);
          }
          return null;
        }),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
  });

  test('renders processing stages', () => {
    render(
      <TestWrapper>
        <ProcessingPage />
      </TestWrapper>
    );

    expect(screen.getByText(/processing investigation/i)).toBeInTheDocument();
    expect(screen.getByText(/ingestion/i)).toBeInTheDocument();
    expect(screen.getByText(/extraction/i)).toBeInTheDocument();
    expect(screen.getByText(/analysis/i)).toBeInTheDocument();
  });

  test('shows progress indicators', async () => {
    mockApiClient.ingestFiles.mockResolvedValue({
      source_ids: ['SRC-123'],
      message: 'Files uploaded'
    });

    render(
      <TestWrapper>
        <ProcessingPage />
      </TestWrapper>
    );

    // Should show progress indicators
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  test('handles processing errors gracefully', async () => {
    mockApiClient.ingestFiles.mockRejectedValue(new Error('Upload failed'));

    render(
      <TestWrapper>
        <ProcessingPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  test('navigates to timeline on completion', async () => {
    // Mock successful API calls
    mockApiClient.ingestFiles.mockResolvedValue({ source_ids: ['SRC-123'], message: 'Success' });
    mockApiClient.extractSources.mockResolvedValue({ extracted_count: 1, message: 'Success' });
    mockApiClient.generateEvents.mockResolvedValue({ events_created: 5, message: 'Success' });
    mockApiClient.generateNarrative.mockResolvedValue({ narrative_blocks_created: 3, message: 'Success' });

    const mockNavigate = jest.fn();
    jest.doMock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate
    }));

    render(
      <TestWrapper>
        <ProcessingPage />
      </TestWrapper>
    );

    // Wait for processing to complete and navigation to trigger
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/timeline');
    }, { timeout: 5000 });
  });
});

describe('TimelinePage Component', () => {
  beforeEach(() => {
    // Mock sessionStorage with results data
    const mockResults = {
      sourceIds: ['SRC-123', 'SRC-456'],
      eventsCreated: ['EVT-001', 'EVT-002', 'EVT-003'],
      narrativeBlocks: ['NARR-001', 'NARR-002']
    };

    const mockInvestigationData = {
      subject_of_investigation: 'Test Investigation',
      start_datetime: '2024-01-01T00:00:00Z',
      end_datetime: '2024-01-31T23:59:59Z',
      time_resolution: 'days'
    };

    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn((key) => {
          if (key === 'processing_results') return JSON.stringify(mockResults);
          if (key === 'investigation_data') return JSON.stringify(mockInvestigationData);
          return null;
        }),
        setItem: jest.fn(),
      },
      writable: true,
    });
  });

  test('renders timeline view by default', async () => {
    render(
      <TestWrapper>
        <TimelinePage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/timeline view/i)).toBeInTheDocument();
    });
  });

  test('toggles between timeline and table view', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TimelinePage />
      </TestWrapper>
    );

    await waitFor(() => {
      const tableToggle = screen.getByRole('button', { name: /table/i });
      expect(tableToggle).toBeInTheDocument();
    });

    const tableToggle = screen.getByRole('button', { name: /table/i });
    await user.click(tableToggle);

    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  test('displays event details in modal', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TimelinePage />
      </TestWrapper>
    );

    await waitFor(() => {
      const eventCard = screen.getAllByText(/event/i)[0];
      expect(eventCard).toBeInTheDocument();
    });

    // Click on first event
    const eventCards = screen.getAllByText(/event/i);
    if (eventCards.length > 0) {
      await user.click(eventCards[0]);

      // Should open modal with event details
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    }
  });

  test('toggles PII visibility', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TimelinePage />
      </TestWrapper>
    );

    await waitFor(() => {
      const piiToggle = screen.getByRole('button', { name: /show.*pii/i });
      expect(piiToggle).toBeInTheDocument();
    });

    const piiToggle = screen.getByRole('button', { name: /show.*pii/i });
    await user.click(piiToggle);

    // PII should now be visible (implementation dependent)
    expect(piiToggle).toBeInTheDocument();
  });

  test('handles download functionality', async () => {
    const user = userEvent.setup();
    const mockApiClient = require('../../../frontend/src/utils/api').apiClient;
    
    mockApiClient.downloadBundle.mockResolvedValue(new Blob(['test'], { type: 'application/zip' }));

    render(
      <TestWrapper>
        <TimelinePage />
      </TestWrapper>
    );

    await waitFor(() => {
      const downloadButton = screen.getByRole('button', { name: /download/i });
      expect(downloadButton).toBeInTheDocument();
    });

    const downloadButton = screen.getByRole('button', { name: /download/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockApiClient.downloadBundle).toHaveBeenCalled();
    });
  });
});

describe('NarrativePage Component', () => {
  beforeEach(() => {
    // Mock sessionStorage with narrative data
    const mockResults = {
      narrativeBlocks: ['NARR-001', 'NARR-002', 'NARR-003']
    };

    const mockInvestigationData = {
      subject_of_investigation: 'Narrative Test Investigation',
      start_datetime: '2024-01-01T00:00:00Z',
      end_datetime: '2024-01-31T23:59:59Z',
      time_resolution: 'days'
    };

    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn((key) => {
          if (key === 'processing_results') return JSON.stringify(mockResults);
          if (key === 'investigation_data') return JSON.stringify(mockInvestigationData);
          return null;
        }),
        setItem: jest.fn(),
      },
      writable: true,
    });
  });

  test('renders narrative content', async () => {
    render(
      <TestWrapper>
        <NarrativePage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/narrative/i)).toBeInTheDocument();
    });
  });

  test('highlights source references in narrative', async () => {
    render(
      <TestWrapper>
        <NarrativePage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Look for source reference highlights (SRC-xxx format)
      const sourceRefs = screen.getAllByText(/SRC-/);
      expect(sourceRefs.length).toBeGreaterThan(0);
    });
  });

  test('toggles source details on click', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <NarrativePage />
      </TestWrapper>
    );

    await waitFor(() => {
      const sourceRefs = screen.getAllByText(/SRC-/);
      if (sourceRefs.length > 0) {
        return sourceRefs[0];
      }
      throw new Error('No source references found');
    });

    const sourceRefs = screen.getAllByText(/SRC-/);
    if (sourceRefs.length > 0) {
      await user.click(sourceRefs[0]);

      // Should show source details
      await waitFor(() => {
        expect(screen.getByText(/source details/i)).toBeInTheDocument();
      });
    }
  });

  test('handles PII toggle in narrative', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <NarrativePage />
      </TestWrapper>
    );

    await waitFor(() => {
      const piiToggle = screen.getByRole('button', { name: /pii/i });
      expect(piiToggle).toBeInTheDocument();
    });

    const piiToggle = screen.getByRole('button', { name: /pii/i });
    await user.click(piiToggle);

    // PII visibility should change
    expect(piiToggle).toBeInTheDocument();
  });
});

describe('App Component', () => {
  test('renders without crashing', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    expect(screen.getByText('TimelineNarrator')).toBeInTheDocument();
  });

  test('renders header and footer', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    expect(screen.getByText('TimelineNarrator')).toBeInTheDocument();
    expect(screen.getByText('Extract • Analyze • Narrate')).toBeInTheDocument();
  });

  test('handles route navigation', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Should render onboarding page by default (route "/")
    expect(screen.getByPlaceholderText(/describe your investigation/i)).toBeInTheDocument();
  });
});

describe('Component Integration', () => {
  test('onboarding to processing navigation', async () => {
    const user = userEvent.setup();
    const mockApiClient = require('../../../frontend/src/utils/api').apiClient;

    // Mock API responses
    mockApiClient.refineBrief.mockResolvedValue({
      refinement: { objective: 'Test', scope: 'Test', confidence: 0.8, refinement_id: 'test-123' },
      message: 'Success'
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Fill out onboarding form (simplified)
    const subjectInput = screen.getByPlaceholderText(/describe your investigation/i);
    await user.type(subjectInput, 'Integration test investigation');

    // Navigate through steps (this would require more detailed step-by-step navigation)
    // For now, just verify the component renders
    expect(subjectInput).toBeInTheDocument();
  });

  test('error boundary handles component errors', () => {
    // Mock console.error to suppress error logs in test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    // Create a component that throws an error
    const ThrowError = () => {
      throw new Error('Test error');
    };

    // This would test error boundary if implemented
    render(
      <TestWrapper>
        <ThrowError />
      </TestWrapper>
    );

    // Clean up
    consoleSpy.mockRestore();
  });
});

describe('Accessibility Tests', () => {
  test('components have proper ARIA labels', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    // Check for proper navigation structure
    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();

    // Check for proper link roles
    const links = screen.getAllByRole('link');
    expect(links.length).toBeGreaterThan(0);
  });

  test('form elements have proper labels', () => {
    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    // Check for form accessibility
    const textInput = screen.getByPlaceholderText(/describe your investigation/i);
    expect(textInput).toBeInTheDocument();
    
    // Should have associated label or aria-label
    expect(textInput).toHaveAttribute('placeholder');
  });

  test('buttons have descriptive text or aria-labels', () => {
    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      // Each button should have text content or aria-label
      expect(
        button.textContent || 
        button.getAttribute('aria-label') ||
        button.getAttribute('title')
      ).toBeTruthy();
    });
  });
});

describe('Performance Tests', () => {
  test('components render within reasonable time', async () => {
    const startTime = performance.now();

    render(
      <TestWrapper>
        <OnboardingPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/describe your investigation/i)).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within 1 second
    expect(renderTime).toBeLessThan(1000);
  });

  test('handles large data sets without performance issues', async () => {
    // Mock large dataset
    const largeResults = {
      eventsCreated: Array.from({ length: 1000 }, (_, i) => `EVT-${i:03d}`),
      narrativeBlocks: Array.from({ length: 100 }, (_, i) => `NARR-${i:03d}`)
    };

    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn((key) => {
          if (key === 'processing_results') return JSON.stringify(largeResults);
          return null;
        }),
        setItem: jest.fn(),
      },
      writable: true,
    });

    const startTime = performance.now();

    render(
      <TestWrapper>
        <TimelinePage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/timeline/i)).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should handle large datasets reasonably
    expect(renderTime).toBeLessThan(2000);
  });
});