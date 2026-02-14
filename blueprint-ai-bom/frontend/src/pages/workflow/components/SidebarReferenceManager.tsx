/**
 * Sidebar Reference Manager - 참조 도면 유형 선택 + 커스텀 참조 세트 관리
 */

import { useRef, useState, useCallback, useEffect } from 'react';
import {
  Loader2,
  Trash2,
  Upload,
  RefreshCw,
  BookOpen,
  FolderPlus,
  FolderOpen,
} from 'lucide-react';
import { API_BASE_URL } from '../../../lib/constants';

// 도면 유형 옵션
const DRAWING_TYPE_OPTIONS: { value: string; label: string; description: string }[] = [
  { value: 'electrical', label: '전기/P&ID 심볼', description: '전기 회로도, 배관 계장도' },
  { value: 'mechanical', label: '기계 도면', description: '기계 부품도, 조립도' },
];

interface ReferenceSet {
  id: string;
  name: string;
  description?: string;
  image_count: number;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

interface SidebarReferenceManagerProps {
  effectiveDrawingType: string;
  onDrawingTypeChange: (type: string) => void;
}

export function SidebarReferenceManager({
  effectiveDrawingType,
  onDrawingTypeChange,
}: SidebarReferenceManagerProps) {
  const refSetUploadRef = useRef<HTMLInputElement>(null);
  const [referenceSets, setReferenceSets] = useState<ReferenceSet[]>([]);
  const [isLoadingRefSets, setIsLoadingRefSets] = useState(false);
  const [showRefSetManager, setShowRefSetManager] = useState(false);
  const [isUploadingRefSet, setIsUploadingRefSet] = useState(false);
  const [newRefSetName, setNewRefSetName] = useState('');
  const [newRefSetDescription, setNewRefSetDescription] = useState('');

  // 참조 세트 목록 로드
  const loadReferenceSets = useCallback(async () => {
    setIsLoadingRefSets(true);
    try {
      const response = await fetch(`${API_BASE_URL}/reference-sets`);
      if (response.ok) {
        const sets = await response.json();
        setReferenceSets(sets);
      }
    } catch (error) {
      console.error('Failed to load reference sets:', error);
    } finally {
      setIsLoadingRefSets(false);
    }
  }, []);

  useEffect(() => { loadReferenceSets(); }, [loadReferenceSets]);

  // 참조 세트 업로드
  const handleRefSetUpload = useCallback(async (file: File) => {
    if (!file.name.endsWith('.zip')) {
      alert('ZIP 파일만 업로드 가능합니다.');
      return;
    }
    if (!newRefSetName.trim()) {
      alert('세트 이름을 입력해주세요.');
      return;
    }

    setIsUploadingRefSet(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', newRefSetName);
      if (newRefSetDescription) formData.append('description', newRefSetDescription);

      const response = await fetch(`${API_BASE_URL}/reference-sets`, {
        method: 'POST', body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const newSet = await response.json();
      setReferenceSets(prev => [...prev, newSet]);
      setNewRefSetName('');
      setNewRefSetDescription('');
      alert(`참조 세트 "${newSet.name}"이(가) 생성되었습니다. (${newSet.image_count}개 이미지)`);
    } catch (error) {
      console.error('Reference set upload failed:', error);
      alert(`참조 세트 업로드 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    } finally {
      setIsUploadingRefSet(false);
      if (refSetUploadRef.current) refSetUploadRef.current.value = '';
    }
  }, [newRefSetName, newRefSetDescription]);

  // 참조 세트 삭제
  const handleDeleteRefSet = useCallback(async (setId: string, setName: string) => {
    if (!confirm(`"${setName}" 세트를 삭제하시겠습니까?`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/reference-sets/${setId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Delete failed');

      setReferenceSets(prev => prev.filter(s => s.id !== setId));
      if (effectiveDrawingType === setId) onDrawingTypeChange('auto');
    } catch (error) {
      console.error('Reference set delete failed:', error);
      alert('참조 세트 삭제에 실패했습니다.');
    }
  }, [effectiveDrawingType, onDrawingTypeChange]);

  return (
    <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-purple-500" />
          <span className="text-xs font-medium text-gray-600 dark:text-gray-400" title="오른쪽 패널에 표시할 참조 클래스 이미지 세트를 선택합니다">참조 도면 유형</span>
        </div>
        <button
          onClick={() => setShowRefSetManager(!showRefSetManager)}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded text-gray-500 hover:text-purple-500 transition-colors"
          title="ZIP 파일로 커스텀 참조 세트를 업로드합니다 (파일명 = 클래스명)"
        >
          <FolderPlus className="w-3.5 h-3.5" />
        </button>
      </div>
      <select
        value={effectiveDrawingType}
        onChange={(e) => onDrawingTypeChange(e.target.value)}
        className="w-full px-2 py-1.5 text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-700 dark:text-gray-300"
        title="도면 유형에 맞는 참조 클래스를 선택하세요"
      >
        <optgroup label="기본 제공">
          {DRAWING_TYPE_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </optgroup>
        {referenceSets.filter(s => !s.is_builtin).length > 0 && (
          <optgroup label="커스텀 세트">
            {referenceSets.filter(s => !s.is_builtin).map(set => (
              <option key={set.id} value={set.id}>{set.name} ({set.image_count}개)</option>
            ))}
          </optgroup>
        )}
      </select>
      <p className="mt-1 text-[9px] text-gray-400">
        {DRAWING_TYPE_OPTIONS.find(o => o.value === effectiveDrawingType)?.description ||
          referenceSets.find(s => s.id === effectiveDrawingType)?.description ||
          '사용자 정의 참조 세트'}
      </p>

      {/* 커스텀 참조 세트 관리 패널 */}
      {showRefSetManager && (
        <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-semibold text-gray-600 dark:text-gray-400 uppercase">
              커스텀 참조 세트
            </span>
            {isLoadingRefSets ? (
              <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
            ) : (
              <button onClick={loadReferenceSets} className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded" title="새로고침">
                <RefreshCw className="w-3 h-3 text-gray-400" />
              </button>
            )}
          </div>

          {/* 커스텀 세트 목록 */}
          <div className="space-y-1 max-h-24 overflow-y-auto mb-2">
            {referenceSets.filter(s => !s.is_builtin).length === 0 ? (
              <p className="text-[10px] text-gray-400 text-center py-2">업로드된 커스텀 세트가 없습니다</p>
            ) : (
              referenceSets.filter(s => !s.is_builtin).map(set => (
                <div
                  key={set.id}
                  className={`flex items-center justify-between p-1.5 rounded text-[10px] ${
                    effectiveDrawingType === set.id
                      ? 'bg-purple-100 dark:bg-purple-900/40 border border-purple-300 dark:border-purple-700'
                      : 'bg-white dark:bg-gray-600 border border-transparent'
                  }`}
                >
                  <div className="flex-1 cursor-pointer" onClick={() => onDrawingTypeChange(set.id)}>
                    <div className="font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                      <FolderOpen className="w-3 h-3 text-purple-500" />{set.name}
                    </div>
                    <div className="text-gray-400">{set.image_count}개 이미지</div>
                  </div>
                  <button onClick={() => handleDeleteRefSet(set.id, set.name)} className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-gray-400 hover:text-red-500" title="삭제">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* 새 세트 업로드 */}
          <div className="border-t border-gray-200 dark:border-gray-600 pt-2">
            <div className="text-[10px] font-semibold text-gray-600 dark:text-gray-400 mb-1">새 세트 추가</div>
            <input type="text" placeholder="세트 이름" value={newRefSetName} onChange={(e) => setNewRefSetName(e.target.value)}
              className="w-full px-2 py-1 text-[10px] bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 rounded mb-1 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            <input type="text" placeholder="설명 (선택)" value={newRefSetDescription} onChange={(e) => setNewRefSetDescription(e.target.value)}
              className="w-full px-2 py-1 text-[10px] bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 rounded mb-1.5 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            <button
              onClick={() => refSetUploadRef.current?.click()}
              disabled={isUploadingRefSet || !newRefSetName.trim()}
              className="w-full flex items-center justify-center space-x-1 px-2 py-1.5 bg-purple-500 hover:bg-purple-600 text-white rounded text-[10px] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isUploadingRefSet ? (
                <><Loader2 className="w-3 h-3 animate-spin" /><span>업로드 중...</span></>
              ) : (
                <><Upload className="w-3 h-3" /><span>ZIP 파일 선택</span></>
              )}
            </button>
            <input ref={refSetUploadRef} type="file" accept=".zip"
              onChange={(e) => { const file = e.target.files?.[0]; if (file) handleRefSetUpload(file); }}
              className="hidden" />
            <p className="text-[9px] text-gray-400 mt-1 text-center">이미지 파일명 = 클래스명</p>
          </div>
        </div>
      )}
    </div>
  );
}
