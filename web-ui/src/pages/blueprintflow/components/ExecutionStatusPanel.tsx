/**
 * ExecutionStatusPanel Component
 * 워크플로우 실행 상태 및 결과 표시
 */

import { useState, useCallback } from 'react';
import { Download, RotateCcw } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import Toast from '../../../components/ui/Toast';

// Toast 알림 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}
import { nodeDefinitions } from '../../../config/nodeDefinitions';
import type { NodeStatus } from '../../../store/workflowStore';
import OCRVisualization from '../../../components/debug/OCRVisualization';
import ToleranceVisualization from '../../../components/debug/ToleranceVisualization';
import SegmentationVisualization from '../../../components/debug/SegmentationVisualization';
import ResultSummaryCard from '../../../components/blueprintflow/ResultSummaryCard';
import PipelineConclusionCard from '../../../components/blueprintflow/PipelineConclusionCard';
import DataTableView from '../../../components/blueprintflow/DataTableView';
import VisualizationImage from '../../../components/blueprintflow/VisualizationImage';
import { extractArrayData, extractVisualizationImages } from '../../../components/blueprintflow/outputExtractors';
import type {
  APINodeStatus,
  PipelineOutput,
  Detection,
  DimensionResult,
  TextResult,
  OCRBlock,
  SegmentResult,
  ToleranceItem,
  ExecutionGroup,
} from '../types';
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

