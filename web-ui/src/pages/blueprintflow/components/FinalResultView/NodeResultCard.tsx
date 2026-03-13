/**
 * FinalResultView — NodeResultCard sub-component
 * Individual node result display card
 */

import type { Node } from 'reactflow';
import { OutputDisplay } from '../OutputDisplays';
import type { APINodeStatus, PipelineOutput } from '../../types';
import { NodeResultHeader } from './NodeResultHeader';
import { ParametersDisplay } from './ParametersDisplay';
import { UIActionDisplay } from './UIActionDisplay';

interface NodeResultCardProps {
  nodeStatus: APINodeStatus;
  stepNumber: number;
  isParallel: boolean;
  nodes: Node[];
  uploadedImage: string | null;
  executionResult: Record<string, unknown>;
}

export function NodeResultCard({
  nodeStatus,
  stepNumber,
  isParallel,
  nodes,
  uploadedImage,
  executionResult,
}: NodeResultCardProps) {
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
