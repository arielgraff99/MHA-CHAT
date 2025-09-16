import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { 
  CloudArrowUpIcon, 
  DocumentTextIcon, 
  CogIcon, 
  ChartBarIcon, 
  BookOpenIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

import { OnboardingState, ProcessingProgress } from '../types';
import apiClient from '../utils/api';

const ProcessingPage: React.FC = () => {
  const navigate = useNavigate();
  const [progress, setProgress] = useState<ProcessingProgress>({
    stage: 'ingestion',
    progress: 0,
    message: 'Initializing...',
    completed_stages: []
  });
  const [investigationData, setInvestigationData] = useState<OnboardingState | null>(null);
  const [sourceIds, setSourceIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const stages = [
    { 
      id: 'ingestion', 
      name: 'Ingestion', 
      description: 'Uploading and validating files',
      icon: CloudArrowUpIcon,
      color: 'blue'
    },
    { 
      id: 'extraction', 
      name: 'Extraction', 
      description: 'Extracting text and metadata',
      icon: DocumentTextIcon,
      color: 'green'
    },
    { 
      id: 'normalization', 
      name: 'Normalization', 
      description: 'Processing dates and entities',
      icon: CogIcon,
      color: 'yellow'
    },
    { 
      id: 'aggregation', 
      name: 'Aggregation', 
      description: 'Creating timeline events',
      icon: ChartBarIcon,
      color: 'purple'
    },
    { 
      id: 'narrative', 
      name: 'Narrative', 
      description: 'Generating timeline narrative',
      icon: BookOpenIcon,
      color: 'indigo'
    }
  ];

  useEffect(() => {
    // Load investigation data from sessionStorage
    const data = sessionStorage.getItem('investigation_data');
    if (!data) {
      toast.error('No investigation data found');
      navigate('/');
      return;
    }

    const parsedData: OnboardingState = JSON.parse(data);
    setInvestigationData(parsedData);
    
    // Start processing
    startProcessing(parsedData);
  }, [navigate]);

  const startProcessing = async (data: OnboardingState) => {
    try {
      // Stage 1: Ingestion
      setProgress({
        stage: 'ingestion',
        progress: 10,
        message: 'Uploading files...',
        completed_stages: []
      });

      const uploadResult = await apiClient.ingestDirectory(
        data.directory_path,
        data.discovered_files
      );
      setSourceIds(uploadResult.source_ids);
      
      setProgress({
        stage: 'ingestion',
        progress: 100,
        message: `Processed ${uploadResult.source_ids.length} files from directory`,
        completed_stages: ['ingestion']
      });

      // Stage 2: Extraction
      setProgress({
        stage: 'extraction',
        progress: 10,
        message: 'Extracting text from files...',
        completed_stages: ['ingestion']
      });

      const extractionResult = await apiClient.extractSources(uploadResult.source_ids);
      
      setProgress({
        stage: 'extraction',
        progress: 100,
        message: 'Text extraction completed',
        completed_stages: ['ingestion', 'extraction']
      });

      // Stage 3: Normalization (Events)
      setProgress({
        stage: 'normalization',
        progress: 10,
        message: 'Creating timeline events...',
        completed_stages: ['ingestion', 'extraction']
      });

      const eventsResult = await apiClient.generateEvents(
        data.subject_of_investigation,
        data.start_datetime,
        data.end_datetime
      );

      setProgress({
        stage: 'normalization',
        progress: 100,
        message: `Created ${eventsResult.events_created.length} events`,
        completed_stages: ['ingestion', 'extraction', 'normalization']
      });

      // Stage 4: Aggregation & Stage 5: Narrative
      setProgress({
        stage: 'narrative',
        progress: 10,
        message: 'Generating timeline narrative...',
        completed_stages: ['ingestion', 'extraction', 'normalization', 'aggregation']
      });

      const narrativeResult = await apiClient.generateNarrative(
        data.time_resolution,
        data.subject_of_investigation,
        data.start_datetime,
        data.end_datetime
      );

      setProgress({
        stage: 'narrative',
        progress: 100,
        message: 'Timeline narrative generated successfully',
        completed_stages: ['ingestion', 'extraction', 'normalization', 'aggregation', 'narrative']
      });

      // Store results for timeline page
      sessionStorage.setItem('processing_results', JSON.stringify({
        sourceIds: uploadResult.source_ids,
        eventsCreated: eventsResult.events_created,
        narrativeBlocks: narrativeResult.narrative_blocks,
        investigationData: data
      }));

      // Navigate to timeline after a brief delay
      setTimeout(() => {
        toast.success('Investigation completed successfully!');
        navigate('/timeline');
      }, 2000);

    } catch (error: any) {
      console.error('Processing error:', error);
      setError(error.response?.data?.detail || error.message || 'Processing failed');
      toast.error('Processing failed. Please try again.');
    }
  };

  const getStageStatus = (stageId: string) => {
    if (progress.completed_stages.includes(stageId)) {
      return 'completed';
    } else if (progress.stage === stageId) {
      return 'active';
    } else {
      return 'pending';
    }
  };

  const getStageColor = (stageId: string, baseColor: string) => {
    const status = getStageStatus(stageId);
    if (status === 'completed') {
      return 'green';
    } else if (status === 'active') {
      return baseColor;
    } else {
      return 'gray';
    }
  };

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="card">
          <div className="text-center">
            <ExclamationCircleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing Failed</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="space-x-4">
              <button
                onClick={() => navigate('/')}
                className="btn-primary"
              >
                Start Over
              </button>
              <button
                onClick={() => setError(null)}
                className="btn-outline"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="card">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Processing Investigation
          </h1>
          <p className="text-gray-600">
            {investigationData?.subject_of_investigation}
          </p>
        </div>

        {/* Progress stages */}
        <div className="space-y-6">
          {stages.map((stage, index) => {
            const status = getStageStatus(stage.id);
            const IconComponent = stage.icon;
            const isActive = status === 'active';
            const isCompleted = status === 'completed';
            
            return (
              <motion.div
                key={stage.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-center p-4 rounded-lg border-2 transition-all duration-300 ${
                  isCompleted 
                    ? 'border-green-200 bg-green-50' 
                    : isActive 
                    ? 'border-blue-200 bg-blue-50' 
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className={`flex items-center justify-center w-12 h-12 rounded-full mr-4 ${
                  isCompleted 
                    ? 'bg-green-100' 
                    : isActive 
                    ? 'bg-blue-100' 
                    : 'bg-gray-100'
                }`}>
                  {isCompleted ? (
                    <CheckCircleIcon className="w-6 h-6 text-green-600" />
                  ) : (
                    <IconComponent className={`w-6 h-6 ${
                      isActive ? 'text-blue-600' : 'text-gray-400'
                    }`} />
                  )}
                </div>

                <div className="flex-1">
                  <h3 className={`font-medium ${
                    isCompleted ? 'text-green-900' : isActive ? 'text-blue-900' : 'text-gray-600'
                  }`}>
                    {stage.name}
                  </h3>
                  <p className={`text-sm ${
                    isCompleted ? 'text-green-700' : isActive ? 'text-blue-700' : 'text-gray-500'
                  }`}>
                    {isActive ? progress.message : stage.description}
                  </p>
                </div>

                {isActive && (
                  <div className="ml-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Overall progress bar */}
        <div className="mt-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Overall Progress</span>
            <span>{Math.round((progress.completed_stages.length / stages.length) * 100)}%</span>
          </div>
          <div className="progress-bar">
            <motion.div
              className="progress-fill"
              initial={{ width: 0 }}
              animate={{ width: `${(progress.completed_stages.length / stages.length) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Processing details */}
        {investigationData && (
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Processing Details</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Files:</span>
                <span className="ml-1 font-medium">{investigationData.files.length}</span>
              </div>
              <div>
                <span className="text-gray-500">Resolution:</span>
                <span className="ml-1 font-medium capitalize">{investigationData.time_resolution}</span>
              </div>
              <div>
                <span className="text-gray-500">Sources:</span>
                <span className="ml-1 font-medium">{sourceIds.length}</span>
              </div>
              <div>
                <span className="text-gray-500">Status:</span>
                <span className="ml-1 font-medium capitalize">{progress.stage}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingPage;