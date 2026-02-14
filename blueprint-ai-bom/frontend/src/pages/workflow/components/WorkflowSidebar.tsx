/**
 * Workflow Sidebar Component
 * 워크플로우 사이드바 - 세션 관리, 설정, 캐시 관리
 * Phase 2C: 이미지 검토 기능 통합
 */

import React, { useRef, useState } from 'react';
import {
  Settings,
  Loader2,
  ChevronRight,
  ChevronLeft,
  Trash2,
  X,
  Moon,
  Sun,
  Download,
  Upload,
  Cpu,
  Zap,
  CheckSquare,
  Square,
} from 'lucide-react';
import { sessionApi } from '../../../lib/api';
import type { GPUStatus } from '../../../lib/api';
import type { SessionImage } from '../../../types';
import { SidebarImagePanel } from './SidebarImagePanel';
import { SidebarReferenceManager } from './SidebarReferenceManager';

interface Session {
  session_id: string;
  filename: string;
  detection_count: number;
  features?: string[];
}

// Feature 이름 매핑
const FEATURE_NAMES: Record<string, string> = {
  symbol_detection: '심볼 검출',
  dimension_ocr: '치수 OCR',
  bom_generation: 'BOM 생성',
  gdt_analysis: 'GD&T 분석',
  tolerance_analysis: '공차 분석',
  table_extraction: '테이블 추출',
  human_verification: 'HITL 검증',
};

interface WorkflowSidebarProps {
  // State
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  darkMode: boolean;
  setDarkMode: (dark: boolean) => void;
  gpuStatus: GPUStatus | null;
  // Sessions
  currentSession: {
    session_id: string;
    filename: string;
    features?: string[];
    template_name?: string;
    workflow_definition?: { nodes?: unknown[] };
    workflow_locked?: boolean;
    drawing_type?: string;
  } | null;
  sessions: Session[];
  projectId?: string;
  detectionCount: number;
  // Image management (Phase 2C)
  sessionImageCount?: number;
  onImagesAdded?: () => void;
  onImageSelect?: (imageId: string, image: SessionImage) => void;
  onImagesSelect?: (imageIds: string[], images: SessionImage[]) => void;
  onExportReady?: () => void;
  // Reference drawing type
  drawingType?: string;
  onDrawingTypeChange?: (type: string) => void;
  // GT management
  onUploadGT?: (imageId: string, file: File) => Promise<void>;
  // Handlers
  onNewSession: () => void;
  onLoadSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onClearCache: (type: 'all' | 'memory') => void;
  onRunAnalysis?: () => void;
  onSessionImported?: (sessionId: string) => void;
  // Loading states
  isLoading: boolean;
  isClearingCache: boolean;
}

