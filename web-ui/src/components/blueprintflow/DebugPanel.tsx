import { useState } from 'react';
import { ChevronUp, ChevronDown, Bug, Clock, FileJson, AlertTriangle } from 'lucide-react';
import JSONViewer from '../debug/JSONViewer';
import RequestTimeline from '../debug/RequestTimeline';
import ErrorPanel from '../debug/ErrorPanel';
import type { RequestTrace } from '../../types/api';
import { useMonitoringStore } from '../../store/monitoringStore';

interface DebugPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  executionResult?: Record<string, unknown> | null;
  executionError?: string | null;
}

type TabType = 'timeline' | 'request' | 'response' | 'errors';

export default function DebugPanel({ isOpen, onToggle, executionResult, executionError }: DebugPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('timeline');
  const [selectedTrace, setSelectedTrace] = useState<RequestTrace | null>(null);

  const { traces } = useMonitoringStore();

  // Filter workflow-related traces
  const workflowTraces = traces.filter(
    (t) => t.endpoint.includes('workflow') ||
           t.endpoint.includes('detect') ||
           t.endpoint.includes('ocr') ||
           t.endpoint.includes('segment')
  );

  const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'timeline', label: 'Timeline', icon: <Clock className="w-4 h-4" /> },
    { id: 'request', label: 'Request', icon: <Bug className="w-4 h-4" /> },
    { id: 'response', label: 'Response', icon: <FileJson className="w-4 h-4" /> },
    { id: 'errors', label: 'Errors', icon: <AlertTriangle className="w-4 h-4" /> },
  ];

  if (!isOpen) {
    return (
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center gap-2 py-2 text-gray-300 hover:bg-gray-700 transition-colors"
        >
          <Bug className="w-4 h-4" />
          <span className="text-sm font-medium">Debug Panel</span>
          <ChevronUp className="w-4 h-4" />
          {workflowTraces.length > 0 && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-blue-600 rounded-full">
              {workflowTraces.length}
            </span>
          )}
          {executionError && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-red-600 rounded-full">
              Error
            </span>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 h-80 bg-gray-900 border-t border-gray-700 flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-white">
            <Bug className="w-4 h-4" />
            <span className="font-medium">Debug Panel</span>
          </div>

          {/* Tabs */}
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded transition-colors ${
                  activeTab === tab.id
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                {tab.icon}
                {tab.label}
                {tab.id === 'errors' && executionError && (
                  <span className="w-2 h-2 bg-red-500 rounded-full" />
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onToggle}
            className="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700"
          >
            <ChevronDown className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'timeline' && (
          <div className="h-full">
            {workflowTraces.length > 0 ? (
              <RequestTimeline
                traces={workflowTraces}
                onSelectTrace={setSelectedTrace}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No requests yet</p>
                  <p className="text-sm">Execute a workflow to see request timeline</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'request' && (
          <div className="h-full">
            {selectedTrace ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-medium">
                    {selectedTrace.method} {selectedTrace.endpoint}
                  </h3>
                  <span className={`px-2 py-1 rounded text-xs ${
                    selectedTrace.status >= 200 && selectedTrace.status < 300
                      ? 'bg-green-900 text-green-200'
                      : 'bg-red-900 text-red-200'
                  }`}>
                    {selectedTrace.status} • {selectedTrace.duration}ms
                  </span>
                </div>

                <div className="bg-gray-800 rounded p-3">
                  <h4 className="text-gray-400 text-sm mb-2">Request Body</h4>
                  <pre className="text-sm text-gray-300 overflow-auto max-h-40">
                    {JSON.stringify(selectedTrace.request, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Bug className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No request selected</p>
                  <p className="text-sm">Select a request from the Timeline tab</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'response' && (
          <div className="h-full overflow-auto">
            {executionResult ? (
              <JSONViewer data={executionResult} />
            ) : selectedTrace?.response ? (
              <JSONViewer data={selectedTrace.response} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <FileJson className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No response data</p>
                  <p className="text-sm">Execute a workflow or select a request</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'errors' && (
          <div className="h-full">
            {executionError ? (
              <ErrorPanel
                error={{
                  status: 500,
                  code: 'EXECUTION_ERROR',
                  message: executionError,
                  details: typeof executionResult?.error === 'object' && executionResult.error !== null
                    ? (executionResult.error as Record<string, unknown>)
                    : undefined,
                }}
              />
            ) : selectedTrace?.error ? (
              <ErrorPanel error={selectedTrace.error} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p className="text-green-400">No errors</p>
                  <p className="text-sm">All executions completed successfully</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
