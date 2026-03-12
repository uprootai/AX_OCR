/**
 * Execution mode toggle button group (Sequential / Parallel / Eager)
 */

interface ExecutionModeToggleProps {
  executionMode: 'sequential' | 'parallel' | 'eager';
  setExecutionMode: (mode: 'sequential' | 'parallel' | 'eager') => void;
}

export function ExecutionModeToggle({
  executionMode,
  setExecutionMode,
}: ExecutionModeToggleProps) {
  return (
    <div className="flex items-center gap-1 border rounded-md overflow-hidden">
      <button
        onClick={() => setExecutionMode('sequential')}
        className={`px-2 py-1.5 text-xs flex items-center gap-1 transition-colors ${
          executionMode === 'sequential'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
        }`}
        title="Sequential execution (one node at a time)"
      >
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="4" y1="12" x2="20" y2="12" />
          <circle cx="6" cy="12" r="2" fill="currentColor" />
          <circle cx="12" cy="12" r="2" fill="currentColor" />
          <circle cx="18" cy="12" r="2" fill="currentColor" />
        </svg>
        Sequential
      </button>
      <button
        onClick={() => setExecutionMode('parallel')}
        className={`px-2 py-1.5 text-xs flex items-center gap-1 transition-colors ${
          executionMode === 'parallel'
            ? 'bg-purple-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
        }`}
        title="Parallel execution (concurrent nodes by level)"
      >
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="4" y1="6" x2="20" y2="6" />
          <line x1="4" y1="12" x2="20" y2="12" />
          <line x1="4" y1="18" x2="20" y2="18" />
          <circle cx="12" cy="6" r="2" fill="currentColor" />
          <circle cx="12" cy="12" r="2" fill="currentColor" />
          <circle cx="12" cy="18" r="2" fill="currentColor" />
        </svg>
        Parallel
      </button>
      <button
        onClick={() => setExecutionMode('eager')}
        className={`px-2 py-1.5 text-xs flex items-center gap-1 transition-colors ${
          executionMode === 'eager'
            ? 'bg-green-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
        }`}
        title="Eager execution (start each node as soon as its dependencies complete)"
      >
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
        </svg>
        Eager
      </button>
    </div>
  );
}
