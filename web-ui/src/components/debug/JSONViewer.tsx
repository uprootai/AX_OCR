import { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { Button } from '../ui/Button';

interface JSONViewerProps {
  data: any;
  title?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
  maxHeight?: string;
}

export default function JSONViewer({
  data,
  title,
  collapsible = true,
  defaultExpanded = true,
  maxHeight = '500px',
}: JSONViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const jsonString = JSON.stringify(data, null, 2);
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-card border rounded-lg overflow-hidden">
      {title && (
        <div className="flex items-center justify-between px-4 py-3 border-b bg-accent/30">
          <h3 className="font-semibold text-sm">{title}</h3>
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            {copied ? (
              <>
                <Check className="h-4 w-4 mr-2" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 mr-2" />
                Copy
              </>
            )}
          </Button>
        </div>
      )}
      <div
        className="overflow-auto p-4 font-mono text-sm"
        style={{ maxHeight }}
      >
        <JSONNode
          value={data}
          name={null}
          collapsible={collapsible}
          defaultExpanded={defaultExpanded}
          depth={0}
        />
      </div>
    </div>
  );
}

interface JSONNodeProps {
  name: string | null;
  value: any;
  collapsible: boolean;
  defaultExpanded: boolean;
  depth: number;
}

function JSONNode({
  name,
  value,
  collapsible,
  defaultExpanded,
  depth,
}: JSONNodeProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded || depth < 2);

  const indent = depth * 20;

  if (value === null) {
    return (
      <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
        {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
        <span className="text-gray-500 dark:text-gray-400">null</span>
      </div>
    );
  }

  if (value === undefined) {
    return (
      <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
        {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
        <span className="text-gray-500 dark:text-gray-400">undefined</span>
      </div>
    );
  }

  if (typeof value === 'boolean') {
    return (
      <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
        {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
        <span className="text-blue-600 dark:text-blue-400">{String(value)}</span>
      </div>
    );
  }

  if (typeof value === 'number') {
    return (
      <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
        {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
        <span className="text-green-600 dark:text-green-400">{value}</span>
      </div>
    );
  }

  if (typeof value === 'string') {
    return (
      <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
        {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
        <span className="text-orange-600 dark:text-orange-400">"{value}"</span>
      </div>
    );
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return (
        <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
          {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
          <span className="text-gray-600 dark:text-gray-400">[]</span>
        </div>
      );
    }

    return (
      <div style={{ marginLeft: `${indent}px` }}>
        <div className="py-0.5 flex items-center gap-1">
          {collapsible && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="hover:bg-accent rounded p-0.5"
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </button>
          )}
          {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
          <span className="text-gray-600 dark:text-gray-400">
            [{value.length}]
          </span>
        </div>
        {isExpanded && (
          <div>
            {value.map((item, index) => (
              <JSONNode
                key={index}
                name={String(index)}
                value={item}
                collapsible={collapsible}
                defaultExpanded={defaultExpanded}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (typeof value === 'object') {
    const keys = Object.keys(value);
    if (keys.length === 0) {
      return (
        <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
          {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
          <span className="text-gray-600 dark:text-gray-400">{'{}'}</span>
        </div>
      );
    }

    return (
      <div style={{ marginLeft: `${indent}px` }}>
        <div className="py-0.5 flex items-center gap-1">
          {collapsible && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="hover:bg-accent rounded p-0.5"
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </button>
          )}
          {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
          <span className="text-gray-600 dark:text-gray-400">
            {'{'}{keys.length}{'}'}
          </span>
        </div>
        {isExpanded && (
          <div>
            {keys.map((key) => (
              <JSONNode
                key={key}
                name={key}
                value={value[key]}
                collapsible={collapsible}
                defaultExpanded={defaultExpanded}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
      {name && <span className="text-purple-600 dark:text-purple-400">{name}: </span>}
      <span>{String(value)}</span>
    </div>
  );
}
