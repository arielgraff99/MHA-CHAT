import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import DatePicker from 'react-datepicker';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { 
  FolderOpenIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon,
  DocumentTextIcon,
  XMarkIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

import { OnboardingState, TimeResolution, BriefRefinement, DiscoveredFile } from '../types';
import apiClient from '../utils/api';

import 'react-datepicker/dist/react-datepicker.css';

const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  
  const [formData, setFormData] = useState<OnboardingState>({
    subject_of_investigation: '',
    start_datetime: '',
    end_datetime: '',
    time_resolution: 'days',
    directory_path: '',
    discovered_files: [],
  });

  const [refinedBrief, setRefinedBrief] = useState<BriefRefinement | null>(null);
  const [briefConfirmed, setBriefConfirmed] = useState(false);

  const steps = [
    { id: 1, name: 'Investigation Setup', description: 'Define what you want to investigate' },
    { id: 2, name: 'Time Range', description: 'Set the temporal boundaries' },
    { id: 3, name: 'Resolution', description: 'Choose timeline granularity' },
    { id: 4, name: 'Select Directory', description: 'Choose folder with source documents' },
    { id: 5, name: 'Review & Confirm', description: 'Confirm and start processing' },
  ];

  const timeResolutionOptions: { value: TimeResolution; label: string; description: string }[] = [
    { value: 'hours', label: 'Hours', description: 'Detailed hour-by-hour timeline' },
    { value: 'days', label: 'Days', description: 'Daily events and activities' },
    { value: 'weeks', label: 'Weeks', description: 'Weekly summary of events' },
    { value: 'months', label: 'Months', description: 'Monthly overview' },
    { value: 'years', label: 'Years', description: 'Yearly high-level summary' },
  ];

  // Supported file extensions
  const supportedExtensions = ['.pdf', '.txt', '.md', '.csv', '.json', '.eml', '.msg', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'];
  
  const handleDirectorySelect = async () => {
    try {
      // Use the File System Access API (modern browsers) or fallback
      if ('showDirectoryPicker' in window) {
        const directoryHandle = await (window as any).showDirectoryPicker({
          mode: 'read'
        });
        
        const files = await scanDirectory(directoryHandle);
        setFormData(prev => ({
          ...prev,
          directory_path: directoryHandle.name,
          discovered_files: files
        }));
        
        toast.success(`Found ${files.filter(f => f.supported).length} supported files in directory`);
      } else {
        // Fallback for browsers that don't support File System Access API
        toast.error('Directory selection not supported in this browser. Please use a modern browser like Chrome, Edge, or Firefox.');
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        toast.error('Failed to select directory');
        console.error('Directory selection error:', error);
      }
    }
  };

  const scanDirectory = async (directoryHandle: any): Promise<DiscoveredFile[]> => {
    const files: DiscoveredFile[] = [];
    
    for await (const entry of directoryHandle.values()) {
      if (entry.kind === 'file') {
        const file = await entry.getFile();
        const extension = '.' + file.name.split('.').pop()?.toLowerCase();
        const isSupported = supportedExtensions.includes(extension);
        
        files.push({
          name: file.name,
          path: file.name, // In browser, we only get the filename
          type: file.type || 'unknown',
          size: file.size,
          extension: extension,
          supported: isSupported
        });
      }
    }
    
    return files.sort((a, b) => a.name.localeCompare(b.name));
  };

  const clearDirectory = () => {
    setFormData(prev => ({
      ...prev,
      directory_path: '',
      discovered_files: []
    }));
  };

  const handleSubjectChange = async (value: string) => {
    setFormData(prev => ({ ...prev, subject_of_investigation: value }));
    
    // Auto-refine brief if enough text
    if (value.length > 10) {
      try {
        const result = await apiClient.refineBrief(value);
        setRefinedBrief(result.refinement);
      } catch (error) {
        console.error('Brief refinement failed:', error);
      }
    }
  };

  const handleConfirmBrief = async (confirmed: boolean) => {
    if (refinedBrief) {
      setBriefConfirmed(confirmed);
      if (confirmed) {
        toast.success('Investigation brief confirmed');
      }
    }
  };

  // Directory validation helper
  const hasValidFiles = () => {
    return formData.discovered_files.some(file => file.supported);
  };

  const canProceedToNextStep = () => {
    switch (currentStep) {
      case 1:
        return formData.subject_of_investigation.length > 0 && (!refinedBrief || briefConfirmed);
      case 2:
        return formData.start_datetime && formData.end_datetime;
      case 3:
        return formData.time_resolution;
      case 4:
        return formData.directory_path && hasValidFiles();
      case 5:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (canProceedToNextStep() && currentStep < 5) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStartProcessing = async () => {
    setIsLoading(true);
    try {
      // Store investigation data in sessionStorage for processing page
      sessionStorage.setItem('investigation_data', JSON.stringify(formData));
      
      toast.success('Starting investigation processing...');
      navigate('/processing');
    } catch (error) {
      toast.error('Failed to start processing');
      setIsLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Progress indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                currentStep >= step.id
                  ? 'border-blue-600 bg-blue-600 text-white'
                  : 'border-gray-300 text-gray-400'
              }`}>
                {currentStep > step.id ? (
                  <CheckCircleIcon className="w-5 h-5" />
                ) : (
                  <span className="text-sm font-medium">{step.id}</span>
                )}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-16 h-0.5 mx-2 ${
                  currentStep > step.id ? 'bg-blue-600' : 'bg-gray-300'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="mt-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {steps[currentStep - 1].name}
          </h2>
          <p className="text-sm text-gray-600">
            {steps[currentStep - 1].description}
          </p>
        </div>
      </div>

      {/* Step content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="card"
        >
          {/* Step 1: Investigation Setup */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  What do you want to investigate?
                </label>
                <textarea
                  value={formData.subject_of_investigation}
                  onChange={(e) => handleSubjectChange(e.target.value)}
                  placeholder="e.g., John Smith's activities during the merger, Company XYZ's communication patterns, Timeline of Project Alpha..."
                  className="input-field h-24 resize-none"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  Describe the person, event, or topic you want to investigate. Be as specific as possible.
                </p>
              </div>

              {/* Brief refinement */}
              {refinedBrief && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="border border-blue-200 rounded-lg p-4 bg-blue-50"
                >
                  <h4 className="font-medium text-blue-900 mb-2">AI-Refined Investigation Brief</h4>
                  <p className="text-blue-800 mb-3">{refinedBrief.refined_brief}</p>
                  
                  {refinedBrief.acceptance_criteria.length > 0 && (
                    <div className="mb-3">
                      <h5 className="font-medium text-blue-900 mb-1">Acceptance Criteria:</h5>
                      <ul className="list-disc list-inside text-sm text-blue-800">
                        {refinedBrief.acceptance_criteria.map((criterion, index) => (
                          <li key={index}>{criterion}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {!briefConfirmed && (
                    <div className="flex space-x-3">
                      <button
                        onClick={() => handleConfirmBrief(true)}
                        className="btn-primary text-sm"
                      >
                        Confirm Brief
                      </button>
                      <button
                        onClick={() => handleConfirmBrief(false)}
                        className="btn-outline text-sm"
                      >
                        Modify
                      </button>
                    </div>
                  )}

                  {briefConfirmed && (
                    <div className="flex items-center text-green-700">
                      <CheckCircleIcon className="w-5 h-5 mr-2" />
                      <span className="text-sm font-medium">Brief confirmed</span>
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          )}

          {/* Step 2: Time Range */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date & Time
                  </label>
                  <DatePicker
                    selected={formData.start_datetime ? new Date(formData.start_datetime) : null}
                    onChange={(date) => {
                      if (date) {
                        setFormData(prev => ({ 
                          ...prev, 
                          start_datetime: date.toISOString() 
                        }));
                      }
                    }}
                    showTimeSelect
                    timeFormat="HH:mm"
                    timeIntervals={15}
                    dateFormat="yyyy-MM-dd HH:mm"
                    className="input-field"
                    placeholderText="Select start date and time"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date & Time
                  </label>
                  <DatePicker
                    selected={formData.end_datetime ? new Date(formData.end_datetime) : null}
                    onChange={(date) => {
                      if (date) {
                        setFormData(prev => ({ 
                          ...prev, 
                          end_datetime: date.toISOString() 
                        }));
                      }
                    }}
                    showTimeSelect
                    timeFormat="HH:mm"
                    timeIntervals={15}
                    dateFormat="yyyy-MM-dd HH:mm"
                    className="input-field"
                    placeholderText="Select end date and time (optional)"
                    minDate={formData.start_datetime ? new Date(formData.start_datetime) : undefined}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Leave empty to use current time
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Time Resolution */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-4">
                  Choose Timeline Resolution
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {timeResolutionOptions.map((option) => (
                    <motion.div
                      key={option.value}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                        formData.time_resolution === option.value
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setFormData(prev => ({ ...prev, time_resolution: option.value }))}
                    >
                      <div className="flex items-center mb-2">
                        <ClockIcon className="w-5 h-5 text-blue-600 mr-2" />
                        <h3 className="font-medium text-gray-900">{option.label}</h3>
                      </div>
                      <p className="text-sm text-gray-600">{option.description}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Directory Selection */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-4">
                  Select Data Directory
                </label>
                
                <div className="space-y-4">
                  {/* Directory Selection Button */}
                  <div
                    onClick={handleDirectorySelect}
                    className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer transition-colors hover:border-gray-400 hover:bg-gray-50"
                  >
                    <FolderOpenIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <div>
                      <p className="text-gray-600 mb-2">
                        Click to select directory
                      </p>
                      <p className="text-sm text-gray-500">
                        Choose the folder containing your investigation documents
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        All supported files in the directory will be analyzed
                      </p>
                    </div>
                  </div>

                  {/* Selected Directory Display */}
                  {formData.directory_path && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <FolderOpenIcon className="h-5 w-5 text-blue-600" />
                          <div>
                            <p className="text-sm font-medium text-blue-900">Selected Directory:</p>
                            <p className="text-sm text-blue-700">{formData.directory_path}</p>
                          </div>
                        </div>
                        <button
                          onClick={clearDirectory}
                          className="text-blue-500 hover:text-blue-700"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                      
                      {formData.discovered_files.length > 0 && (
                        <div className="pt-3 border-t border-blue-200">
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-sm font-medium text-blue-900">
                              Found {formData.discovered_files.filter(f => f.supported).length} supported files:
                            </p>
                            <p className="text-xs text-blue-600">
                              {formData.discovered_files.length - formData.discovered_files.filter(f => f.supported).length} unsupported
                            </p>
                          </div>
                          
                          <div className="max-h-40 overflow-y-auto space-y-1">
                            {formData.discovered_files.slice(0, 15).map((file, index) => (
                              <div key={index} className={`flex items-center justify-between p-2 rounded ${
                                file.supported ? 'bg-white' : 'bg-gray-100'
                              }`}>
                                <div className="flex items-center space-x-2 flex-1 min-w-0">
                                  <DocumentTextIcon className={`h-3 w-3 ${
                                    file.supported ? 'text-green-500' : 'text-gray-400'
                                  }`} />
                                  <span className={`text-xs truncate ${
                                    file.supported ? 'text-blue-700' : 'text-gray-500'
                                  }`}>
                                    {file.name}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs text-blue-500">{file.extension}</span>
                                  <span className="text-xs text-gray-500">{formatFileSize(file.size)}</span>
                                </div>
                              </div>
                            ))}
                            {formData.discovered_files.length > 15 && (
                              <p className="text-xs text-blue-600 text-center py-2">
                                ... and {formData.discovered_files.length - 15} more files
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Supported File Types */}
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-2">Supported file types:</p>
                    <div className="flex flex-wrap justify-center gap-2">
                      {['PDF', 'TXT', 'MD', 'CSV', 'JSON', 'EML', 'MSG', 'JPG', 'PNG', 'TIFF'].map((type) => (
                        <span key={type} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Output Location Notice */}
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <ExclamationCircleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-yellow-800">Output Location</p>
                        <p className="text-sm text-yellow-700 mt-1">
                          All generated files (CSV reports, metadata, analysis results) will be saved 
                          in the same directory as your source data with timestamped filenames.
                        </p>
                        <p className="text-xs text-yellow-600 mt-1">
                          Example: timeline_analysis_2024-01-15_14-30-45.csv
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Review & Confirm */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Review Your Investigation</h3>
                
                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900">Subject</h4>
                    <p className="text-gray-700">{formData.subject_of_investigation}</p>
                    {refinedBrief && briefConfirmed && (
                      <div className="mt-2 p-3 bg-blue-50 rounded border-l-4 border-blue-400">
                        <p className="text-sm text-blue-800">{refinedBrief.refined_brief}</p>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900">Start Date</h4>
                      <p className="text-gray-700">
                        {format(new Date(formData.start_datetime), 'PPpp')}
                      </p>
                    </div>
                    
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900">End Date</h4>
                      <p className="text-gray-700">
                        {formData.end_datetime 
                          ? format(new Date(formData.end_datetime), 'PPpp')
                          : 'Current time'
                        }
                      </p>
                    </div>
                    
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900">Resolution</h4>
                      <p className="text-gray-700 capitalize">{formData.time_resolution}</p>
                    </div>
                  </div>

                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">
                      Data Directory
                    </h4>
                    <div className="flex items-center space-x-2 mb-2">
                      <FolderOpenIcon className="h-4 w-4 text-gray-500" />
                      <p className="text-sm text-gray-700">{formData.directory_path}</p>
                    </div>
                    <div className="text-sm text-gray-600">
                      {formData.discovered_files.filter(f => f.supported).length} supported files • 
                      Total size: {formatFileSize(formData.discovered_files.reduce((sum, file) => sum + file.size, 0))}
                    </div>
                    <div className="mt-2 text-xs text-yellow-700 bg-yellow-50 p-2 rounded">
                      📁 Output files will be saved in the same directory with timestamps
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className={`btn-outline ${currentStep === 1 ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Previous
            </button>

            {currentStep < 5 ? (
              <button
                onClick={handleNext}
                disabled={!canProceedToNextStep()}
                className={`btn-primary flex items-center ${
                  !canProceedToNextStep() ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Next
                <ArrowRightIcon className="w-4 h-4 ml-2" />
              </button>
            ) : (
              <button
                onClick={handleStartProcessing}
                disabled={isLoading || !canProceedToNextStep()}
                className={`btn-primary flex items-center ${
                  isLoading || !canProceedToNextStep() ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Starting...
                  </>
                ) : (
                  <>
                    Start Investigation
                    <ArrowRightIcon className="w-4 h-4 ml-2" />
                  </>
                )}
              </button>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default OnboardingPage;