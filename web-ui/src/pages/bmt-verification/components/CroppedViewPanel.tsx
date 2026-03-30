import { Image as ImageIcon } from 'lucide-react';
import type { CroppedView } from '../types';

interface CroppedViewPanelProps {
  views: CroppedView[];
  selectedView: CroppedView | null;
  onSelectView: (view: CroppedView) => void;
}

export default function CroppedViewPanel({ views, selectedView, onSelectView }: CroppedViewPanelProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
        Cropped Views
      </h3>

      {views.length === 0 && (
        <p className="text-sm text-gray-400 dark:text-gray-500 italic">No views available</p>
      )}

      <div className="grid grid-cols-2 gap-3">
        {views.map((view) => {
          const isSelected = selectedView?.id === view.id;
          return (
            <button
              key={view.id}
              type="button"
              onClick={() => onSelectView(view)}
              className={`
                group relative rounded-lg overflow-hidden border-2 transition-all
                ${isSelected
                  ? 'border-blue-500 ring-2 ring-blue-500/30 shadow-lg'
                  : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600'}
                bg-white dark:bg-gray-800
              `}
            >
              {/* Thumbnail */}
              <div className="aspect-[4/3] bg-gray-100 dark:bg-gray-900 flex items-center justify-center overflow-hidden">
                <img
                  src={view.imagePath}
                  alt={view.viewName}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                  }}
                />
                <div className="hidden flex-col items-center gap-1 text-gray-400 dark:text-gray-600">
                  <ImageIcon size={24} />
                  <span className="text-xs">No image</span>
                </div>
              </div>

              {/* Label */}
              <div className="p-2 flex items-center justify-between">
                <span className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                  {view.viewName}
                </span>
                <span className={`
                  text-[10px] font-semibold px-1.5 py-0.5 rounded-full
                  ${view.tags.length > 0
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}
                `}>
                  {view.tags.length} TAG{view.tags.length !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-blue-500 ring-2 ring-white dark:ring-gray-800" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
