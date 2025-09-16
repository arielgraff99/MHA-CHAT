import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { 
  CalendarIcon, 
  ClockIcon, 
  DocumentTextIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

import { Event, OnboardingState } from '../types';
import apiClient from '../utils/api';

const TimelinePage: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [investigationData, setInvestigationData] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [showPII, setShowPII] = useState(false);
  const [viewMode, setViewMode] = useState<'timeline' | 'table'>('timeline');

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    try {
      // Load processing results from sessionStorage
      const resultsData = sessionStorage.getItem('processing_results');
      const investigationData = sessionStorage.getItem('investigation_data');
      
      if (!resultsData || !investigationData) {
        toast.error('No results found. Please start a new investigation.');
        return;
      }

      const results = JSON.parse(resultsData);
      const invData: OnboardingState = JSON.parse(investigationData);
      
      setInvestigationData(invData);
      
      // For demo purposes, create mock events based on the processing results
      const mockEvents: Event[] = results.eventsCreated.map((eventId: string, index: number) => ({
        id: eventId,
        subject_of_investigation: invData.subject_of_investigation,
        event_datetime_iso: new Date(Date.now() - (index * 24 * 60 * 60 * 1000)).toISOString(),
        timezone: 'America/Toronto',
        event_title: `Event ${index + 1}`,
        event_summary: `This is a sample event extracted from the uploaded documents. Event ${index + 1} contains relevant information about ${invData.subject_of_investigation}.`,
        entities_people: ['John Doe', 'Jane Smith'],
        entities_orgs: ['Company ABC', 'Organization XYZ'],
        entities_locations: ['Toronto', 'New York'],
        keywords: ['meeting', 'document', 'timeline'],
        source_id: results.sourceIds[index % results.sourceIds.length],
        source_excerpt: `Excerpt from source document containing information about this event...`,
        confidence_overall: 0.8 + (Math.random() * 0.2),
        created_timestamp: new Date().toISOString()
      }));

      setEvents(mockEvents);
      setLoading(false);
      
    } catch (error) {
      console.error('Failed to load results:', error);
      toast.error('Failed to load timeline data');
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await apiClient.downloadBundle();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `timeline_export_${Date.now()}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Export downloaded successfully');
    } catch (error) {
      toast.error('Failed to download export');
    }
  };

  const formatConfidence = (confidence: number) => {
    return `${Math.round(confidence * 100)}%`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="card text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading timeline data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Timeline</h1>
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
              Export Data
            </button>
          </div>
        </div>
      </div>

      {/* View mode toggle */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
          <button
            onClick={() => setViewMode('timeline')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'timeline' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Timeline View
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'table' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Table View
          </button>
        </div>
      </div>

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Event Timeline</h2>
          
          {events.length === 0 ? (
            <div className="text-center py-12">
              <CalendarIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No events found for the specified criteria.</p>
            </div>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-300"></div>
              
              {/* Events */}
              <div className="space-y-6">
                {events.map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="relative flex items-start"
                  >
                    {/* Timeline dot */}
                    <div className="absolute left-5 w-3 h-3 bg-blue-600 rounded-full border-2 border-white shadow-md"></div>
                    
                    {/* Event content */}
                    <div className="ml-12 flex-1">
                      <div 
                        className="card cursor-pointer hover:shadow-lg transition-shadow"
                        onClick={() => setSelectedEvent(event)}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-semibold text-gray-900">{event.event_title}</h3>
                            <div className="flex items-center text-sm text-gray-500 mt-1">
                              <ClockIcon className="w-4 h-4 mr-1" />
                              {format(new Date(event.event_datetime_iso), 'PPpp')}
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`text-sm font-medium ${getConfidenceColor(event.confidence_overall)}`}>
                              {formatConfidence(event.confidence_overall)}
                            </span>
                            <p className="text-xs text-gray-500 mt-1">Confidence</p>
                          </div>
                        </div>
                        
                        <p className="text-gray-700 mb-3">{event.event_summary}</p>
                        
                        {/* Entities */}
                        <div className="flex flex-wrap gap-2">
                          {event.entities_people.slice(0, 3).map((person, idx) => (
                            <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                              👤 {person}
                            </span>
                          ))}
                          {event.entities_orgs.slice(0, 2).map((org, idx) => (
                            <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                              🏢 {org}
                            </span>
                          ))}
                          {event.entities_locations.slice(0, 2).map((location, idx) => (
                            <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                              📍 {location}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Events Table</h2>
          
          {events.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No events found for the specified criteria.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date & Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Event
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entities
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confidence
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {events.map((event) => (
                    <tr 
                      key={event.id} 
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => setSelectedEvent(event)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {format(new Date(event.event_datetime_iso), 'MMM dd, yyyy HH:mm')}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{event.event_title}</div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {event.event_summary}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {event.entities_people.slice(0, 2).map((person, idx) => (
                            <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              {person}
                            </span>
                          ))}
                          {event.entities_orgs.slice(0, 1).map((org, idx) => (
                            <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              {org}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${getConfidenceColor(event.confidence_overall)}`}>
                          {formatConfidence(event.confidence_overall)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {event.source_id}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Event Details</h3>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">{selectedEvent.event_title}</h4>
                  <div className="flex items-center text-sm text-gray-500 mt-1">
                    <ClockIcon className="w-4 h-4 mr-1" />
                    {format(new Date(selectedEvent.event_datetime_iso), 'PPpp')}
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Summary</h5>
                  <p className="text-gray-700">{selectedEvent.event_summary}</p>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Entities</h5>
                  <div className="space-y-2">
                    {selectedEvent.entities_people.length > 0 && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">People: </span>
                        <span className="text-sm text-gray-700">{selectedEvent.entities_people.join(', ')}</span>
                      </div>
                    )}
                    {selectedEvent.entities_orgs.length > 0 && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Organizations: </span>
                        <span className="text-sm text-gray-700">{selectedEvent.entities_orgs.join(', ')}</span>
                      </div>
                    )}
                    {selectedEvent.entities_locations.length > 0 && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Locations: </span>
                        <span className="text-sm text-gray-700">{selectedEvent.entities_locations.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Source Information</h5>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Source ID: {selectedEvent.source_id}</p>
                    <p className="text-sm text-gray-600 mb-2">
                      Confidence: <span className={getConfidenceColor(selectedEvent.confidence_overall)}>
                        {formatConfidence(selectedEvent.confidence_overall)}
                      </span>
                    </p>
                    <div>
                      <span className="text-sm font-medium text-gray-600">Excerpt: </span>
                      <p className="text-sm text-gray-700 mt-1">{selectedEvent.source_excerpt}</p>
                    </div>
                  </div>
                </div>

                {selectedEvent.keywords.length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">Keywords</h5>
                    <div className="flex flex-wrap gap-2">
                      {selectedEvent.keywords.map((keyword, idx) => (
                        <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200">
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="btn-primary w-full"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Summary stats */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600">{events.length}</div>
          <div className="text-sm text-gray-600">Total Events</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">
            {new Set(events.flatMap(e => e.entities_people)).size}
          </div>
          <div className="text-sm text-gray-600">People</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-600">
            {new Set(events.flatMap(e => e.entities_orgs)).size}
          </div>
          <div className="text-sm text-gray-600">Organizations</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-orange-600">
            {new Set(events.map(e => e.source_id)).size}
          </div>
          <div className="text-sm text-gray-600">Sources</div>
        </div>
      </div>
    </div>
  );

  function formatConfidence(confidence: number): string {
    return `${Math.round(confidence * 100)}%`;
  }

  function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  }
};

export default TimelinePage;