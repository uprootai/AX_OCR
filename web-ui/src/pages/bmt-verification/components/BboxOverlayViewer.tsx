import { useState, useCallback, type MouseEvent } from 'react';
import { Check, X, Edit3, Plus, MousePointer } from 'lucide-react';
import type { CroppedView } from '../types';

type TagState = 'pending' | 'approved' | 'rejected' | 'edited';

interface BboxOverlayViewerProps {
  view: CroppedView;
  onTagAction: (tagId: string, action: 'approve' | 'reject' | 'edit') => void;
  onAddManualTag: (x: number, y: number) => void;
}

const STATE_STYLES: Record<TagState, { border: string; bg: string; icon?: typeof Check }> = {
  pending:  { border: 'border-blue-500 border-dashed', bg: 'bg-blue-500/15' },
  approved: { border: 'border-green-500 border-solid', bg: 'bg-green-500/20', icon: Check },
  rejected: { border: 'border-red-500 border-solid', bg: 'bg-red-500/20', icon: X },
  edited:   { border: 'border-orange-500 border-solid', bg: 'bg-orange-500/20', icon: Edit3 },
};

export default function BboxOverlayViewer({ view, onTagAction, onAddManualTag }: BboxOverlayViewerProps) {
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [tagStates, setTagStates] = useState<Record<string, TagState>>({});
  const [showManualInput, setShowManualInput] = useState<{ x: number; y: number } | null>(null);
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [manualPart, setManualPart] = useState('');

  const getState = (tagId: string): TagState => tagStates[tagId] ?? 'pending';

  const handleAction = useCallback((tagId: string, action: 'approve' | 'reject' | 'edit') => {
    if (action === 'edit') {
      setEditingTag(tagId);
      const tag = view.tags.find((t) => t.id === tagId);
      setEditValue(tag?.tagCode ?? '');
      return;
    }
    const stateMap: Record<string, TagState> = { approve: 'approved', reject: 'rejected' };
    setTagStates((prev) => ({ ...prev, [tagId]: stateMap[action] }));
    onTagAction(tagId, action);
    setSelectedTag(null);
  }, [onTagAction, view.tags]);

  const confirmEdit = useCallback((tagId: string) => {
    setTagStates((prev) => ({ ...prev, [tagId]: 'edited' }));
    onTagAction(tagId, 'edit');
    setEditingTag(null);
    setSelectedTag(null);
  }, [onTagAction]);

  const handleImageClick = useCallback((e: MouseEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest('[data-bbox]')) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setSelectedTag(null);
    setShowManualInput({ x, y });
  }, []);

  const submitManual = useCallback(() => {
    if (!showManualInput || !manualCode) return;
    onAddManualTag(showManualInput.x, showManualInput.y);
    setShowManualInput(null);
    setManualCode('');
    setManualPart('');
  }, [showManualInput, manualCode, onAddManualTag]);

  return (
    <div className="space-y-2">
      {/* Image + overlays */}
      <div className="relative cursor-crosshair select-none" onClick={handleImageClick}>
        <img src={view.imagePath} alt={view.viewName} className="w-full rounded-lg" draggable={false} />

        {view.tags.map((tag) => {
          const bb = tag.boundingBox;
          if (!bb) return null;
          const state = getState(tag.id);
          const style = STATE_STYLES[state];
          const Icon = style.icon;
          const isSelected = selectedTag === tag.id;

          return (
            <div key={tag.id} data-bbox>
              {/* Label above bbox */}
              <div
                className="absolute text-[10px] font-bold text-white bg-gray-800/80 px-1 rounded"
                style={{ left: `${bb.x}%`, top: `${bb.y - 3}%` }}
              >
                {tag.tagCode}
              </div>

              {/* Bbox rectangle */}
              <div
                className={`absolute border-2 rounded cursor-pointer transition-all ${style.border} ${style.bg} ${isSelected ? 'ring-2 ring-white/60' : ''}`}
                style={{ left: `${bb.x}%`, top: `${bb.y}%`, width: `${bb.w}%`, height: `${bb.h}%` }}
                onClick={(e) => { e.stopPropagation(); setSelectedTag(isSelected ? null : tag.id); setShowManualInput(null); }}
              >
                {Icon && <Icon className="w-3 h-3 absolute top-0.5 right-0.5 text-white drop-shadow" />}
              </div>

              {/* Popup tooltip */}
              {isSelected && (
                <div
                  className="absolute z-20 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 p-3 text-xs"
                  style={{ left: `${Math.min(bb.x + bb.w + 1, 70)}%`, top: `${bb.y}%` }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <p className="font-bold text-gray-900 dark:text-white text-sm mb-1">{tag.tagCode}</p>
                  <p className="text-gray-600 dark:text-gray-400">{tag.partName}</p>
                  <p className="text-gray-500 dark:text-gray-500 mt-1">
                    Confidence: <span className="font-medium">{Math.round(tag.confidence * 100)}%</span>
                  </p>
                  <p className="text-gray-500 dark:text-gray-500">Engine: {tag.ocrEngine}</p>

                  {editingTag === tag.id ? (
                    <div className="mt-2 flex gap-1">
                      <input
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="flex-1 px-1.5 py-1 border rounded text-xs dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        autoFocus
                      />
                      <button onClick={() => confirmEdit(tag.id)} className="px-2 py-1 bg-orange-500 text-white rounded text-xs hover:bg-orange-600">
                        <Check className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <div className="mt-2 flex gap-1">
                      <button onClick={() => handleAction(tag.id, 'approve')} className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded hover:bg-green-100 dark:hover:bg-green-900/50 font-medium">
                        <Check className="w-3 h-3" /> 승인
                      </button>
                      <button onClick={() => handleAction(tag.id, 'edit')} className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded hover:bg-orange-100 dark:hover:bg-orange-900/50 font-medium">
                        <Edit3 className="w-3 h-3" /> 수정
                      </button>
                      <button onClick={() => handleAction(tag.id, 'reject')} className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded hover:bg-red-100 dark:hover:bg-red-900/50 font-medium">
                        <X className="w-3 h-3" /> 거부
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Manual tag input */}
        {showManualInput && (
          <div
            className="absolute z-20 w-52 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 p-3 text-xs"
            style={{ left: `${Math.min(showManualInput.x, 70)}%`, top: `${showManualInput.y}%` }}
            onClick={(e) => e.stopPropagation()}
          >
            <p className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-1">
              <Plus className="w-3 h-3" /> 수작업 TAG 추가
            </p>
            <input placeholder="TAG 코드" value={manualCode} onChange={(e) => setManualCode(e.target.value)}
              className="w-full mb-1.5 px-2 py-1 border rounded text-xs dark:bg-gray-700 dark:border-gray-600 dark:text-white" autoFocus />
            <input placeholder="부품명" value={manualPart} onChange={(e) => setManualPart(e.target.value)}
              className="w-full mb-2 px-2 py-1 border rounded text-xs dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
            <div className="flex gap-1">
              <button onClick={submitManual} disabled={!manualCode}
                className="flex-1 px-2 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:opacity-40 font-medium">
                추가
              </button>
              <button onClick={() => setShowManualInput(null)}
                className="px-2 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded text-xs hover:bg-gray-200 dark:hover:bg-gray-600">
                취소
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-[11px] text-gray-500 dark:text-gray-400 px-1">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-dashed border-blue-500 bg-blue-500/15 inline-block" /> 미확인</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-green-500 bg-green-500/20 inline-block" /> 승인</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-orange-500 bg-orange-500/20 inline-block" /> 수정</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-red-500 bg-red-500/20 inline-block" /> 거부</span>
        <span className="flex items-center gap-1"><MousePointer className="w-3 h-3" /> 빈 영역 클릭 = 수작업 추가</span>
      </div>
    </div>
  );
}
