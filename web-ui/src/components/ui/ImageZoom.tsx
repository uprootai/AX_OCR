import { useState } from 'react';
import { X, ZoomIn } from 'lucide-react';

interface ImageZoomProps {
  children: React.ReactNode;
}

export default function ImageZoom({ children }: ImageZoomProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Thumbnail with click handler */}
      <div
        className="relative group cursor-pointer inline-block w-full"
        onClick={() => setIsOpen(true)}
      >
        <div style={{ pointerEvents: 'none' }}>
          {children}
        </div>
        {/* Hover overlay */}
        <div className="absolute inset-0 bg-transparent group-hover:bg-black/20 transition-all duration-300 flex items-center justify-center" style={{ pointerEvents: 'none' }}>
          <div className="opacity-0 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300 bg-white dark:bg-gray-800 rounded-full p-4 shadow-2xl border-2 border-blue-500">
            <ZoomIn className="w-12 h-12 text-blue-600 dark:text-blue-400" strokeWidth={2.5} />
          </div>
        </div>
      </div>

      {/* Full-screen modal */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4 backdrop-blur-sm"
          onClick={() => setIsOpen(false)}
        >
          {/* Close button */}
          <button
            className="absolute top-4 right-4 p-3 bg-white/20 hover:bg-white/30 rounded-full transition-all shadow-lg z-10"
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(false);
            }}
          >
            <X className="w-8 h-8 text-white" />
          </button>

          {/* Hint text */}
          <div className="absolute top-4 left-4 text-white/80 text-sm bg-black/30 px-3 py-2 rounded-lg">
            클릭하면 닫힙니다
          </div>

          {/* Zoomed content */}
          <div
            className="max-w-[95vw] max-h-[95vh] overflow-auto bg-white dark:bg-gray-900 rounded-lg shadow-2xl p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="min-w-full">
              {children}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