// Final execution result display
function FinalResult({
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

  return (
    <div className="space-y-3">
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

// Output display
function OutputDisplay({
  output,
  nodeType,
  nodeId,
  uploadedImage,
}: {
  output: PipelineOutput;
  nodeType: string;
  nodeId: string;
  uploadedImage: string | null;
}) {
  return (
    <>
      {/* Output Image - visualized_image 우선 (바운딩박스 포함) */}
      {(output.visualized_image || output.image) && (
        <OutputImageDisplay
          imageData={output.visualized_image || output.image || ''}
          nodeLabel={nodeType}
        />
      )}

      {/* Detections (YOLO) */}
      {output.detections && Array.isArray(output.detections) && (
        <DetectionsDisplay detections={output.detections} />
      )}

      {/* eDOCr2 Dimensions */}
      {output.dimensions && Array.isArray(output.dimensions) && (
        <DimensionsDisplay dimensions={output.dimensions} gdtCount={output.gdt?.length} />
      )}

      {/* OCR Visualization */}
      {(nodeType === 'edocr2' || nodeType.includes('ocr')) &&
       (output.dimensions || output.gdt) &&
       uploadedImage && (
        <div className="mt-3">
          <OCRVisualization
            imageBase64={uploadedImage}
            ocrResult={{
              dimensions: (output.dimensions || []) as { type: string; value: number; unit: string; tolerance: string | number | null }[],
              gdt: (output.gdt || []) as { type: string; value: number; datum: string | null }[],
              text: (typeof output.text === 'object' ? output.text : { total_blocks: 0 }) as { total_blocks?: number },
            }}
            compact={true}
          />
        </div>
      )}

      {/* Text Results */}
      {output.text && typeof output.text === 'string' && (
        <TextDisplay text={output.text} />
      )}

      {/* PaddleOCR Text Results */}
      {output.text_results && Array.isArray(output.text_results) && (
        <TextResultsDisplay textResults={output.text_results} />
      )}

      {/* OCR Blocks */}
      {output.blocks && Array.isArray(output.blocks) && (
        <BlocksDisplay blocks={output.blocks} />
      )}

      {/* Segmentation Results */}
      {output.segments && Array.isArray(output.segments) && (
        <SegmentsDisplay segments={output.segments} />
      )}
      {output.mask && (
        <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
          <div className="text-xs font-semibold text-green-900 dark:text-green-100">
            🎨 Segmentation Mask Available
          </div>
        </div>
      )}

      {/* Segmentation Visualization */}
      {nodeType === 'edgnet' && (output.num_components !== undefined || output.classifications) && (
        <div className="mt-3">
          <SegmentationVisualization
            imageBase64={uploadedImage || undefined}
            segmentationResult={{
              num_components: output.num_components || 0,
              classifications: output.classifications || { contour: 0, text: 0, dimension: 0 },
              graph: output.graph || { nodes: 0, edges: 0, avg_degree: 0 },
              vectorization: output.vectorization || { num_bezier_curves: 0, total_length: 0 },
            }}
            compact={true}
          />
        </div>
      )}

      {/* Tolerance Results */}
      {output.tolerances && Array.isArray(output.tolerances) && (
        <TolerancesDisplay tolerances={output.tolerances} />
      )}
      {output.analysis && typeof output.analysis === 'object' && (
        <AnalysisDisplay analysis={output.analysis} />
      )}

      {/* Tolerance Visualization */}
      {nodeType === 'skinmodel' && (output.manufacturability || output.predicted_tolerances) && (
        <div className="mt-3">
          <ToleranceVisualization
            toleranceData={{
              manufacturability: output.manufacturability,
              predicted_tolerances: output.predicted_tolerances,
              analysis: output.analysis,
            }}
            compact={true}
          />
        </div>
      )}

      {/* VL Results */}
      {output.result && typeof output.result === 'string' && (
        <VLResultDisplay result={output.result} />
      )}
      {output.description && typeof output.description === 'string' && (
        <VLDescriptionDisplay description={output.description} />
      )}

      {/* Data Table Views */}
      {(() => {
        const arrayData = extractArrayData(output as Record<string, unknown>);
        if (arrayData.length === 0) return null;
        return (
          <div className="mt-3 space-y-3">
            {arrayData.map(({ field, data, title }) => (
              <DataTableView
                key={field}
                data={data}
                title={title}
                nodeType={nodeType}
                exportFilename={`${nodeId}_${field}`}
                compact={true}
                pageSize={5}
              />
            ))}
          </div>
        );
      })()}

      {/* Visualization Images */}
      {(() => {
        const visualizations = extractVisualizationImages(output as Record<string, unknown>);
        const filteredVis = visualizations.filter(
          v => v.field !== 'image' && v.field !== 'visualized_image'
        );
        if (filteredVis.length === 0) return null;
        return (
          <div className="mt-3 space-y-2">
            {filteredVis.map(({ field, base64, title }) => (
              <VisualizationImage
                key={field}
                base64={base64}
                title={title}
                maxHeight="200px"
              />
            ))}
          </div>
        );
      })()}

      {/* Interactive Action UI */}
      {output.ui_action && (
        <UIActionDisplay
          uiAction={output.ui_action}
          sessionId={output.session_id}
          message={output.message}
        />
      )}

      {/* Raw Data Viewer */}
      {Object.keys(output).length > 0 && (
        <details className="mt-2">
          <summary className="text-xs font-medium text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-200">
            🔍 View Raw Data ({Object.keys(output).length} fields)
          </summary>
          <pre className="mt-2 p-2 bg-white dark:bg-gray-900 rounded text-xs overflow-auto max-h-60 border border-gray-200 dark:border-gray-700">
            {JSON.stringify(output, null, 2)}
          </pre>
        </details>
      )}
    </>
  );
}

// Helper components for output display
function OutputImageDisplay({ imageData, nodeLabel }: { imageData: string; nodeLabel: string }) {
  const src = imageData.startsWith('data:') ? imageData : `data:image/jpeg;base64,${imageData}`;
  return (
    <div className="mt-3">
      <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
        📸 Output Image:
      </div>
      <img
        src={src}
        alt={`${nodeLabel} result`}
        className="w-full h-auto rounded border border-gray-300 dark:border-gray-600 shadow-sm cursor-pointer hover:shadow-lg transition-shadow"
        onClick={(e) => {
          const img = e.currentTarget;
          const win = window.open('', '_blank');
          if (win) {
            win.document.write(`<img src="${img.src}" style="max-width:100%; height:auto;" />`);
          }
        }}
        title="클릭하여 크게 보기"
      />
    </div>
  );
}

function DetectionsDisplay({ detections }: { detections: Detection[] }) {
  return (
    <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
      <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">
        🎯 Detections: {detections.length} objects
      </div>
      <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
        {detections.slice(0, 3).map((det, i) => (
          <div key={i}>
            • {det.class_name || det.class || 'Unknown'} ({(det.confidence * 100).toFixed(1)}%)
          </div>
        ))}
        {detections.length > 3 && (
          <div className="text-blue-500 dark:text-blue-400">
            ... and {detections.length - 3} more
          </div>
        )}
      </div>
    </div>
  );
}

function DimensionsDisplay({ dimensions, gdtCount }: { dimensions: DimensionResult[]; gdtCount?: number }) {
  return (
    <div className="mt-2 p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded border border-indigo-200 dark:border-indigo-800">
      <div className="text-xs font-semibold text-indigo-900 dark:text-indigo-100">
        📏 Dimensions: {dimensions.length}
        {(gdtCount ?? 0) > 0 && ` | GD&T: ${gdtCount}`}
      </div>
      <div className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
        {dimensions.slice(0, 5).map((dim, i) => (
          <div key={i}>
            • {dim.type && `[${dim.type}] `}{dim.value || dim.text || JSON.stringify(dim).slice(0, 50)}{dim.unit || ''}{dim.tolerance ? ` ±${dim.tolerance}` : ''}
          </div>
        ))}
        {dimensions.length > 5 && (
          <div className="text-indigo-500 dark:text-indigo-400">
            ... and {dimensions.length - 5} more
          </div>
        )}
      </div>
    </div>
  );
}

function TextDisplay({ text }: { text: string }) {
  return (
    <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
      <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
        📝 Extracted Text:
      </div>
      <div className="text-xs text-purple-700 dark:text-purple-300 mt-1 whitespace-pre-wrap">
        {text.slice(0, 200)}
        {text.length > 200 && '...'}
      </div>
    </div>
  );
}

function TextResultsDisplay({ textResults }: { textResults: TextResult[] }) {
  return (
    <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
      <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
        📝 OCR Text Results: {textResults.length}
      </div>
      <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
        {textResults.slice(0, 5).map((textResult, i) => (
          <div key={i}>
            • {textResult.text || textResult.content || JSON.stringify(textResult).slice(0, 50)}
          </div>
        ))}
        {textResults.length > 5 && (
          <div className="text-purple-500 dark:text-purple-400">
            ... and {textResults.length - 5} more
          </div>
        )}
      </div>
    </div>
  );
}

function BlocksDisplay({ blocks }: { blocks: OCRBlock[] }) {
  return (
    <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
      <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
        📝 OCR Blocks: {blocks.length}
      </div>
      <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
        {blocks.slice(0, 3).map((block, i) => (
          <div key={i}>• {block.text || JSON.stringify(block).slice(0, 50)}</div>
        ))}
        {blocks.length > 3 && (
          <div className="text-purple-500 dark:text-purple-400">
            ... and {blocks.length - 3} more
          </div>
        )}
      </div>
    </div>
  );
}

function SegmentsDisplay({ segments }: { segments: SegmentResult[] }) {
  return (
    <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
      <div className="text-xs font-semibold text-green-900 dark:text-green-100">
        🎨 Segmentation: {segments.length} segments
      </div>
      <div className="text-xs text-green-700 dark:text-green-300 mt-1">
        {segments.slice(0, 3).map((seg, i) => (
          <div key={i}>
            • {seg.class || seg.type || `Segment ${i + 1}`}
            {seg.confidence && ` (${(seg.confidence * 100).toFixed(1)}%)`}
          </div>
        ))}
        {segments.length > 3 && (
          <div className="text-green-500 dark:text-green-400">
            ... and {segments.length - 3} more
          </div>
        )}
      </div>
    </div>
  );
}

function TolerancesDisplay({ tolerances }: { tolerances: ToleranceItem[] }) {
  return (
    <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
      <div className="text-xs font-semibold text-orange-900 dark:text-orange-100">
        📐 Tolerance Analysis: {tolerances.length} items
      </div>
      <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
        {tolerances.slice(0, 5).map((tol, i) => (
          <div key={i}>
            • {tol.dimension || tol.name || `Tolerance ${i + 1}`}
            {tol.value && `: ${tol.value}`}
          </div>
        ))}
        {tolerances.length > 5 && (
          <div className="text-orange-500 dark:text-orange-400">
            ... and {tolerances.length - 5} more
          </div>
        )}
      </div>
    </div>
  );
}

function AnalysisDisplay({ analysis }: { analysis: Record<string, unknown> }) {
  return (
    <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
      <div className="text-xs font-semibold text-orange-900 dark:text-orange-100">
        📐 Analysis Details:
      </div>
      <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
        {Object.entries(analysis).slice(0, 5).map(([key, value]) => (
          <div key={key}>• {key}: {String(value).slice(0, 50)}</div>
        ))}
      </div>
    </div>
  );
}

function VLResultDisplay({ result }: { result: string }) {
  return (
    <div className="mt-2 p-2 bg-pink-50 dark:bg-pink-900/20 rounded border border-pink-200 dark:border-pink-800">
      <div className="text-xs font-semibold text-pink-900 dark:text-pink-100">
        🤖 VL Result:
      </div>
      <div className="text-xs text-pink-700 dark:text-pink-300 mt-1 whitespace-pre-wrap">
        {result.slice(0, 300)}
        {result.length > 300 && '...'}
      </div>
    </div>
  );
}

function VLDescriptionDisplay({ description }: { description: string }) {
  return (
    <div className="mt-2 p-2 bg-pink-50 dark:bg-pink-900/20 rounded border border-pink-200 dark:border-pink-800">
      <div className="text-xs font-semibold text-pink-900 dark:text-pink-100">
        🤖 AI Description:
      </div>
      <div className="text-xs text-pink-700 dark:text-pink-300 mt-1 whitespace-pre-wrap">
        {description.slice(0, 300)}
        {description.length > 300 && '...'}
      </div>
    </div>
  );
}

function UIActionDisplay({
  uiAction,
  sessionId,
  message,
}: {
  uiAction: { url?: string; label?: string };
  sessionId?: string;
  message?: string;
}) {
  // Toast 알림 상태
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  // Toast 표시 헬퍼 함수
  const showToast = useCallback((toastMessage: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message: toastMessage, type });
  }, []);

  // 세션 삭제 핸들러
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

      {/* Toast 알림 */}
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
