import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidProps {
  chart: string;
  className?: string;
}

export default function Mermaid({ chart, className = '' }: MermaidProps) {
  const elementRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!elementRef.current) return;

      try {
        // Initialize mermaid with better visibility
        mermaid.initialize({
          startOnLoad: false,
          theme: 'base',
          themeVariables: {
            primaryColor: '#e3f2fd',
            primaryTextColor: '#000000',
            primaryBorderColor: '#1976d2',
            lineColor: '#333333',
            secondaryColor: '#f3e5f5',
            tertiaryColor: '#fff3e0',
            textColor: '#000000',
            mainBkg: '#ffffff',
            secondBkg: '#f5f5f5',
            noteBkgColor: '#fff9c4',
            noteTextColor: '#000000',
            activationBorderColor: '#666',
            activationBkgColor: '#f4f4f4',
            sequenceNumberColor: '#ffffff',
          },
          securityLevel: 'loose',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis',
          },
          sequence: {
            useMaxWidth: true,
            showSequenceNumbers: false,
            actorFontSize: 14,
            actorFontWeight: 600,
            noteFontSize: 12,
            messageFontSize: 13,
            messageFontWeight: 500,
          },
        });

        // Generate unique ID
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

        // Clear previous content
        elementRef.current.innerHTML = '';

        // Render the diagram
        const { svg } = await mermaid.render(id, chart);

        if (elementRef.current) {
          elementRef.current.innerHTML = svg;
          setError(null);
        }
      } catch (err) {
        console.error('Mermaid rendering error:', err);
        const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류';
        const errorStack = err instanceof Error ? err.stack : undefined;
        console.error('Error message:', errorMessage);
        console.error('Error stack:', errorStack);
        console.error('Chart content:', chart);
        setError(errorMessage);
      }
    };

    renderDiagram();
  }, [chart]);

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
        <p className="text-sm text-red-800 dark:text-red-200 font-semibold mb-2">
          ❌ 다이어그램 렌더링 실패
        </p>
        <p className="text-xs text-red-700 dark:text-red-300 mb-2">
          오류: {error}
        </p>
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
          <a
            href="https://mermaid.live"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            mermaid.live
          </a>
          에서 문법 확인하세요.
        </p>
        <pre className="text-xs mt-2 overflow-x-auto bg-gray-100 dark:bg-gray-900 p-2 rounded">
          {chart}
        </pre>
      </div>
    );
  }

  return (
    <div
      ref={elementRef}
      className={`mermaid-container ${className}`}
    />
  );
}
