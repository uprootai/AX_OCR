/**
 * FinalResultView — NodeResultHeader sub-component
 */

import { nodeDefinitions } from '../../../../config/nodeDefinitions';

interface NodeResultHeaderProps {
  nodeLabel: string;
  nodeType: string;
  nodeId: string;
  status: string;
}

export function NodeResultHeader({
  nodeLabel,
  nodeType,
  nodeId,
  status,
}: NodeResultHeaderProps) {
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
