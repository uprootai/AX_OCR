/**
 * Workflow Sidebar Component
 * 워크플로우 사이드바 - 세션 관리, 설정, 캐시 관리
 */

import React, { useRef, useState, useCallback } from 'react';
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
  Download,
  Upload,
  ImagePlus,
  Images,
  FileArchive,
} from 'lucide-react';
import { sessionApi } from '../../../lib/api';
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
  currentSession: { session_id: string; filename: string; features?: string[] } | null;
  sessions: Session[];
  detectionCount: number;
  // Image management (Phase 2C)
  sessionImageCount?: number;
  onImagesAdded?: () => void;
  // Handlers
  onNewSession: () => void;
  onLoadSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onRunDetection: (config: DetectionConfig) => void;
  onClearCache: (type: 'all' | 'memory') => void;
  onAnalysisOptionsChange?: (options: AnalysisOptionsData) => void;
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
  config,
  setConfig,
  showSettings,
  setShowSettings,
  showAnalysisOptions,
  setShowAnalysisOptions,
  currentSession,
  sessions,
  detectionCount,
  sessionImageCount = 0,
  onImagesAdded,
  onNewSession,
  onLoadSession,
  onDeleteSession,
  onRunDetection,
  onClearCache,
  onAnalysisOptionsChange,
  onRunAnalysis,
  onSessionImported,
  isLoading,
  isClearingCache,
}: WorkflowSidebarProps) {
  const importFileRef = useRef<HTMLInputElement>(null);
  const imageUploadRef = useRef<HTMLInputElement>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isUploadingImages, setIsUploadingImages] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // 이미지 업로드 핸들러 (일반 이미지 + ZIP 지원)
  const handleImageUpload = useCallback(async (files: FileList | File[]) => {
    if (!currentSession || files.length === 0) return;

    setIsUploadingImages(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:5020'}/sessions/${currentSession.session_id}/images/bulk-upload`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      console.log('Images uploaded:', result);
      onImagesAdded?.();
    } catch (error) {
      console.error('Image upload failed:', error);
      alert('이미지 업로드에 실패했습니다.');
    } finally {
      setIsUploadingImages(false);
      if (imageUploadRef.current) {
        imageUploadRef.current.value = '';
      }
    }
  }, [currentSession, onImagesAdded]);

  // 파일 선택 핸들러
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      handleImageUpload(files);
    }
  }, [handleImageUpload]);

  // 드래그 앤 드롭 핸들러
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleImageUpload(files);
    }
  }, [handleImageUpload]);

  const handleLoadSession = (sessionId: string) => {
    onLoadSession(sessionId);
  };

  // Export 핸들러
  const handleExportSession = async () => {
    if (!currentSession) return;
    setIsExporting(true);
    try {
      await sessionApi.exportJson(currentSession.session_id, true, true);
    } catch (error) {
      console.error('Export failed:', error);
      alert('세션 Export에 실패했습니다.');
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
      // Reset file input
      if (importFileRef.current) {
        importFileRef.current.value = '';
      }
    }
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

            {/* Export/Import 버튼 */}
            <div className="mt-3 grid grid-cols-2 gap-2">
              <button
                onClick={handleExportSession}
                disabled={!currentSession || isExporting}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isExporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                <span>Export</span>
              </button>
              <button
                onClick={() => importFileRef.current?.click()}
                disabled={isImporting}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isImporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
                <span>Import</span>
              </button>
              <input
                ref={importFileRef}
                type="file"
                accept=".json"
                onChange={handleImportSession}
                className="hidden"
              />
            </div>

            {/* 이미지 관리 섹션 (Phase 2C) */}
            {currentSession && (
              <div
                className={`mt-3 p-3 rounded-lg border-2 border-dashed transition-colors ${
                  isDragging
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="flex items-center space-x-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                    <Images className="w-4 h-4" />
                    <span>세션 이미지</span>
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full">
                    {sessionImageCount}장
                  </span>
                </div>

                <button
                  onClick={() => imageUploadRef.current?.click()}
                  disabled={isUploadingImages}
                  className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isUploadingImages ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>업로드 중...</span>
                    </>
                  ) : (
                    <>
                      <ImagePlus className="w-4 h-4" />
                      <span>이미지 추가</span>
                    </>
                  )}
                </button>

                <p className="mt-2 text-[10px] text-center text-gray-500 dark:text-gray-400">
                  <FileArchive className="w-3 h-3 inline mr-1" />
                  이미지 또는 ZIP 파일 드래그 앤 드롭
                </p>

                <input
                  ref={imageUploadRef}
                  type="file"
                  accept="image/*,.zip"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
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
                {currentSession?.features && currentSession.features.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 text-[10px] font-medium bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full border border-blue-200 dark:border-blue-700">
                    Builder 설정
                  </span>
                )}
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
