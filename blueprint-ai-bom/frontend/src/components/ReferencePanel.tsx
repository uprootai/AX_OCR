/**
 * ReferencePanel - 클래스별 참조 이미지 패널
 * Streamlit의 심볼 참조 기능과 동일
 */

import { useState, useEffect } from 'react';
import { X, ChevronDown, ChevronRight, Search } from 'lucide-react';
import axios from 'axios';

interface ClassExample {
  class_name: string;
  image_base64: string;
  filename: string;
}

interface ReferencePanelProps {
  onClose: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5020';

export function ReferencePanel({ onClose }: ReferencePanelProps) {
  const [examples, setExamples] = useState<ClassExample[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  // Load class examples from backend
  useEffect(() => {
    const loadExamples = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const { data } = await axios.get<{ examples: ClassExample[] }>(
          `${API_BASE_URL}/api/config/class-examples`
        );
        setExamples(data.examples || []);
      } catch (err) {
        console.error('Failed to load class examples:', err);
        setError('참조 이미지를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    loadExamples();
  }, []);

  // Filter examples by search query
  const filteredExamples = examples.filter(ex =>
    ex.class_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  return (
    <aside className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">참조 이미지</h2>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
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
              <p>참조 이미지가 없습니다.</p>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredExamples.map((example) => {
              const isExpanded = expandedItems.has(example.class_name);
              return (
                <div key={example.class_name} className="p-3">
                  <button
                    onClick={() => toggleExpand(example.class_name)}
                    className="w-full flex items-center justify-between text-left hover:bg-gray-50 rounded p-2 -m-2"
                  >
                    <div>
                      <p className="font-medium text-gray-900 text-sm">
                        {example.class_name}
                      </p>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    )}
                  </button>

                  {isExpanded && example.image_base64 && (
                    <div className="mt-3 bg-gray-50 rounded-lg p-2">
                      <img
                        src={`data:image/jpeg;base64,${example.image_base64}`}
                        alt={example.class_name}
                        className="w-full rounded border border-gray-200"
                      />
                      <p className="text-xs text-gray-500 mt-1 text-center">
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
