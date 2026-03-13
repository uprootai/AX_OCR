/**
 * FinalResultView — ParametersDisplay sub-component
 */

interface ParametersDisplayProps {
  parameters: Record<string, unknown>;
}

export function ParametersDisplay({ parameters }: ParametersDisplayProps) {
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
