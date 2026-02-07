/**
 * ExecutionStatusPanel Component
 * 워크플로우 실행 상태 및 결과 표시
 */

import { useState } from 'react';
import { RotateCcw } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import type { NodeStatus } from '../../../store/workflowStore';
import { FinalResult } from './FinalResultView';
import type { Node } from 'reactflow';

interface ExecutionStatusPanelProps {
  isExecuting: boolean;
  executionResult: Record<string, unknown> | null;
  executionError: string | null;
  nodeStatuses: Record<string, NodeStatus>;
  executionId: string | null;
  nodes: Node[];
  uploadedImage: string | null;
  onRerun: () => void;
  onDownloadJSON: () => void;
}

export function ExecutionStatusPanel({
  isExecuting,
  executionResult,
  executionError,
  nodeStatuses,
  executionId,
  nodes,
  uploadedImage,
  onRerun,
  onDownloadJSON,
}: ExecutionStatusPanelProps) {
  const [isStatusCollapsed, setIsStatusCollapsed] = useState(false);

  const hasStatus = isExecuting || executionResult || executionError || Object.keys(nodeStatuses).length > 0;
  if (!hasStatus) return null;

  return (
    <div className="mt-3 rounded-md bg-gray-100 dark:bg-gray-700">
      {/* Collapse/Expand Header */}
      <div className="flex items-center justify-between p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-t-md">
        <div
          className="flex items-center gap-2 cursor-pointer flex-1"
          onClick={() => setIsStatusCollapsed(!isStatusCollapsed)}
        >
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
            {isStatusCollapsed ? '▶' : '▼'} Execution Status
            {executionResult?.status != null && (
              <span className={`px-2 py-0.5 rounded text-xs ${
                executionResult.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                executionResult.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
              }`}>
                {String(executionResult.status)}
              </span>
            )}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {!isExecuting && executionResult && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRerun();
              }}
              className="text-xs px-2 py-1 h-6"
              title="Re-run workflow"
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Re-run
            </Button>
          )}
          <span
            className="text-xs text-gray-500 cursor-pointer"
            onClick={() => setIsStatusCollapsed(!isStatusCollapsed)}
          >
            {isStatusCollapsed ? 'Expand' : 'Collapse'}
          </span>
        </div>
      </div>

      {/* Collapsible Content */}
      {!isStatusCollapsed && (
        <div className="p-3 pt-0">
          {executionError && (
            <div className="text-red-600 dark:text-red-400 flex items-center gap-2">
              <span className="font-semibold">Error:</span>
              <span>{executionError}</span>
            </div>
          )}

          {/* Real-time Node Status (SSE) */}
          {isExecuting && Object.keys(nodeStatuses).length > 0 && (
            <RealTimeStatus nodeStatuses={nodeStatuses} executionId={executionId} />
          )}

          {/* Final Result */}
          {executionResult && !isExecuting && (
            <FinalResult
              executionResult={executionResult}
              nodes={nodes}
              uploadedImage={uploadedImage}
              onDownloadJSON={onDownloadJSON}
            />
          )}
        </div>
      )}
    </div>
  );
}

// Real-time status during execution
function RealTimeStatus({
  nodeStatuses,
  executionId,
}: {
  nodeStatuses: Record<string, NodeStatus>;
  executionId: string | null;
}) {
  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold text-blue-600 dark:text-blue-400">
          ⚡ Executing Workflow
        </span>
        {executionId && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            (ID: {executionId.slice(0, 8)})
          </span>
        )}
      </div>
      <div className="text-sm space-y-1">
        {Object.values(nodeStatuses).map((nodeStatus) => (
          <div key={nodeStatus.nodeId} className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              nodeStatus.status === 'completed' ? 'bg-green-500' :
              nodeStatus.status === 'failed' ? 'bg-red-500' :
              nodeStatus.status === 'running' ? 'bg-yellow-500 animate-pulse' :
              'bg-gray-400'
            }`} />
            <span className="text-gray-700 dark:text-gray-300 flex-1">
              {nodeStatus.nodeId}
            </span>
            <span className={`px-2 py-0.5 rounded text-xs ${
              nodeStatus.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
              nodeStatus.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
              nodeStatus.status === 'running' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
              'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
            }`}>
              {nodeStatus.status}
            </span>
            {nodeStatus.status === 'running' && nodeStatus.elapsedSeconds !== undefined ? (
              <span className="text-xs text-yellow-600 dark:text-yellow-400 font-mono">
                {nodeStatus.elapsedSeconds}초 경과
              </span>
            ) : nodeStatus.progress !== undefined && nodeStatus.progress > 0 ? (
              <span className="text-xs text-gray-500">
                {(nodeStatus.progress * 100).toFixed(0)}%
              </span>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
