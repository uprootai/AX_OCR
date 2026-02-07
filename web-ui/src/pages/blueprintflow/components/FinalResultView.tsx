/**
 * FinalResultView Component
 * 워크플로우 실행 완료 후 최종 결과 표시
 *
 * ExecutionStatusPanel.tsx에서 추출
 */

import { useState, useCallback, useMemo } from 'react';
import { Download, ExternalLink } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import Toast from '../../../components/ui/Toast';
import { nodeDefinitions } from '../../../config/nodeDefinitions';
import ResultSummaryCard from '../../../components/blueprintflow/ResultSummaryCard';
import PipelineConclusionCard from '../../../components/blueprintflow/PipelineConclusionCard';
import { OutputDisplay } from './OutputDisplays';
import type {
  APINodeStatus,
  PipelineOutput,
  ExecutionGroup,
} from '../types';
import type { Node } from 'reactflow';

// Toast 알림 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

// Group nodes by parallel execution
function groupNodesByExecution(nodeStatuses: APINodeStatus[]): ExecutionGroup[] {
  const groups: ExecutionGroup[] = [];
  const processed = new Set<string>();

  nodeStatuses.forEach((node) => {
    if (processed.has(node.node_id)) return;

    const parallelNodes = [node];
    processed.add(node.node_id);

    if (node.start_time && node.end_time) {
      const nodeStart = new Date(node.start_time).getTime();
      const nodeEnd = new Date(node.end_time).getTime();

      nodeStatuses.forEach((other) => {
        if (processed.has(other.node_id)) return;
        if (!other.start_time || !other.end_time) return;

        const otherStart = new Date(other.start_time).getTime();
        const otherEnd = new Date(other.end_time).getTime();
        const overlaps = nodeStart < otherEnd && nodeEnd > otherStart;

        if (overlaps) {
          parallelNodes.push(other);
          processed.add(other.node_id);
        }
      });
    }

    groups.push({
      type: parallelNodes.length > 1 ? 'parallel' : 'sequential',
      nodes: parallelNodes,
      startTime: node.start_time,
      endTime: node.end_time,
    });
  });

  return groups;
}

