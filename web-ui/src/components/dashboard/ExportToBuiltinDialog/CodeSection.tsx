import { Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';
import type { ReactNode } from 'react';

interface CodeSectionProps {
  sectionKey: string;
  title: string;
  filePath: string;
  icon: ReactNode;
  content: string;
  isExpanded: boolean;
  isCopied: boolean;
  onToggle: (key: string) => void;
  onCopy: (text: string, key: string) => void;
}

export function CodeSection({
  sectionKey,
  title,
  filePath,
  icon,
  content,
  isExpanded,
  isCopied,
  onToggle,
  onCopy,
}: CodeSectionProps) {
  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => onToggle(sectionKey)}
        className="w-full flex items-center justify-between p-4 bg-muted/50 hover:bg-muted transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-semibold">{title}</span>
          <code className="text-xs bg-muted px-2 py-0.5 rounded">{filePath}</code>
        </div>
        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
      </button>
      {isExpanded && (
        <div className="p-4 bg-gray-900 relative">
          <button
            onClick={() => onCopy(content, sectionKey)}
            className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            {isCopied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4 text-gray-300" />
            )}
          </button>
          <pre className="text-sm text-gray-100 overflow-x-auto font-mono whitespace-pre">{content}</pre>
        </div>
      )}
    </div>
  );
}
