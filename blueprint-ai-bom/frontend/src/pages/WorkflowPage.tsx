/**
 * Workflow Page - Streamlit 스타일 단일 페이지 레이아웃
 * 모든 섹션을 한 페이지에 표시
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  FileSpreadsheet,
  Settings,
  Loader2,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  Download,
  Trash2,
  Check,
  X,
  AlertCircle,
  Moon,
  Sun,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import axios from 'axios';
import { detectionApi, systemApi, groundTruthApi, blueprintFlowApi } from '../lib/api';
import type { GPUStatus, GTCompareResponse } from '../lib/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5020';

interface ClassExample {
  class_name: string;
  image_base64: string;
}
import type { VerificationStatus, DetectionConfig, ExportFormat } from '../types';
import { ReferencePanel } from '../components/ReferencePanel';
import { DrawingCanvas } from '../components/DrawingCanvas';

// 페이지당 아이템 수
const ITEMS_PER_PAGE = 7;

export function WorkflowPage() {
  // URL Parameters
  const [searchParams] = useSearchParams();
  const urlSessionId = searchParams.get('session');

  // Store
  const {
    currentSession,
    sessions,
    detections,
    imageData,
    imageSize,
    bomData,
    isLoading,
    error,
    loadSessions,
    loadSession,
    deleteSession,
    runDetection,
    verifyDetection,
    deleteDetection,
    approveAll,
    rejectAll,
    generateBOM,
    clearError,
    reset,
  } = useSessionStore();

  // Local state
  const [showSettings, setShowSettings] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('excel');
  const [availableClasses, setAvailableClasses] = useState<string[]>([]);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('darkMode') === 'true' ||
             window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [gpuStatus, setGpuStatus] = useState<GPUStatus | null>(null);
  const [config, setConfig] = useState<DetectionConfig>({
    confidence: 0.4,  // Streamlit과 동일 (nodeDefinitions 기준)
    iou_threshold: 0.5,  // Streamlit과 동일
    model_id: 'yolo',
  });

  // Class examples for reference images
  const [classExamples, setClassExamples] = useState<ClassExample[]>([]);

  // GT comparison
  const [gtCompareResult, setGtCompareResult] = useState<GTCompareResponse | null>(null);
  const [isLoadingGT, setIsLoadingGT] = useState(false);
  const [showGTImages, setShowGTImages] = useState(true);
  const [showRefImages, setShowRefImages] = useState(true);

  // Manual label
  const [showManualLabel, setShowManualLabel] = useState(false);
  const [manualLabel, setManualLabel] = useState({ class_name: '' });

  // Edit mode for detections
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingClassName, setEditingClassName] = useState<string>('');

  // Cache clearing
  const [isClearingCache, setIsClearingCache] = useState(false);

  // Fetch YOLO defaults from BlueprintFlow API
  useEffect(() => {
    const fetchYOLODefaults = async () => {
      const defaults = await blueprintFlowApi.getYOLODefaults();
      setConfig(prev => ({
        ...prev,
        confidence: defaults.confidence,
        iou_threshold: defaults.iou,
      }));
      console.log('📊 BlueprintFlow YOLO defaults loaded:', defaults);
    };
    fetchYOLODefaults();
  }, []);

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  // Load initial data
  useEffect(() => {
    loadSessions();
    loadClasses();
    loadClassExamples();
    loadSystemStatus();
    const interval = setInterval(loadSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load session from URL parameter
  useEffect(() => {
    if (urlSessionId && (!currentSession || currentSession.session_id !== urlSessionId)) {
      loadSession(urlSessionId);
    }
  }, [urlSessionId, currentSession, loadSession]);

  // Auto-load GT when detections are available
  useEffect(() => {
    const autoLoadGT = async () => {
      if (!currentSession || !imageSize || detections.length === 0) return;
      if (gtCompareResult) return;
      if (isLoadingGT) return;

      setIsLoadingGT(true);
      try {
        const detectionsForCompare = detections.map(d => ({
          class_name: d.class_name,
          bbox: d.bbox,
        }));
        // class_agnostic 모드로 GT 비교 (클래스 무관하게 위치만으로 매칭)
        // 이렇게 하면 모델 클래스와 GT 클래스가 달라도 위치 기반으로 매칭 가능
        const result = await groundTruthApi.compare(
          currentSession.filename,
          detectionsForCompare,
          imageSize.width,
          imageSize.height,
          0.3,  // IoU threshold
          { classAgnostic: true }  // 위치 기반 매칭 활성화
        );
        if (result.has_ground_truth) {
          setGtCompareResult(result);
        }
      } catch {
        // GT not available
      } finally {
        setIsLoadingGT(false);
      }
    };
    autoLoadGT();
  }, [currentSession?.session_id, imageSize, detections.length]);

  // Load functions
  const loadClasses = async () => {
    try {
      const { classes } = await detectionApi.getClasses();
      setAvailableClasses(classes);
    } catch (err) {
      console.error('Failed to load classes:', err);
    }
  };

  const loadClassExamples = async () => {
    try {
      const { data } = await axios.get<{ examples: ClassExample[] }>(
        `${API_BASE_URL}/api/config/class-examples`
      );
      setClassExamples(data.examples || []);
    } catch (err) {
      console.error('Failed to load class examples:', err);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const gpu = await systemApi.getGPUStatus();
      setGpuStatus(gpu);
    } catch (err) {
      console.error('Failed to load system status:', err);
    }
  };

  // Handlers
  const handleVerify = async (detectionId: string, status: VerificationStatus) => {
    if (!currentSession) return;
    try {
      await verifyDetection(detectionId, status);
    } catch (err) {
      console.error('Verification failed:', err);
    }
  };

  const handleGenerateBOM = async () => {
    if (!currentSession) return;
    try {
      await generateBOM();
    } catch (err) {
      console.error('BOM generation failed:', err);
    }
  };

  const handleClearCache = async (cacheType: 'all' | 'memory') => {
    setIsClearingCache(true);
    try {
      await systemApi.clearCache(cacheType);
    } catch (err) {
      console.error('Cache clear failed:', err);
    } finally {
      setIsClearingCache(false);
    }
  };

  const handleNewSession = () => {
    reset();
    setGtCompareResult(null);
    setCurrentPage(1);
  };

  // Stats
  const stats = useMemo(() => {
    const total = detections.length;
    const approved = detections.filter(d => d.verification_status === 'approved').length;
    const rejected = detections.filter(d => d.verification_status === 'rejected').length;
    const pending = detections.filter(d => d.verification_status === 'pending').length;
    const manual = detections.filter(d => d.verification_status === 'manual').length;
    return { total, approved, rejected, pending, manual };
  }, [detections]);

  // Pagination
  const totalPages = Math.ceil(detections.length / ITEMS_PER_PAGE);
  const paginatedDetections = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return detections.slice(start, start + ITEMS_PER_PAGE);
  }, [detections, currentPage]);

  // Get GT bbox for detection
  const getGtBboxForDetection = useCallback((detectionIndex: number) => {
    if (!gtCompareResult) return null;
    const match = gtCompareResult.tp_matches.find(m => m.detection_idx === detectionIndex);
    return match?.gt_bbox || null;
  }, [gtCompareResult]);

  // Render sidebar
  const renderSidebar = () => (
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
                  onClick={handleNewSession}
                  className="text-xs text-red-600 hover:text-red-700"
                >
                  새 세션
                </button>
              )}
            </div>
            {currentSession ? (
              <div className="text-sm">
                <p className="font-medium text-gray-900 dark:text-white truncate">{currentSession.filename}</p>
                <p className="text-xs text-gray-500">{detections.length}개 검출</p>
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
                    className={`group relative p-2 rounded-lg text-sm cursor-pointer transition-colors ${
                      currentSession?.session_id === session.session_id
                        ? 'bg-primary-50 dark:bg-primary-900/30 border border-primary-200'
                        : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100'
                    }`}
                    onClick={() => {
                      loadSession(session.session_id);
                      setGtCompareResult(null);
                    }}
                  >
                    <p className="font-medium truncate text-gray-900 dark:text-white">{session.filename}</p>
                    <p className="text-xs text-gray-500">{session.detection_count}개 검출</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('세션을 삭제하시겠습니까?')) {
                          deleteSession(session.session_id);
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
          </div>

          {/* Settings */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              <span className="flex items-center space-x-2 text-gray-700 dark:text-gray-300">
                <Settings className="w-4 h-4" />
                <span className="text-sm">검출 설정</span>
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
                  onClick={() => runDetection(config)}
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
                      <span>검출 실행</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Cache */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleClearCache('memory')}
                disabled={isClearingCache}
                className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 rounded-lg hover:bg-gray-100 text-xs disabled:opacity-50"
              >
                {isClearingCache ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                <span>메모리</span>
              </button>
              <button
                onClick={() => handleClearCache('all')}
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

  // Detection row component (Streamlit style - one per line)
  const DetectionRow = ({ detection, index }: { detection: typeof detections[0]; index: number }) => {
    const globalIndex = (currentPage - 1) * ITEMS_PER_PAGE + index;
    const gtBbox = getGtBboxForDetection(globalIndex);
    const match = gtCompareResult?.tp_matches.find(m => m.detection_idx === globalIndex);

    // Status colors
    const statusColors = {
      approved: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
      rejected: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
      pending: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
      manual: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800',
      modified: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
    };

    // Crop image from bbox
    const cropImage = (bbox: { x1: number; y1: number; x2: number; y2: number }) => {
      if (!imageData || !imageSize) return null;

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return null;

      const img = new Image();
      img.src = imageData;

      const width = bbox.x2 - bbox.x1;
      const height = bbox.y2 - bbox.y1;
      canvas.width = width;
      canvas.height = height;

      return new Promise<string>((resolve) => {
        img.onload = () => {
          ctx.drawImage(img, bbox.x1, bbox.y1, width, height, 0, 0, width, height);
          resolve(canvas.toDataURL());
        };
        if (img.complete) {
          ctx.drawImage(img, bbox.x1, bbox.y1, width, height, 0, 0, width, height);
          resolve(canvas.toDataURL());
        }
      });
    };

    const [croppedSrc, setCroppedSrc] = useState<string | null>(null);
    const [gtCroppedSrc, setGtCroppedSrc] = useState<string | null>(null);

    useEffect(() => {
      if (imageData && imageSize) {
        cropImage(detection.bbox)?.then(src => src && setCroppedSrc(src));
        if (gtBbox) {
          cropImage(gtBbox)?.then(src => src && setGtCroppedSrc(src));
        }
      }
    }, [imageData, imageSize, detection.bbox, gtBbox]);

    return (
      <div className={`p-4 rounded-lg border ${statusColors[detection.verification_status]} mb-3`}>
        <div className="flex items-start gap-4">
          {/* Index */}
          <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-200 dark:bg-gray-700 rounded-full text-sm font-bold">
            {globalIndex + 1}
          </div>

          {/* Images (GT, Detection, Reference) */}
          <div className="flex gap-2 flex-shrink-0">
            {/* GT Image */}
            {showGTImages && (
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">🏷️ GT</p>
                <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded border flex items-center justify-center overflow-hidden">
                  {gtCroppedSrc ? (
                    <img src={gtCroppedSrc} alt="GT" className="max-w-full max-h-full object-contain" />
                  ) : (
                    <span className="text-xs text-gray-400">없음</span>
                  )}
                </div>
              </div>
            )}

            {/* Detection Image */}
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-1">🔍 검출</p>
              <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded border flex items-center justify-center overflow-hidden">
                {croppedSrc ? (
                  <img src={croppedSrc} alt="Detection" className="max-w-full max-h-full object-contain" />
                ) : (
                  <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                )}
              </div>
            </div>

            {/* Reference Image */}
            {showRefImages && (() => {
              const refExample = classExamples.find(ex => detection.class_name.includes(ex.class_name));
              return (
                <div className="text-center">
                  <p className="text-xs text-gray-500 mb-1">📚 참조</p>
                  <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded border flex items-center justify-center overflow-hidden">
                    {refExample?.image_base64 ? (
                      <img
                        src={`data:image/jpeg;base64,${refExample.image_base64}`}
                        alt="Reference"
                        className="max-w-full max-h-full object-contain"
                      />
                    ) : (
                      <span className="text-xs text-gray-400">없음</span>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {editingId === detection.id ? (
                // Edit mode: show class dropdown
                <select
                  value={editingClassName}
                  onChange={(e) => setEditingClassName(e.target.value)}
                  className="px-2 py-1 text-sm border border-orange-300 dark:border-orange-600 rounded bg-white dark:bg-gray-800 focus:ring-2 focus:ring-orange-500"
                  autoFocus
                >
                  {availableClasses.map(cls => (
                    <option key={cls} value={cls}>{cls}</option>
                  ))}
                </select>
              ) : (
                <span className="font-semibold text-gray-900 dark:text-white">
                  {detection.modified_class_name || detection.class_name}
                  {detection.modified_class_name && detection.modified_class_name !== detection.class_name && (
                    <span className="ml-1 text-xs text-orange-500">(수정됨)</span>
                  )}
                </span>
              )}
              <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded">
                {(detection.confidence * 100).toFixed(1)}%
              </span>
              {match && (
                <span className={`text-xs px-2 py-0.5 rounded ${match.class_match ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  IoU: {(match.iou * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500">
              위치: ({detection.bbox.x1}, {detection.bbox.y1}) - ({detection.bbox.x2}, {detection.bbox.y2})
            </p>
            {match && !match.class_match && (
              <p className="text-xs text-yellow-600 mt-1">
                GT 클래스: {match.gt_class}
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {editingId === detection.id ? (
              // Edit mode actions
              <>
                <button
                  onClick={() => {
                    // Save edited class name
                    if (editingClassName && editingClassName !== detection.class_name) {
                      verifyDetection(detection.id, 'approved', editingClassName);
                    }
                    setEditingId(null);
                    setEditingClassName('');
                  }}
                  className="px-3 py-1.5 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm flex items-center gap-1"
                  title="수정 완료"
                >
                  <Check className="w-3 h-3" />
                  <span>완료</span>
                </button>
                <button
                  onClick={() => {
                    setEditingId(null);
                    setEditingClassName('');
                  }}
                  className="px-3 py-1.5 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 text-sm"
                  title="취소"
                >
                  취소
                </button>
              </>
            ) : (
              // Normal actions
              <>
                <button
                  onClick={() => handleVerify(detection.id, 'approved')}
                  disabled={editingId !== null}
                  className={`p-2 rounded-lg transition-colors ${
                    detection.verification_status === 'approved'
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-green-100 hover:text-green-600'
                  } disabled:opacity-50`}
                  title="승인"
                >
                  <Check className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleVerify(detection.id, 'rejected')}
                  disabled={editingId !== null}
                  className={`p-2 rounded-lg transition-colors ${
                    detection.verification_status === 'rejected'
                      ? 'bg-red-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-red-100 hover:text-red-600'
                  } disabled:opacity-50`}
                  title="거부"
                >
                  <X className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setEditingId(detection.id);
                    setEditingClassName(detection.modified_class_name || detection.class_name);
                  }}
                  disabled={editingId !== null}
                  className={`p-2 rounded-lg transition-colors ${
                    detection.verification_status === 'modified'
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-orange-100 hover:text-orange-600'
                  } disabled:opacity-50`}
                  title="수정"
                >
                  <span className="text-sm">✏️</span>
                </button>
                {/* 삭제 버튼 - 수작업 라벨만 삭제 가능 */}
                {detection.verification_status === 'manual' && (
                  <button
                    onClick={() => {
                      if (confirm('이 수작업 라벨을 삭제하시겠습니까?')) {
                        deleteDetection(detection.id);
                      }
                    }}
                    disabled={editingId !== null}
                    className="p-2 rounded-lg transition-colors bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-red-100 hover:text-red-600 disabled:opacity-50"
                    title="삭제"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {renderSidebar()}

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5" />
                <span>{error}</span>
              </div>
              <button onClick={clearError} className="text-red-500 hover:text-red-700">×</button>
            </div>
          )}

          {/* Title */}
          <div className="text-center mb-2">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🎯 AI 기반 BOM 추출 결과</h1>
            {currentSession && (
              <p className="text-sm text-gray-500 mt-1">📄 {currentSession.filename}</p>
            )}
          </div>

          {/* 참조 도면 */}
          {imageData && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3">📐 참조 도면</h2>
              <div className="flex gap-4">
                <div className="flex-1">
                  <img
                    src={imageData}
                    alt="도면"
                    className="w-full max-h-[400px] object-contain rounded-lg border border-gray-200 dark:border-gray-700"
                  />
                </div>
                {imageSize && (
                  <div className="w-48 space-y-2 text-sm">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
                      <span className="text-gray-500">크기:</span>
                      <span className="ml-2 font-medium">{imageSize.width} × {imageSize.height}</span>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
                      <span className="text-gray-500">검출:</span>
                      <span className="ml-2 font-medium">{detections.length}개</span>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
                      <span className="text-gray-500">승인:</span>
                      <span className="ml-2 font-medium text-green-600">{stats.approved}개</span>
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Section 1: AI 검출 결과 */}
          {detections.length > 0 && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              {/* Title with inline metrics (Streamlit style) */}
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                🔍 AI 검출 결과
                {gtCompareResult && (
                  <span className="text-base font-normal ml-2">
                    📊 파나시아 YOLOv11N - {stats.total}개 검출
                    (F1: {gtCompareResult.metrics.f1_score.toFixed(1)}%,
                    정밀도: {gtCompareResult.metrics.precision.toFixed(1)}%,
                    재현율: {gtCompareResult.metrics.recall.toFixed(1)}%)
                  </span>
                )}
              </h2>

              {/* GT 로드 상태 (Streamlit style) */}
              {gtCompareResult && (
                <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-3 mb-4">
                  <p className="text-green-800 dark:text-green-200">
                    ✅ Ground Truth 로드됨: {gtCompareResult.gt_count}개 라벨
                  </p>
                </div>
              )}

              {/* GT vs Prediction Side by Side (Streamlit style) */}
              {imageData && imageSize && gtCompareResult && (
                <div className="grid grid-cols-2 gap-4 mb-4">
                  {/* Left: Ground Truth (Green boxes) */}
                  <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <canvas
                      ref={(canvas) => {
                        if (!canvas || !imageData || !imageSize) return;
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return;

                        const img = new Image();
                        img.onload = () => {
                          // Scale to fit
                          const scale = Math.min(canvas.parentElement!.clientWidth / img.width, 400 / img.height);
                          canvas.width = img.width * scale;
                          canvas.height = img.height * scale;
                          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                          // Collect all GT boxes from tp_matches and fn_labels
                          const allGtBoxes: Array<{ bbox: { x1: number; y1: number; x2: number; y2: number }; class_name: string }> = [];

                          // GT boxes from matched detections
                          gtCompareResult.tp_matches.forEach(match => {
                            allGtBoxes.push({ bbox: match.gt_bbox, class_name: match.gt_class });
                          });

                          // GT boxes from unmatched (FN) labels
                          gtCompareResult.fn_labels.forEach(label => {
                            allGtBoxes.push({ bbox: label.bbox, class_name: label.class_name });
                          });

                          // Draw GT boxes (GREEN, thick)
                          ctx.strokeStyle = '#22c55e';
                          ctx.lineWidth = 3;
                          ctx.font = 'bold 12px sans-serif';
                          allGtBoxes.forEach((gt, idx) => {
                            const x1 = gt.bbox.x1 * scale;
                            const y1 = gt.bbox.y1 * scale;
                            const w = (gt.bbox.x2 - gt.bbox.x1) * scale;
                            const h = (gt.bbox.y2 - gt.bbox.y1) * scale;
                            ctx.strokeRect(x1, y1, w, h);
                            // Label
                            ctx.fillStyle = '#22c55e';
                            ctx.fillRect(x1, y1 - 16, 30, 16);
                            ctx.fillStyle = '#fff';
                            ctx.fillText(`GT${idx + 1}`, x1 + 2, y1 - 4);
                          });
                        };
                        img.src = imageData;
                      }}
                      className="w-full"
                    />
                    <p className="text-center py-2 text-sm font-medium text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/30">
                      🟢 Ground Truth ({gtCompareResult.gt_count}개)
                    </p>
                  </div>

                  {/* Right: Predictions (RED boxes) */}
                  <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <canvas
                      ref={(canvas) => {
                        if (!canvas || !imageData || !imageSize) return;
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return;

                        const img = new Image();
                        img.onload = () => {
                          // Scale to fit
                          const scale = Math.min(canvas.parentElement!.clientWidth / img.width, 400 / img.height);
                          canvas.width = img.width * scale;
                          canvas.height = img.height * scale;
                          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                          // Draw Detection boxes (RED, thick)
                          ctx.strokeStyle = '#ef4444';
                          ctx.lineWidth = 3;
                          ctx.font = 'bold 12px sans-serif';
                          detections.forEach((det, idx) => {
                            const x1 = det.bbox.x1 * scale;
                            const y1 = det.bbox.y1 * scale;
                            const w = (det.bbox.x2 - det.bbox.x1) * scale;
                            const h = (det.bbox.y2 - det.bbox.y1) * scale;
                            ctx.strokeRect(x1, y1, w, h);
                            // Label
                            ctx.fillStyle = '#ef4444';
                            ctx.fillRect(x1, y1 - 16, 20, 16);
                            ctx.fillStyle = '#fff';
                            ctx.fillText(`${idx + 1}`, x1 + 4, y1 - 4);
                          });
                        };
                        img.src = imageData;
                      }}
                      className="w-full"
                    />
                    <p className="text-center py-2 text-sm font-medium text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/30">
                      🔴 검출 결과 ({detections.length}개)
                    </p>
                  </div>
                </div>
              )}

              {/* Stats Grid */}
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
                  <p className="text-sm text-gray-500">총 검출 수</p>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {detections.length > 0 ? (detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length).toFixed(3) : '0.000'}
                  </p>
                  <p className="text-sm text-gray-500">평균 신뢰도</p>
                </div>
                {gtCompareResult ? (
                  <>
                    <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-600">{gtCompareResult.metrics.precision.toFixed(1)}%</p>
                      <p className="text-sm text-gray-500">Precision</p>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-purple-600">{gtCompareResult.metrics.recall.toFixed(1)}%</p>
                      <p className="text-sm text-gray-500">Recall</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
                      <p className="text-sm text-gray-500">승인</p>
                    </div>
                    <div className="bg-yellow-50 dark:bg-yellow-900/30 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
                      <p className="text-sm text-gray-500">대기</p>
                    </div>
                  </>
                )}
              </div>

              {/* F1 Score highlight (Streamlit style) */}
              {gtCompareResult && (
                <div className="bg-green-100 dark:bg-green-900/50 border border-green-300 dark:border-green-700 rounded-lg p-3">
                  <p className="text-green-800 dark:text-green-200 font-medium">
                    🎯 F1 Score: {gtCompareResult.metrics.f1_score.toFixed(1)}%
                    (TP:{gtCompareResult.metrics.tp}, FP:{gtCompareResult.metrics.fp}, FN:{gtCompareResult.metrics.fn})
                  </p>
                </div>
              )}
            </section>
          )}

          {/* Section 4: 심볼 검증 및 수정 */}
          {detections.length > 0 && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">✅ 심볼 검증 및 수정</h2>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => approveAll()}
                    disabled={isLoading}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>처리 중...</span>
                      </>
                    ) : (
                      <span>전체 승인</span>
                    )}
                  </button>
                  <button
                    onClick={() => rejectAll()}
                    disabled={isLoading}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>처리 중...</span>
                      </>
                    ) : (
                      <span>전체 거부</span>
                    )}
                  </button>
                </div>
              </div>

              {/* Options */}
              <div className="flex items-center space-x-6 mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showGTImages}
                    onChange={(e) => setShowGTImages(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">🏷️ GT 이미지 표시</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showRefImages}
                    onChange={(e) => setShowRefImages(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">📚 참조 이미지 표시</span>
                </label>
                <button
                  onClick={() => setShowManualLabel(!showManualLabel)}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  ✏️ 수작업 라벨 추가
                </button>
              </div>

              {/* Manual Label Section */}
              {showManualLabel && imageData && imageSize && (
                <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <h3 className="font-semibold mb-3">✏️ 수작업 라벨 추가</h3>
                  <div className="mb-4">
                    <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">1. 클래스 선택</label>
                    <select
                      value={manualLabel.class_name}
                      onChange={(e) => setManualLabel({ class_name: e.target.value })}
                      className="w-full max-w-xs px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                    >
                      <option value="">클래스 선택...</option>
                      {availableClasses.map(cls => (
                        <option key={cls} value={cls}>{cls}</option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-4">
                    <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">2. 바운딩 박스 그리기</label>
                    <DrawingCanvas
                      imageData={imageData}
                      imageSize={imageSize}
                      selectedClass={manualLabel.class_name}
                      maxWidth="100%"
                      existingBoxes={
                        // 승인/수정/수작업 라벨만 표시 (pending, rejected 제외)
                        detections
                          .filter(d =>
                            d.verification_status === 'approved' ||
                            d.verification_status === 'modified' ||
                            d.verification_status === 'manual'
                          )
                          .map(d => ({
                            bbox: d.bbox,
                            label: d.modified_class_name || d.class_name,
                            color: d.verification_status === 'manual' ? '#a855f7' :
                                   d.verification_status === 'modified' ? '#f97316' : '#22c55e'
                          }))
                      }
                      onBoxDrawn={(box) => {
                        if (manualLabel.class_name && currentSession) {
                          detectionApi.addManual(currentSession.session_id, {
                            class_name: manualLabel.class_name,
                            bbox: box,
                          }).then(() => {
                            loadSession(currentSession.session_id);
                          });
                        }
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Pagination */}
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-gray-500">
                  📄 {currentPage} / {totalPages} 페이지 (전체 {detections.length}개 중 {(currentPage - 1) * ITEMS_PER_PAGE + 1}-{Math.min(currentPage * ITEMS_PER_PAGE, detections.length)}번째)
                </p>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
                  >
                    ⏮️ 처음
                  </button>
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
                  >
                    ◀️ 이전
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-1 text-sm rounded ${
                        page === currentPage
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
                  >
                    다음 ▶️
                  </button>
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
                  >
                    마지막 ⏭️
                  </button>
                </div>
              </div>

              {/* Detection List (one per line) */}
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900 dark:text-white">🔍 검출 결과</h3>
                {paginatedDetections.map((detection, index) => (
                  <DetectionRow key={detection.id} detection={detection} index={index} />
                ))}
              </div>
            </section>
          )}

          {/* Section 5: 최종 검증 결과 이미지 */}
          {imageData && imageSize && (stats.approved > 0 || stats.rejected > 0) && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">🖼️ 최종 검증 결과 이미지</h2>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center border border-green-200 dark:border-green-800">
                  <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
                  <p className="text-sm text-gray-500">✅ 승인됨</p>
                </div>
                <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 text-center border border-orange-200 dark:border-orange-800">
                  <p className="text-2xl font-bold text-orange-600">
                    {detections.filter(d => d.modified_class_name && d.modified_class_name !== d.class_name).length}
                  </p>
                  <p className="text-sm text-gray-500">✏️ 수정됨</p>
                </div>
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center border border-purple-200 dark:border-purple-800">
                  <p className="text-2xl font-bold text-purple-600">
                    {detections.filter(d => d.verification_status === 'manual').length}
                  </p>
                  <p className="text-sm text-gray-500">🎨 수작업</p>
                </div>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-4 mb-4 text-sm">
                <span className="flex items-center gap-1">
                  <span className="w-4 h-4 bg-green-500 rounded"></span> 승인
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-4 h-4 bg-orange-500 rounded"></span> 수정
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-4 h-4 bg-purple-500 rounded"></span> 수작업
                </span>
              </div>

              {/* Final Image with Bounding Boxes */}
              <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700">
                <canvas
                  ref={(canvas) => {
                    if (!canvas || !imageData || !imageSize) return;
                    const ctx = canvas.getContext('2d');
                    if (!ctx) return;

                    const img = new Image();
                    img.onload = () => {
                      // Scale to fit container (max 800px width)
                      const maxWidth = 800;
                      const scale = Math.min(1, maxWidth / imageSize.width);
                      canvas.width = imageSize.width * scale;
                      canvas.height = imageSize.height * scale;

                      // Draw image
                      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                      // Draw bounding boxes for approved/modified/manual detections
                      const finalDetections = detections.filter(d =>
                        d.verification_status === 'approved' ||
                        d.verification_status === 'modified' ||
                        d.verification_status === 'manual'
                      );

                      finalDetections.forEach((detection, idx) => {
                        const { x1, y1, x2, y2 } = detection.bbox;
                        const sx1 = x1 * scale;
                        const sy1 = y1 * scale;
                        const sx2 = x2 * scale;
                        const sy2 = y2 * scale;

                        // Color based on status
                        let color = '#22c55e'; // green - approved
                        if (detection.modified_class_name && detection.modified_class_name !== detection.class_name) {
                          color = '#f97316'; // orange - modified
                        } else if (detection.verification_status === 'manual') {
                          color = '#a855f7'; // purple - manual
                        }

                        // Draw rectangle
                        ctx.strokeStyle = color;
                        ctx.lineWidth = 2;
                        ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

                        // Draw label background
                        const label = `${idx + 1}`;
                        ctx.font = 'bold 12px sans-serif';
                        const textWidth = ctx.measureText(label).width;
                        ctx.fillStyle = color;
                        ctx.fillRect(sx1, sy1 - 18, textWidth + 8, 18);

                        // Draw label text
                        ctx.fillStyle = 'white';
                        ctx.fillText(label, sx1 + 4, sy1 - 5);
                      });
                    };
                    img.src = imageData;
                  }}
                  className="max-w-full"
                />
                <p className="text-center text-sm text-gray-500 mt-2 pb-2">
                  최종 선정된 부품: 총 {detections.filter(d =>
                    d.verification_status === 'approved' ||
                    d.verification_status === 'modified' ||
                    d.verification_status === 'manual'
                  ).length}개
                </p>
              </div>
            </section>
          )}

          {/* Section 6: BOM 생성 */}
          {detections.length > 0 && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">📊 BOM 생성 및 내보내기</h2>
                <div className="flex items-center space-x-3">
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <option value="excel">Excel (.xlsx)</option>
                    <option value="csv">CSV</option>
                    <option value="json">JSON</option>
                  </select>
                  <button
                    onClick={handleGenerateBOM}
                    disabled={isLoading || stats.approved === 0}
                    className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    <FileSpreadsheet className="w-5 h-5" />
                    <span>BOM 생성</span>
                  </button>
                </div>
              </div>

              {stats.approved === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FileSpreadsheet className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>승인된 검출 결과가 없습니다.</p>
                  <p className="text-sm">위에서 검출 결과를 승인하세요.</p>
                </div>
              ) : bomData ? (
                <div>
                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold">{bomData.items.length}</p>
                      <p className="text-sm text-gray-500">품목 수</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold">{bomData.summary.total_quantity}</p>
                      <p className="text-sm text-gray-500">총 수량</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold">{bomData.summary.total?.toLocaleString() || '-'}</p>
                      <p className="text-sm text-gray-500">예상 비용 (원)</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-600">✓</p>
                      <p className="text-sm text-gray-500">생성 완료</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th className="px-4 py-2 text-left">#</th>
                          <th className="px-4 py-2 text-left">품목명</th>
                          <th className="px-4 py-2 text-center">수량</th>
                          <th className="px-4 py-2 text-right">단가</th>
                          <th className="px-4 py-2 text-right">금액</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bomData.items.map((item, idx) => (
                          <tr key={idx} className="border-b border-gray-200 dark:border-gray-700">
                            <td className="px-4 py-2">{idx + 1}</td>
                            <td className="px-4 py-2 font-medium">{item.class_name}</td>
                            <td className="px-4 py-2 text-center">{item.quantity}</td>
                            <td className="px-4 py-2 text-right">{item.unit_price?.toLocaleString() || '-'}</td>
                            <td className="px-4 py-2 text-right">{item.total_price?.toLocaleString() || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-gray-50 dark:bg-gray-700 font-bold">
                        <tr>
                          <td colSpan={2} className="px-4 py-2">합계</td>
                          <td className="px-4 py-2 text-center">{bomData.summary.total_quantity}</td>
                          <td className="px-4 py-2"></td>
                          <td className="px-4 py-2 text-right">{bomData.summary.total?.toLocaleString() || '-'}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>

                  <div className="mt-4 flex justify-end">
                    <a
                      href={`http://localhost:5020/bom/${currentSession?.session_id}/download?format=${exportFormat}`}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      download
                    >
                      <Download className="w-4 h-4" />
                      <span>다운로드</span>
                    </a>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>BOM을 생성하려면 위의 "BOM 생성" 버튼을 클릭하세요.</p>
                </div>
              )}
            </section>
          )}

        </div>
      </main>

      {/* 📚 심볼 참조 패널 (오른쪽 고정) */}
      <ReferencePanel onClose={() => {}} />
    </div>
  );
}

export default WorkflowPage;