// Final execution result display
export function FinalResult({
  executionResult,
  nodes,
  uploadedImage,
  onDownloadJSON,
}: {
  executionResult: Record<string, unknown>;
  nodes: Node[];
  uploadedImage: string | null;
  onDownloadJSON: () => void;
}) {
  const nodeStatuses = (executionResult.node_statuses || []) as APINodeStatus[];
  const groups = groupNodesByExecution(nodeStatuses);
  const parallelGroups = groups.filter(g => g.type === 'parallel').length;
  const sequentialNodes = groups.filter(g => g.type === 'sequential').length;

  // BOM 세션 정보 추출 (blueprint-ai-bom 노드의 output에서)
  const bomSessionInfo = useMemo(() => {
    const finalOutput = executionResult.final_output as Record<string, Record<string, unknown>> | undefined;
    if (!finalOutput) return null;

    // final_output에서 BOM 노드 결과 찾기
    for (const [nodeId, output] of Object.entries(finalOutput)) {
      if (output?.session_id && output?.verification_url) {
        return {
          nodeId,
          sessionId: output.session_id as string,
          verificationUrl: output.verification_url as string,
          message: output.message as string | undefined,
          detectionCount: output.detection_count as number | undefined,
          dimensionCount: output.dimension_count as number | undefined,
        };
      }
    }

    // node_statuses에서도 찾기
    for (const ns of nodeStatuses) {
      const output = ns.output as Record<string, unknown> | undefined;
      if (output?.session_id && output?.verification_url) {
        return {
          nodeId: ns.node_id,
          sessionId: output.session_id as string,
          verificationUrl: output.verification_url as string,
          message: output.message as string | undefined,
          detectionCount: output.detection_count as number | undefined,
          dimensionCount: output.dimension_count as number | undefined,
        };
      }
    }

    return null;
  }, [executionResult, nodeStatuses]);

  return (
    <div className="space-y-3">
      {/* AI BOM 세션 열기 버튼 (BOM 노드 결과가 있는 경우) */}
      {bomSessionInfo && (
        <div className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">🎯</span>
                <span className="font-semibold text-blue-900 dark:text-blue-100">
                  AI BOM 세션 생성 완료
                </span>
              </div>
              <div className="text-sm text-blue-700 dark:text-blue-300">
                {bomSessionInfo.message || '검증 UI에서 결과를 확인하고 BOM을 생성하세요.'}
              </div>
              <div className="flex gap-3 mt-1 text-xs text-blue-600 dark:text-blue-400">
                {bomSessionInfo.detectionCount !== undefined && (
                  <span>검출: {bomSessionInfo.detectionCount}개</span>
                )}
                {bomSessionInfo.dimensionCount !== undefined && (
                  <span>치수: {bomSessionInfo.dimensionCount}개</span>
                )}
                <span>Session: {bomSessionInfo.sessionId.slice(0, 8)}...</span>
              </div>
            </div>
            <a
              href={bomSessionInfo.verificationUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
            >
              <ExternalLink className="w-4 h-4" />
              AI BOM 열기
            </a>
          </div>
        </div>
      )}

      {/* Status Header */}
      <div className="text-green-600 dark:text-green-400">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold">Status:</span>
            <span className="px-2 py-1 rounded bg-green-100 dark:bg-green-900 text-xs">
              {executionResult.status as string}
            </span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              ({(executionResult.execution_time_ms as number)?.toFixed(0) || 0}ms)
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onDownloadJSON}
            className="text-xs"
          >
            <Download className="w-3 h-3 mr-1" />
            JSON
          </Button>
        </div>

        {/* Node Status Summary */}
        {nodeStatuses.length > 0 && (
          <div className="text-sm space-y-1">
            {nodeStatuses.map((nodeStatus) => (
              <div key={nodeStatus.node_id} className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  nodeStatus.status === 'completed' ? 'bg-green-500' :
                  nodeStatus.status === 'failed' ? 'bg-red-500' :
                  nodeStatus.status === 'running' ? 'bg-yellow-500' :
                  'bg-gray-500'
                }`} />
                <span className="text-gray-700 dark:text-gray-300">
                  {nodeStatus.node_id}: {nodeStatus.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Result Summary Card */}
      {nodeStatuses.length > 0 && (
        <ResultSummaryCard
          results={nodeStatuses.map((nodeStatus) => {
            const workflowNode = nodes.find((n) => n.id === nodeStatus.node_id);
            return {
              nodeId: nodeStatus.node_id,
              nodeType: workflowNode?.type || 'unknown',
              status: nodeStatus.status === 'completed' ? 'success' :
                      nodeStatus.status === 'failed' ? 'error' :
                      nodeStatus.status === 'running' ? 'running' : 'pending',
              executionTime: nodeStatus.execution_time,
              output: (nodeStatus.output || (executionResult.final_output as Record<string, unknown>)?.[nodeStatus.node_id]) as Record<string, unknown> | undefined,
            };
          })}
          totalExecutionTime={executionResult.execution_time_ms as number | undefined}
        />
      )}

      {/* Pipeline Conclusion Card */}
      {nodeStatuses.length > 0 && (
        <PipelineConclusionCard
          executionResult={{
            status: executionResult.status as string,
            execution_time_ms: executionResult.execution_time_ms as number | undefined,
            node_statuses: nodeStatuses.map((ns) => ({
              node_id: ns.node_id,
              node_type: nodes.find(n => n.id === ns.node_id)?.type,
              status: ns.status,
              output: (ns.output || (executionResult.final_output as Record<string, unknown>)?.[ns.node_id]) as Record<string, unknown> | undefined,
            })),
            final_output: executionResult.final_output as Record<string, Record<string, unknown>> | undefined,
          }}
          nodes={nodes.map(n => ({
            id: n.id,
            type: n.type,
            data: { label: n.data?.label as string | undefined },
          }))}
        />
      )}

      {/* Progressive Pipeline Results */}
      {nodeStatuses.length > 0 && (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
          {/* Pipeline Results Header */}
          <div className="flex items-center gap-2 mb-3">
            <span className="font-semibold text-gray-900 dark:text-white">🔄 Pipeline Results</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              ({nodeStatuses.length} nodes
              {parallelGroups > 0 && (
                <span className="ml-1 text-cyan-600 dark:text-cyan-400 font-semibold">
                  • {parallelGroups} parallel group{parallelGroups > 1 ? 's' : ''}
                </span>
              )}
              {sequentialNodes > 0 && (
                <span className="ml-1">
                  • {sequentialNodes} sequential
                </span>
              )}
              )
            </span>
          </div>

          {/* Grouped execution display */}
          <div className="space-y-4">
            {(() => {
              let globalIndex = 0;
              return groups.map((group, groupIndex) => (
                <div key={groupIndex}>
                  {/* Parallel Group Indicator */}
                  {group.type === 'parallel' && (
                    <div className="mb-2 flex items-center gap-2 px-3 py-1.5 bg-cyan-50 dark:bg-cyan-900/30 border-l-4 border-cyan-500 rounded">
                      <span className="text-xs font-semibold text-cyan-700 dark:text-cyan-300">
                        ⚡ Parallel Execution ({group.nodes.length} nodes running simultaneously)
                      </span>
                    </div>
                  )}

                  {/* Nodes in this group */}
                  <div className={group.type === 'parallel' ? 'ml-4 space-y-3' : 'space-y-3'}>
                    {group.nodes.map((nodeStatus) => {
                      const currentIndex = globalIndex++;
                      return (
                        <NodeResultCard
                          key={nodeStatus.node_id}
                          nodeStatus={nodeStatus}
                          stepNumber={currentIndex + 1}
                          isParallel={group.type === 'parallel'}
                          nodes={nodes}
                          uploadedImage={uploadedImage}
                          executionResult={executionResult}
                        />
                      );
                    })}
                  </div>

                  {/* Group separator arrow */}
                  {groupIndex < groups.length - 1 && (
                    <div className="flex justify-center py-2 my-2">
                      <div className="w-0.5 h-6 bg-gradient-to-b from-cyan-400 to-cyan-600"></div>
                      <div className="absolute mt-5 text-cyan-600">▼</div>
                    </div>
                  )}
                </div>
              ));
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

// Individual node result card
function NodeResultCard({
  nodeStatus,
  stepNumber,
  isParallel,
  nodes,
  uploadedImage,
  executionResult,
}: {
  nodeStatus: APINodeStatus;
  stepNumber: number;
  isParallel: boolean;
  nodes: Node[];
  uploadedImage: string | null;
  executionResult: Record<string, unknown>;
}) {
  const workflowNode = nodes.find((n) => n.id === nodeStatus.node_id);
  const nodeLabel = workflowNode?.data?.label || nodeStatus.node_id;
  const nodeType = workflowNode?.type || 'unknown';
  const output = (nodeStatus.output || (executionResult.final_output as Record<string, unknown>)?.[nodeStatus.node_id]) as PipelineOutput | undefined;

  return (
    <div className="relative">
      <div className="flex items-start gap-3">
        {/* Step Number */}
        <div className={`flex-shrink-0 w-8 h-8 text-white rounded-full flex items-center justify-center font-bold text-sm ${
          isParallel ? 'bg-cyan-500' : 'bg-cyan-600'
        }`}>
          {stepNumber}
        </div>

        {/* Node Info & Results */}
        <div className="flex-1 bg-gray-50 dark:bg-gray-700 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
          {/* Node Header */}
          <NodeResultHeader
            nodeLabel={nodeLabel as string}
            nodeType={nodeType}
            nodeId={nodeStatus.node_id}
            status={nodeStatus.status}
          />

          {/* Parameters Used */}
          {workflowNode?.data?.parameters && Object.keys(workflowNode.data.parameters as object).length > 0 && (
            <ParametersDisplay parameters={workflowNode.data.parameters as Record<string, unknown>} />
          )}

          {/* Output Content */}
          {output && (
            <OutputDisplay
              output={output}
              nodeType={nodeType}
              nodeId={nodeStatus.node_id}
              uploadedImage={uploadedImage}
            />
          )}

          {/* Interactive Action UI */}
          {output?.ui_action && (
            <UIActionDisplay
              uiAction={output.ui_action}
              sessionId={output.session_id}
              message={output.message}
            />
          )}

          {/* Error Display */}
          {nodeStatus.error && (
            <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
              <div className="text-xs font-semibold text-red-900 dark:text-red-100">
                ❌ Error:
              </div>
              <div className="text-xs text-red-700 dark:text-red-300 mt-1">
                {nodeStatus.error}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Node result header
function NodeResultHeader({
  nodeLabel,
  nodeType,
  nodeId,
  status,
}: {
  nodeLabel: string;
  nodeType: string;
  nodeId: string;
  status: string;
}) {
  return (
    <div className="flex items-center justify-between mb-2">
      <div>
        <div className="font-medium text-sm text-gray-900 dark:text-white">
          {nodeLabel}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {nodeType} • {nodeId}
        </div>
        {nodeDefinitions[nodeType as keyof typeof nodeDefinitions]?.description && (
          <div className="text-xs text-blue-600 dark:text-blue-400 mt-1 italic">
            💡 {nodeDefinitions[nodeType as keyof typeof nodeDefinitions].description}
          </div>
        )}
      </div>
      <div className={`px-2 py-1 rounded text-xs font-semibold ${
        status === 'completed'
          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
          : status === 'failed'
          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          : 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-200'
      }`}>
        {status}
      </div>
    </div>
  );
}

// Parameters display
function ParametersDisplay({ parameters }: { parameters: Record<string, unknown> }) {
  return (
    <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">
      <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
        ⚙️ Parameters:
      </div>
      <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
        {Object.entries(parameters).map(([key, value]) => (
          <div key={key} className="flex gap-1">
            <span className="font-mono text-blue-600 dark:text-blue-400">{key}:</span>
            <span className="font-mono">{String(value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Interactive Action UI display
function UIActionDisplay({
  uiAction,
  sessionId,
  message,
}: {
  uiAction: { url?: string; label?: string };
  sessionId?: string;
  message?: string;
}) {
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  const showToast = useCallback((toastMessage: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message: toastMessage, type });
  }, []);

  const handleDeleteSession = async () => {
    try {
      await fetch(`http://localhost:5020/sessions/${sessionId}`, { method: 'DELETE' });
      showToast('✓ 세션이 삭제되었습니다', 'success');
    } catch {
      showToast('✗ 세션 삭제 실패', 'error');
    }
  };

  return (
    <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
            🔗 {message || '액션이 필요합니다'}
          </div>
          <a
            href={uiAction.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
          >
            <span>🚀</span>
            {uiAction.label || '열기'}
            <span className="text-blue-200">↗</span>
          </a>
        </div>
        {sessionId && (
          <button
            onClick={handleDeleteSession}
            className="ml-3 px-2 py-1 text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
            title="세션 삭제"
          >
            🗑️ 세션 닫기
          </button>
        )}
      </div>
      {sessionId && (
        <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
          Session: {sessionId}
        </div>
      )}

      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.type === 'error' ? 15000 : 10000}
          onClose={() => setToast(prev => ({ ...prev, show: false }))}
        />
      )}
    </div>
  );
}
