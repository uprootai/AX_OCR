/**
 * FinalResultView — FinalResult main component
 * Final execution result display after workflow completion
 */

import { useMemo } from 'react';
import { Download, ExternalLink } from 'lucide-react';
import { Button } from '../../../../components/ui/Button';
import ResultSummaryCard from '../../../../components/blueprintflow/ResultSummaryCard';
import PipelineConclusionCard from '../../../../components/blueprintflow/PipelineConclusionCard';
import type { Node } from 'reactflow';
import type { APINodeStatus } from '../../types';
import { groupNodesByExecution } from './utils';
import { NodeResultCard } from './NodeResultCard';

interface FinalResultProps {
  executionResult: Record<string, unknown>;
  nodes: Node[];
  uploadedImage: string | null;
  onDownloadJSON: () => void;
}

export function FinalResult({
  executionResult,
  nodes,
  uploadedImage,
  onDownloadJSON,
}: FinalResultProps) {
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
              href={bomSessionInfo.verificationUrl.replace(/^https?:\/\/localhost:\d+/, '/bom')}
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
