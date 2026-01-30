/**
 * ReferencePanel - 클래스별 참조 도면 패널
 * AI가 인식하지 못했거나 틀린 부분을 작업자가 육안으로 최종 결정하기 위한 참조 도면
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ChevronDown, ChevronRight, ChevronsUpDown, PanelRightClose, PanelRightOpen, Search } from 'lucide-react';
import axios from 'axios';
import logger from '../lib/logger';
import { API_BASE_URL } from '../lib/constants';

interface ClassExample {
  class_name: string;
  image_base64: string;
  filename: string;
}

interface ReferencePanelProps {
  onClose?: () => void;
  drawingType?: 'pid' | 'electrical' | 'sld' | string;
}

const MIN_WIDTH = 200;
const MAX_WIDTH = 800;
const DEFAULT_WIDTH = 320;

export function ReferencePanel({ drawingType = 'electrical' }: ReferencePanelProps) {
  const [examples, setExamples] = useState<ClassExample[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [collapsed, setCollapsed] = useState(false);
  const [panelWidth, setPanelWidth] = useState(DEFAULT_WIDTH);
  const isResizing = useRef(false);

  // 드래그 리사이즈
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizing.current = true;
    const startX = e.clientX;
    const startWidth = panelWidth;

    const onMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      // 왼쪽 경계를 드래그하므로 startX - e.clientX 가 양수면 넓어짐
      const delta = startX - e.clientX;
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth + delta));
      setPanelWidth(newWidth);
    };

    const onMouseUp = () => {
      isResizing.current = false;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, [panelWidth]);

  // Load class examples from backend
  useEffect(() => {
    const loadExamples = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // drawing_type을 쿼리 파라미터로 전달
        const apiDrawingType = drawingType === 'pid' ? 'pid' : 'electrical';
        const { data } = await axios.get<{ examples: ClassExample[] }>(
          `${API_BASE_URL}/api/config/class-examples?drawing_type=${apiDrawingType}`
        );
        const loaded = data.examples || [];
        setExamples(loaded);
        // 기본적으로 모든 항목 펼침
        setExpandedItems(new Set(loaded.map(ex => ex.class_name)));
      } catch (err) {
        logger.error('Failed to load class examples:', err);
        setError('참조 도면을 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    loadExamples();
  }, [drawingType]);

  // Filter examples by search query
  const filteredExamples = examples.filter(ex =>
    ex.class_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const allExpanded = filteredExamples.length > 0 && filteredExamples.every(ex => expandedItems.has(ex.class_name));

  // Toggle all items
  const toggleAll = () => {
    if (allExpanded) {
      setExpandedItems(new Set());
    } else {
      setExpandedItems(new Set(filteredExamples.map(ex => ex.class_name)));
    }
  };

  // Toggle item expansion
  const toggleExpand = (className: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(className)) {
        next.delete(className);
      } else {
        next.add(className);
      }
      return next;
    });
  };

  // 접힌 상태
  if (collapsed) {
    return (
      <aside className="bg-white border-l border-gray-200 flex flex-col h-full w-10">
        <button
          onClick={() => setCollapsed(false)}
          className="flex items-center justify-center w-full h-12 hover:bg-gray-100"
          title="참조 도면 펼치기"
        >
          <PanelRightOpen className="w-5 h-5 text-gray-500" />
        </button>
        <div className="flex-1 flex items-center justify-center">
          <span className="text-xs text-gray-400 writing-vertical" style={{ writingMode: 'vertical-rl' }}>
            참조 도면
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside className="bg-white border-l border-gray-200 flex flex-col h-full relative" style={{ width: panelWidth }}>
      {/* 리사이즈 핸들 */}
      <div
        onMouseDown={handleMouseDown}
        className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-400 active:bg-blue-500 z-10"
        title="드래그하여 너비 조정"
      />

      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-gray-900 whitespace-nowrap">참조 도면</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={toggleAll}
            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded"
            title={allExpanded ? '모두 접기' : '모두 펼치기'}
          >
            <ChevronsUpDown className="w-4 h-4" />
            {allExpanded ? '접기' : '펼치기'}
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="p-1 hover:bg-gray-100 rounded"
            title="패널 접기"
          >
            <PanelRightClose className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="클래스명 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto mb-2" />
            <p>로딩 중...</p>
          </div>
        ) : error ? (
          <div className="p-4 text-center text-red-600">
            <p>{error}</p>
            <p className="text-sm text-gray-500 mt-2">
              백엔드에서 class_examples API를 확인하세요.
            </p>
          </div>
        ) : filteredExamples.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {searchQuery ? (
              <p>"{searchQuery}"에 해당하는 클래스가 없습니다.</p>
            ) : (
              <p>참조 도면이 없습니다.</p>
            )}
          </div>
        ) : (
          <div className="p-2" style={{ columns: '180px auto', columnGap: '8px' }}>
            {filteredExamples.map((example) => {
              const isExpanded = expandedItems.has(example.class_name);
              return (
                <div key={example.class_name} className="mb-2 break-inside-avoid">
                  <button
                    onClick={() => toggleExpand(example.class_name)}
                    className="w-full flex items-center justify-between text-left hover:bg-gray-50 rounded px-2 py-1.5"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900 text-xs truncate">
                        {example.class_name}
                      </p>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-3 h-3 text-gray-400 shrink-0 ml-1" />
                    ) : (
                      <ChevronRight className="w-3 h-3 text-gray-400 shrink-0 ml-1" />
                    )}
                  </button>

                  {isExpanded && example.image_base64 && (
                    <div className="mt-1 bg-gray-50 rounded p-1.5">
                      <img
                        src={`data:image/jpeg;base64,${example.image_base64}`}
                        alt={example.class_name}
                        className="w-full rounded border border-gray-200"
                      />
                      <p className="text-[10px] text-gray-500 mt-0.5 text-center truncate">
                        {example.filename}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-500 text-center">
          {filteredExamples.length}개 클래스 참조 가능
        </p>
      </div>
    </aside>
  );
}
