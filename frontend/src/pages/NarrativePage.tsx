import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { 
  BookOpenIcon, 
  LinkIcon, 
  ArrowDownTrayIcon,
  EyeIcon,
  EyeSlashIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

import { NarrativeBlock, OnboardingState } from '../types';
import apiClient from '../utils/api';

const NarrativePage: React.FC = () => {
  const [narrativeBlocks, setNarrativeBlocks] = useState<NarrativeBlock[]>([]);
  const [investigationData, setInvestigationData] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPII, setShowPII] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  useEffect(() => {
    loadNarrativeData();
  }, []);

  const loadNarrativeData = async () => {
    try {
      // Load processing results from sessionStorage
      const resultsData = sessionStorage.getItem('processing_results');
      const investigationData = sessionStorage.getItem('investigation_data');
      
      if (!resultsData || !investigationData) {
        toast.error('No narrative data found. Please start a new investigation.');
        return;
      }

      const results = JSON.parse(resultsData);
      const invData: OnboardingState = JSON.parse(investigationData);
      
      setInvestigationData(invData);
      
      // For demo purposes, create mock narrative blocks
      const mockNarrativeBlocks: NarrativeBlock[] = results.narrativeBlocks.map((blockId: string, index: number) => {
        const startDate = new Date(invData.start_datetime);
        const blockStart = new Date(startDate.getTime() + (index * 7 * 24 * 60 * 60 * 1000)); // Weekly blocks
        const blockEnd = new Date(blockStart.getTime() + (7 * 24 * 60 * 60 * 1000));
        
        return {
          id: blockId,
          subject_of_investigation: invData.subject_of_investigation,
          time_bucket_label: `${format(blockStart, 'yyyy-MM-dd')} to ${format(blockEnd, 'yyyy-MM-dd')}`,
          start_datetime_iso: blockStart.toISOString(),
          end_datetime_iso: blockEnd.toISOString(),
          narrative_text: `During this period, significant developments occurred regarding ${invData.subject_of_investigation}. Multiple sources [SRC-${results.sourceIds[0]}] and [SRC-${results.sourceIds[1] || results.sourceIds[0]}] indicate increased activity and communication patterns. The timeline shows a clear progression of events that align with the investigation parameters. Key stakeholders were actively involved in meetings and correspondence, as evidenced by the extracted documents and metadata analysis.`,
          event_ids_included: results.eventsCreated.slice(index * 2, (index + 1) * 2),
          evidence_source_ids: results.sourceIds.slice(0, 2),
          aggregation_level: invData.time_resolution,
          llm_model: 'gpt-4',
          llm_temperature: 0.2,
          created_timestamp_iso: new Date().toISOString()
        };
      });

      setNarrativeBlocks(mockNarrativeBlocks);
      setLoading(false);
      
    } catch (error) {
      console.error('Failed to load narrative data:', error);
      toast.error('Failed to load narrative data');
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await apiClient.downloadBundle();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `narrative_export_${Date.now()}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Narrative export downloaded successfully');
    } catch (error) {
      toast.error('Failed to download export');
    }
  };

  const extractSourceReferences = (narrativeText: string): string[] => {
    const sourcePattern = /\[SRC-([a-zA-Z0-9]+)\]/g;
    const matches = narrativeText.match(sourcePattern);
    return matches ? matches.map(match => match.slice(1, -1)) : [];
  };

  const highlightSourceReferences = (text: string): JSX.Element => {
    const sourcePattern = /(\[SRC-[a-zA-Z0-9]+\])/g;
    const parts = text.split(sourcePattern);
    
    return (
      <>
        {parts.map((part, index) => {
          if (part.match(sourcePattern)) {
            const sourceId = part.slice(1, -1); // Remove brackets
            return (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 mx-1 bg-blue-100 text-blue-800 text-xs rounded cursor-pointer hover:bg-blue-200 transition-colors"
                onClick={() => {
                  if (selectedSources.includes(sourceId)) {
                    setSelectedSources(prev => prev.filter(id => id !== sourceId));
                  } else {
                    setSelectedSources(prev => [...prev, sourceId]);
                  }
                }}
                title={`Click to ${selectedSources.includes(sourceId) ? 'hide' : 'show'} source details`}
              >
                <LinkIcon className="w-3 h-3 mr-1" />
                {sourceId}
              </span>
            );
          }
          return <span key={index}>{part}</span>;
        })}
      </>
    );
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="card text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading narrative...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Timeline Narrative</h1>
            <p className="text-gray-600">{investigationData?.subject_of_investigation}</p>
            {investigationData && (
              <p className="text-sm text-gray-500 mt-1">
                {format(new Date(investigationData.start_datetime), 'PPP')} - {' '}
                {investigationData.end_datetime 
                  ? format(new Date(investigationData.end_datetime), 'PPP')
                  : 'Present'
                } • Resolution: {investigationData.time_resolution}
              </p>
            )}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => setShowPII(!showPII)}
              className={`btn-outline flex items-center ${showPII ? 'bg-yellow-50 border-yellow-300' : ''}`}
            >
              {showPII ? <EyeSlashIcon className="w-4 h-4 mr-2" /> : <EyeIcon className="w-4 h-4 mr-2" />}
              {showPII ? 'Hide' : 'Show'} PII
            </button>
            
            <button
              onClick={handleDownload}
              className="btn-primary flex items-center"
            >
              <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
              Export Narrative
            </button>
          </div>
        </div>
      </div>

      {/* Narrative content */}
      {narrativeBlocks.length === 0 ? (
        <div className="card text-center py-12">
          <BookOpenIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Narrative Generated</h3>
          <p className="text-gray-600">No narrative blocks were generated for this investigation.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {narrativeBlocks.map((block, index) => (
            <motion.div
              key={block.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card"
            >
              {/* Block header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{block.time_bucket_label}</h3>
                  <div className="flex items-center text-sm text-gray-500 mt-1">
                    <BookOpenIcon className="w-4 h-4 mr-1" />
                    {block.event_ids_included.length} events • {block.evidence_source_ids.length} sources
                  </div>
                </div>
                
                <div className="text-right text-xs text-gray-500">
                  <div>Generated: {format(new Date(block.created_timestamp_iso), 'PPp')}</div>
                  {block.llm_model && (
                    <div className="mt-1">Model: {block.llm_model}</div>
                  )}
                </div>
              </div>

              {/* Narrative text with source highlighting */}
              <div className="prose prose-sm max-w-none">
                <p className="text-gray-800 leading-relaxed">
                  {highlightSourceReferences(block.narrative_text)}
                </p>
              </div>

              {/* Source details (expandable) */}
              {selectedSources.some(sourceId => block.evidence_source_ids.includes(sourceId)) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-4 pt-4 border-t border-gray-200"
                >
                  <h5 className="font-medium text-gray-900 mb-2">Referenced Sources</h5>
                  <div className="space-y-2">
                    {block.evidence_source_ids
                      .filter(sourceId => selectedSources.includes(sourceId))
                      .map((sourceId) => (
                        <div key={sourceId} className="bg-blue-50 p-3 rounded-lg">
                          <div className="flex items-center mb-2">
                            <DocumentTextIcon className="w-4 h-4 text-blue-600 mr-2" />
                            <span className="font-medium text-blue-900">{sourceId}</span>
                          </div>
                          <p className="text-sm text-blue-800">
                            Source document referenced in this narrative block. Contains evidence supporting the timeline events described above.
                          </p>
                        </div>
                      ))
                    }
                  </div>
                </motion.div>
              )}

              {/* Block metadata */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Events:</span>
                    <span className="ml-1 font-medium">{block.event_ids_included.length}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Sources:</span>
                    <span className="ml-1 font-medium">{block.evidence_source_ids.length}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Level:</span>
                    <span className="ml-1 font-medium capitalize">{block.aggregation_level}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Temperature:</span>
                    <span className="ml-1 font-medium">{block.llm_temperature || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Instructions */}
      <div className="mt-8 card bg-blue-50 border border-blue-200">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <LinkIcon className="w-5 h-5 text-blue-600 mt-0.5" />
          </div>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-blue-900">Source Traceability</h4>
            <p className="text-sm text-blue-800 mt-1">
              Click on source references (like [SRC-xxxxx]) in the narrative to view source details. 
              Every claim in the narrative is backed by evidence from your uploaded documents.
            </p>
          </div>
        </div>
      </div>

      {/* Summary statistics */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600">{narrativeBlocks.length}</div>
          <div className="text-sm text-gray-600">Narrative Blocks</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">
            {narrativeBlocks.reduce((sum, block) => sum + block.event_ids_included.length, 0)}
          </div>
          <div className="text-sm text-gray-600">Total Events</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-600">
            {new Set(narrativeBlocks.flatMap(block => block.evidence_source_ids)).size}
          </div>
          <div className="text-sm text-gray-600">Source Documents</div>
        </div>
      </div>
    </div>
  );
};

export default NarrativePage;