export function WorkflowSidebar({
  sidebarCollapsed,
  setSidebarCollapsed,
  darkMode,
  setDarkMode,
  gpuStatus,
  currentSession,
  sessions,
  projectId,
  detectionCount: _detectionCount,
  sessionImageCount: _sessionImageCount = 0,
  onImagesAdded,
  onImageSelect,
  onImagesSelect,
  onExportReady: _onExportReady,
  onNewSession: _onNewSession,
  onLoadSession,
  onDeleteSession,
  onClearCache,
  onRunAnalysis,
  onSessionImported,
  drawingType: externalDrawingType,
  onDrawingTypeChange,
  onUploadGT,
  isLoading,
  isClearingCache,
}: WorkflowSidebarProps) {
  const importFileRef = useRef<HTMLInputElement>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // 참조 도면 유형 상태
  const [localDrawingType, setLocalDrawingType] = useState<string>('auto');
  const effectiveDrawingType = externalDrawingType || localDrawingType || currentSession?.drawing_type || 'auto';

  const handleDrawingTypeChange = (newType: string) => {
    setLocalDrawingType(newType);
    onDrawingTypeChange?.(newType);
  };

  // Export 핸들러 (JSON)
  const handleExportSession = async () => {
    if (!currentSession) return;
    setIsExporting(true);
    try {
      await sessionApi.exportJson(currentSession.session_id, true, true);
    } catch (error) {
      console.error('Export failed:', error);
      alert('세션 백업에 실패했습니다.');
    } finally {
      setIsExporting(false);
    }
  };

  // Import 핸들러
  const handleImportSession = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsImporting(true);
    try {
      const response = await sessionApi.importJson(file);
      onSessionImported?.(response.session_id);
      onLoadSession(response.session_id);
      alert('세션을 성공적으로 Import했습니다.');
    } catch (error) {
      console.error('Import failed:', error);
      alert('세션 Import에 실패했습니다. 유효한 JSON 파일인지 확인해주세요.');
    } finally {
      setIsImporting(false);
      if (importFileRef.current) importFileRef.current.value = '';
    }
  };

  return (
    <aside className={`${sidebarCollapsed ? 'w-16' : 'w-72'} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen transition-all duration-300 flex-shrink-0`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <h1 className="text-lg font-bold text-gray-900 dark:text-white" title="AI 기반 도면 분석 및 BOM 추출 시스템">Blueprint AI</h1>
          )}
          <div className="flex items-center space-x-1">
            {!sidebarCollapsed && (
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
                title="화면 테마를 밝게/어둡게 전환합니다"
              >
                {darkMode ? <Sun className="w-4 h-4 text-yellow-500" /> : <Moon className="w-4 h-4 text-gray-600" />}
              </button>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
              title="사이드바를 접거나 펼칩니다"
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* API Status - GPU 사용 API */}
        {!sidebarCollapsed && currentSession?.features && currentSession.features.includes('symbol_detection') && (
          <div className="mt-3 space-y-1" title="YOLO 심볼 검출 모델의 GPU/CPU 사용 상태">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">ML API 상태</div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-700 dark:text-gray-300">YOLO (심볼 검출)</span>
              <span className={`flex items-center gap-1 ${gpuStatus?.available ? 'text-green-600' : 'text-blue-600'}`}>
                {gpuStatus?.available ? <Zap className="w-3 h-3" /> : <Cpu className="w-3 h-3" />}
                {gpuStatus?.available ? 'GPU' : 'CPU'}
              </span>
            </div>
          </div>
        )}

        {/* 참조 도면 유형 + 참조 세트 관리 */}
        {!sidebarCollapsed && currentSession && (
          <SidebarReferenceManager
            effectiveDrawingType={effectiveDrawingType}
            onDrawingTypeChange={handleDrawingTypeChange}
          />
        )}
      </div>

      {/* Sessions */}
      {!sidebarCollapsed && (
        <>
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 overflow-y-auto min-h-0">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300" title="현재 작업 중인 도면 세션">현재 세션</h2>
            </div>
            {currentSession ? (
              <div className="text-sm">
                <p className="font-medium text-gray-900 dark:text-white truncate" title="세션에 업로드된 원본 도면 파일">{currentSession.filename}</p>
                {currentSession.features && currentSession.features.length > 0 && (
                  <p className="text-xs text-gray-500">
                    {currentSession.features.map(f => FEATURE_NAMES[f] || f).join(' · ')}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">세션 없음</p>
            )}

            {/* Export/Import 버튼 */}
            <div className="mt-3 grid grid-cols-2 gap-2">
              <button
                onClick={handleExportSession}
                disabled={!currentSession || isExporting}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="현재 세션을 JSON으로 백업합니다"
              >
                {isExporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                <span>세션 백업</span>
              </button>
              <button
                onClick={() => importFileRef.current?.click()}
                disabled={isImporting}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="이전에 백업한 JSON 파일을 불러와 세션을 복원합니다"
              >
                {isImporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
                <span>Import</span>
              </button>
              <input ref={importFileRef} type="file" accept=".json" onChange={handleImportSession} className="hidden" />
            </div>

            {/* 세션 이미지 패널 */}
            <SidebarImagePanel
              currentSession={currentSession}
              effectiveDrawingType={effectiveDrawingType}
              onImageSelect={onImageSelect}
              onImagesSelect={onImagesSelect}
              onImagesAdded={onImagesAdded}
              onUploadGT={onUploadGT}
              onLoadSession={onLoadSession}
            />
          </div>

          {/* 세션 목록 */}
          <div className="flex-shrink-0 overflow-y-auto p-4 max-h-[240px]">
            <div className="flex items-center justify-between mb-2">
              {!isSelectMode ? (
                <>
                  <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300" title="최근 작업한 세션 목록. 클릭하면 해당 세션으로 전환">
                    {projectId ? '프로젝트 세션' : '최근 세션'}
                  </h2>
                  {sessions.length > 0 && (
                    <button
                      onClick={() => { setIsSelectMode(true); setSelectedIds(new Set()); }}
                      className="text-xs px-2 py-0.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      title="여러 세션을 선택하여 일괄 삭제할 수 있습니다"
                    >
                      선택
                    </button>
                  )}
                </>
              ) : (
                <>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        const allIds = sessions.slice(0, 10).map(s => s.session_id);
                        setSelectedIds(prev =>
                          prev.size === allIds.length ? new Set() : new Set(allIds)
                        );
                      }}
                      className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      {selectedIds.size === sessions.slice(0, 10).length
                        ? '전체해제'
                        : '전체선택'}
                    </button>
                    <button
                      onClick={async () => {
                        if (selectedIds.size === 0) return;
                        if (confirm(`선택한 세션 ${selectedIds.size}개를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
                          for (const id of selectedIds) { await onDeleteSession(id); }
                          setSelectedIds(new Set());
                          setIsSelectMode(false);
                        }
                      }}
                      disabled={selectedIds.size === 0}
                      className="flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <Trash2 className="w-3 h-3" />
                      <span>{selectedIds.size}개 삭제</span>
                    </button>
                  </div>
                  <button
                    onClick={() => { setIsSelectMode(false); setSelectedIds(new Set()); }}
                    className="text-xs px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 transition-colors"
                  >
                    취소
                  </button>
                </>
              )}
            </div>
            {sessions.length === 0 ? (
              <p className="text-sm text-gray-500">세션이 없습니다.</p>
            ) : (
              <ul className="space-y-2">
                {sessions.slice(0, 10).map(session => {
                  const isCurrent = currentSession?.session_id === session.session_id;
                  const isSelected = selectedIds.has(session.session_id);
                  return (
                    <li
                      key={session.session_id}
                      title="클릭하여 이 세션으로 전환"
                      className={`group relative p-2 rounded-lg text-sm cursor-pointer transition-colors ${
                        isCurrent
                          ? 'bg-primary-50 dark:bg-primary-900/30 border border-primary-200'
                          : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100'
                      }`}
                      onClick={() => {
                        if (isSelectMode) {
                          setSelectedIds(prev => {
                            const next = new Set(prev);
                            if (next.has(session.session_id)) next.delete(session.session_id);
                            else next.add(session.session_id);
                            return next;
                          });
                        } else {
                          onLoadSession(session.session_id);
                        }
                      }}
                    >
                      <div className="flex items-start gap-2">
                        {isSelectMode && (
                          <div className="flex-shrink-0 mt-0.5">
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            ) : (
                              <Square className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                            )}
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate text-gray-900 dark:text-white">{session.filename}</p>
                          <p className="text-xs text-gray-500">
                            {session.features && session.features.length > 0
                              ? session.features.map(f => FEATURE_NAMES[f] || f).join(' · ')
                              : `${session.detection_count}개 검출`}
                          </p>
                        </div>
                      </div>
                      {!isSelectMode && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm('세션을 삭제하시겠습니까?')) onDeleteSession(session.session_id);
                          }}
                          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 text-gray-400 hover:text-red-600"
                          title="이 세션을 삭제합니다 (되돌릴 수 없음)"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {/* 분석 실행 */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            {currentSession?.features && currentSession.features.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center space-x-2 mb-2" title="빌더(Builder)에서 워크플로우에 포함된 분석 기능들">
                  <Settings className="w-4 h-4 text-gray-500" />
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">활성화된 기능</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full" title="워크플로우 빌더에서 설정된 기능. 변경은 Builder 탭에서">Builder</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {currentSession.features.map((feature) => (
                    <span key={feature} className="text-[10px] px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full">
                      {FEATURE_NAMES[feature] || feature}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <button
              onClick={onRunAnalysis}
              disabled={isLoading || !currentSession}
              className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
              title="활성화된 기능(심볼 검출, OCR 등)을 순차 실행합니다"
            >
              {isLoading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /><span>분석 중...</span></>
              ) : (
                <><Zap className="w-5 h-5" /><span>분석 실행</span></>
              )}
            </button>
            {!currentSession && (
              <p className="mt-2 text-[10px] text-center text-gray-400">세션을 선택하거나 이미지를 업로드하세요</p>
            )}
          </div>

          {/* Cache */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => onClearCache('memory')}
                disabled={isClearingCache}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 rounded-lg hover:bg-gray-100 text-xs disabled:opacity-50"
                title="GPU/CPU에 로드된 ML 모델을 해제합니다. 다음 분석 시 자동 재로드"
              >
                {isClearingCache ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                <span>메모리</span>
              </button>
              <button
                onClick={() => onClearCache('all')}
                disabled={isClearingCache}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-300 rounded-lg hover:bg-red-100 text-xs disabled:opacity-50"
                title="메모리 해제 + 임시 파일 정리. 디스크 공간 확보"
              >
                {isClearingCache ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                <span>전체</span>
              </button>
            </div>
          </div>
        </>
      )}

    </aside>
  );
}
