/**
 * Workflow Sidebar Component
 * 워크플로우 사이드바 — 세션 관리 + 이미지 탐색 + 세션 전환
 *
 * 구성:
 * 1. Header (Blueprint AI + 테마 + 접기)
 * 2. 현재 세션 정보 + Export/Import
 * 3. 세션 이미지 패널 (flex-1로 남은 공간 차지)
 * 4. 프로젝트 세션 목록 (컴팩트, 최대 160px)
 */

import { useState } from 'react';
import {
  ChevronRight,
  ChevronLeft,
  Trash2,
  X,
  Moon,
  Sun,
  CheckSquare,
  Square,
} from 'lucide-react';
import type { GPUStatus } from '../../../lib/api';
import type { SessionImage } from '../../../types';
import { SidebarImagePanel } from './SidebarImagePanel';

interface Session {
  session_id: string;
  filename: string;
  detection_count: number;
  features?: string[];
  project_id?: string;
  project_name?: string;
}

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
  currentSession,
  sessions,
  projectId,
  onImagesAdded,
  onImageSelect,
  onImagesSelect,
  onLoadSession,
  onDeleteSession,
  drawingType: externalDrawingType,
  onDrawingTypeChange,
  onUploadGT,
}: WorkflowSidebarProps) {
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const effectiveDrawingType = externalDrawingType || currentSession?.drawing_type || 'auto';

  return (
    <aside className={`${sidebarCollapsed ? 'w-16' : 'w-72'} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen transition-all duration-300 flex-shrink-0`}>
      {/* ===== 1. Header ===== */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">Blueprint AI</h1>
          )}
          <div className="flex items-center space-x-1">
            {!sidebarCollapsed && (
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                {darkMode ? <Sun className="w-4 h-4 text-yellow-500" /> : <Moon className="w-4 h-4 text-gray-600" />}
              </button>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {!sidebarCollapsed && (
        <>
          {/* ===== 2. 도면 유형 설정 ===== */}
          <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
            <label className="text-[10px] font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">도면 유형</label>
            <select
              value={effectiveDrawingType}
              onChange={(e) => onDrawingTypeChange?.(e.target.value)}
              className="w-full mt-1 px-2 py-1.5 text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-purple-500 text-gray-700 dark:text-gray-300"
            >
              <option value="auto">자동 감지</option>
              <option value="electrical_panel">전기 제어판</option>
              <option value="pid">P&ID (배관계장도)</option>
              <option value="dimension">치수 도면</option>
              <option value="assembly">조립도</option>
              <option value="dimension_bom">치수 + BOM</option>
            </select>
          </div>

          {/* ===== 3. 세션 이미지 패널 ===== */}
          <div className="overflow-y-auto px-3 py-2 border-b border-gray-200 dark:border-gray-700 min-h-0 max-h-[45vh]">
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

          {/* ===== 4. 프로젝트 세션 목록 ===== */}
          <div className="flex-1 overflow-y-auto px-3 py-2 min-h-[120px] max-h-[280px]">
            <div className="flex items-center justify-between mb-1.5">
              {!isSelectMode ? (
                <>
                  <h2 className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                    {projectId ? '프로젝트 세션' : '최근 세션'}
                    {sessions.length > 0 && (
                      <span className="ml-1 font-normal text-gray-400">({sessions.length})</span>
                    )}
                  </h2>
                  {sessions.length > 0 && (
                    <button
                      onClick={() => { setIsSelectMode(true); setSelectedIds(new Set()); }}
                      className="text-[10px] px-1.5 py-0.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
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
                        const allIds = sessions.map(s => s.session_id);
                        setSelectedIds(prev =>
                          prev.size === allIds.length ? new Set() : new Set(allIds)
                        );
                      }}
                      className="text-[10px] px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 transition-colors"
                    >
                      {selectedIds.size === sessions.length ? '전체해제' : '전체선택'}
                    </button>
                    <button
                      onClick={async () => {
                        if (selectedIds.size === 0) return;
                        if (confirm(`선택한 세션 ${selectedIds.size}개를 삭제하시겠습니까?`)) {
                          for (const id of selectedIds) { await onDeleteSession(id); }
                          setSelectedIds(new Set());
                          setIsSelectMode(false);
                        }
                      }}
                      disabled={selectedIds.size === 0}
                      className="flex items-center gap-0.5 text-[10px] px-1 py-0.5 rounded bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 transition-colors disabled:opacity-40"
                    >
                      <Trash2 className="w-2.5 h-2.5" />
                      <span>{selectedIds.size}개 삭제</span>
                    </button>
                  </div>
                  <button
                    onClick={() => { setIsSelectMode(false); setSelectedIds(new Set()); }}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 transition-colors"
                  >
                    취소
                  </button>
                </>
              )}
            </div>
            {sessions.length === 0 ? (
              <p className="text-xs text-gray-500">세션이 없습니다.</p>
            ) : (
              <ul className="space-y-1">
                {sessions.map(session => {
                  const isCurrent = currentSession?.session_id === session.session_id;
                  const isSelected = selectedIds.has(session.session_id);
                  return (
                    <li
                      key={session.session_id}
                      className={`group relative px-2 py-1.5 rounded text-xs cursor-pointer transition-colors ${
                        isCurrent
                          ? 'bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700'
                          : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
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
                      <div className="flex items-center gap-1.5">
                        {isSelectMode && (
                          <div className="flex-shrink-0">
                            {isSelected ? (
                              <CheckSquare className="w-3.5 h-3.5 text-blue-600" />
                            ) : (
                              <Square className="w-3.5 h-3.5 text-gray-400" />
                            )}
                          </div>
                        )}
                        <p className="flex-1 truncate font-medium text-gray-800 dark:text-gray-200">
                          {session.filename}
                        </p>
                      </div>
                      {!isSelectMode && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm('세션을 삭제하시겠습니까?')) onDeleteSession(session.session_id);
                          }}
                          className="absolute right-1 top-1/2 -translate-y-1/2 p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 text-gray-400 hover:text-red-600"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </>
      )}
    </aside>
  );
}
