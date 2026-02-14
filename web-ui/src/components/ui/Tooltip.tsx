import { useState } from 'react';
import type { ReactNode } from 'react';

interface TooltipProps {
  content: string;
  children: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  /** 인라인 텍스트용 점선 밑줄 + cursor-help 스타일 (기본: false) */
  underline?: boolean;
  /** 래퍼 요소의 추가 className */
  className?: string;
}

export function Tooltip({
  content,
  children,
  position = 'top',
  underline = false,
  className = '',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent',
  };

  return (
    <span
      className={`relative inline-flex ${underline ? 'cursor-help' : ''} ${className}`}
      style={underline ? { borderBottom: '1px dotted #9ca3af' } : undefined}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <span
          className={`absolute z-50 px-3 py-2 text-xs leading-relaxed text-white bg-gray-900 dark:bg-gray-700 rounded-lg shadow-lg w-max max-w-xs pointer-events-none ${positionClasses[position]}`}
          role="tooltip"
        >
          {content}
          <span
            className={`absolute w-0 h-0 border-4 border-gray-900 dark:border-gray-700 ${arrowClasses[position]}`}
          />
        </span>
      )}
    </span>
  );
}
