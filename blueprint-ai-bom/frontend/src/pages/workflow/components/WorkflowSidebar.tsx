/**
 * Workflow Sidebar Component
 * 워크플로우 사이드바 - 세션 관리, 설정, 캐시 관리
 */

import {
  Settings,
  Loader2,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  Trash2,
  X,
  Moon,
  Sun,
  Cpu,
  RefreshCw,
  Ruler,
} from 'lucide-react';
import { AnalysisOptions } from '../../../components/AnalysisOptions';
import type { GPUStatus } from '../../../lib/api';
import type { DetectionConfig } from '../../../types';
import type { AnalysisOptionsData } from '../types/workflow';

interface Session {
  session_id: string;
  filename: string;
  detection_count: number;
}

interface WorkflowSidebarProps {
  // State
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  darkMode: boolean;
  setDarkMode: (dark: boolean) => void;
  gpuStatus: GPUStatus | null;
  config: DetectionConfig;
  setConfig: (config: DetectionConfig) => void;
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  showAnalysisOptions: boolean;
  setShowAnalysisOptions: (show: boolean) => void;
  // Sessions
  currentSession: { session_id: string; filename: string } | null;
  sessions: Session[];
  detectionCount: number;
  // Handlers
  onNewSession: () => void;
  onLoadSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onRunDetection: (config: DetectionConfig) => void;
  onClearCache: (type: 'all' | 'memory') => void;
  onAnalysisOptionsChange?: (options: AnalysisOptionsData) => void;
  onRunAnalysis?: () => void;
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
  config,
  setConfig,
  showSettings,
  setShowSettings,
  showAnalysisOptions,
  setShowAnalysisOptions,
  currentSession,
  sessions,
  detectionCount,
  onNewSession,
  onLoadSession,
  onDeleteSession,
  onRunDetection,
  onClearCache,
  onAnalysisOptionsChange,
  onRunAnalysis,
  isLoading,
  isClearingCache,
}: WorkflowSidebarProps) {
  const handleLoadSession = (sessionId: string) => {
    onLoadSession(sessionId);
  };

  return (
    <aside className={`${sidebarCollapsed ? 'w-16' : 'w-72'} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen transition-all duration-300 flex-shrink-0`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">Blueprint AI</h1>
          )}
          <div className="flex items-center space-x-1">
            {!sidebarCollapsed && (
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                {darkMode ? <Sun className="w-4 h-4 text-yellow-500" /> : <Moon className="w-4 h-4 text-gray-600" />}
              </button>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* GPU Status */}
        {!sidebarCollapsed && gpuStatus && (
          <div className="mt-3 text-xs">
            <div className={`flex items-center space-x-1 ${gpuStatus.available ? 'text-green-600' : 'text-blue-600'}`}>
              <Cpu className="w-3 h-3" />
              <span>{gpuStatus.available ? 'GPU' : 'CPU'} 모드</span>
            </div>
            {gpuStatus.available && (
              <div className="mt-1 text-gray-500">
                VRAM: {gpuStatus.memory_used}MB / {gpuStatus.memory_total}MB ({gpuStatus.memory_percent}%)
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sessions */}
      {!sidebarCollapsed && (
        <>
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">현재 세션</h2>
              {currentSession && (
                <button
                  onClick={onNewSession}
                  className="text-xs text-red-600 hover:text-red-700"
                >
                  새 세션
                </button>
              )}
            </div>
            {currentSession ? (
              <div className="text-sm">
                <p className="font-medium text-gray-900 dark:text-white truncate">{currentSession.filename}</p>
                <p className="text-xs text-gray-500">{detectionCount}개 검출</p>
              </div>
            ) : (
              <p className="text-sm text-gray-500">세션 없음</p>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">최근 세션</h2>
            {sessions.length === 0 ? (
              <p className="text-sm text-gray-500">세션이 없습니다.</p>
            ) : (
              <ul className="space-y-2">
                {sessions.slice(0, 10).map(session => (
                  <li
                    key={session.session_id}
                    className={`group relative p-2 rounded-lg text-sm cursor-pointer transition-colors ${currentSession?.session_id === session.session_id
                      ? 'bg-primary-50 dark:bg-primary-900/30 border border-primary-200'
                      : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100'
                      }`}
                    onClick={() => handleLoadSession(session.session_id)}
                  >
                    <p className="font-medium truncate text-gray-900 dark:text-white">{session.filename}</p>
                    <p className="text-xs text-gray-500">{session.detection_count}개 검출</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('세션을 삭제하시겠습니까?')) {
                          onDeleteSession(session.session_id);
                        }
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 text-gray-400 hover:text-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {/* 세션 전체 삭제 버튼 */}
            {sessions.length > 0 && (
              <button
                onClick={async () => {
                  if (confirm(`모든 세션(${sessions.length}개)을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
                    for (const session of sessions) {
                      await onDeleteSession(session.session_id);
                    }
                  }
                }}
                className="w-full mt-3 flex items-center justify-center space-x-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span>전체 삭제 ({sessions.length}개)</span>
              </button>
            )}
          </div>

          {/* Settings */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            {/* 기존 심볼 검출 설정 */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              <span className="flex items-center space-x-2 text-gray-700 dark:text-gray-300">
                <Settings className="w-4 h-4" />
                <span className="text-sm">심볼 검출 설정</span>
              </span>
              {showSettings ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
            {showSettings && (
              <div className="mt-3 space-y-3">
                <div>
                  <label className="text-xs text-gray-600 dark:text-gray-400">신뢰도: {config.confidence}</label>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.05"
                    value={config.confidence}
                    onChange={(e) => setConfig({ ...config, confidence: parseFloat(e.target.value) })}
                    className="w-full accent-primary-600"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-600 dark:text-gray-400">IOU: {config.iou_threshold}</label>
                  <input
                    type="range"
                    min="0.1"
                    max="0.9"
                    step="0.05"
                    value={config.iou_threshold}
                    onChange={(e) => setConfig({ ...config, iou_threshold: parseFloat(e.target.value) })}
                    className="w-full accent-primary-600"
                  />
                </div>
                {/* 검출 실행 버튼 */}
                <button
                  onClick={() => onRunDetection(config)}
                  disabled={isLoading || !currentSession}
                  className="w-full mt-3 flex items-center justify-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>검출 중...</span>
                    </>
                  ) : (
                    <>
                      <Settings className="w-4 h-4" />
                      <span>심볼 검출</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {/* 통합 분석 옵션 토글 */}
            <button
              onClick={() => setShowAnalysisOptions(!showAnalysisOptions)}
              className="w-full mt-2 flex items-center justify-between px-3 py-2 bg-purple-50 dark:bg-purple-900/30 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/50 border border-purple-200 dark:border-purple-800"
            >
              <span className="flex items-center space-x-2 text-purple-700 dark:text-purple-300">
                <Ruler className="w-4 h-4" />
                <span className="text-sm">분석 옵션</span>
              </span>
              {showAnalysisOptions ? <ChevronDown className="w-4 h-4 text-purple-600" /> : <ChevronRight className="w-4 h-4 text-purple-600" />}
            </button>
            {showAnalysisOptions && currentSession && (
              <div className="mt-2">
                <AnalysisOptions
                  sessionId={currentSession.session_id}
                  onOptionsChange={onAnalysisOptionsChange}
                  onRunAnalysis={onRunAnalysis}
                  compact={true}
                />
              </div>
            )}
          </div>

          {/* Cache */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => onClearCache('memory')}
                disabled={isClearingCache}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 rounded-lg hover:bg-gray-100 text-xs disabled:opacity-50"
              >
                {isClearingCache ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                <span>메모리</span>
              </button>
              <button
                onClick={() => onClearCache('all')}
                disabled={isClearingCache}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-300 rounded-lg hover:bg-red-100 text-xs disabled:opacity-50"
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
