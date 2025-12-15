/**
 * Workflow Page - Streamlit-like 통합 워크플로우
 * 사이드바에서 전체 프로세스를 한눈에 관리
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Upload,
  Play,
  CheckCircle,
  FileSpreadsheet,
  Settings,
  Loader2,
  ChevronRight,
  ChevronDown,
  Image as ImageIcon,
  Download,
  Trash2,
  Check,
  X,
  ChevronLeft,
  AlertCircle,
  Moon,
  Sun,
  HelpCircle,
  Cpu,
  LayoutGrid,
  List,
  Info,
  RefreshCw,
  StopCircle,
} from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import { detectionApi, systemApi, testImagesApi, modelsApi, groundTruthApi } from '../lib/api';
import type { GPUStatus, SystemInfo, TestImage, AIModel, GTCompareResponse } from '../lib/api';
import type { VerificationStatus, DetectionConfig, ExportFormat } from '../types';
import { DetectionCard } from '../components/DetectionCard';
import { ReferencePanel } from '../components/ReferencePanel';
import { DrawingCanvas } from '../components/DrawingCanvas';
import { RotateCcw } from 'lucide-react';

// 페이지당 아이템 수
const ITEMS_PER_PAGE = 7;

// 워크플로우 단계
type WorkflowStep = 'upload' | 'detection' | 'verification' | 'bom';

export function WorkflowPage() {
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
    uploadImage,
    runDetection,
    cancelDetection,
    verifyDetection,
    approveAll,
    rejectAll,
    generateBOM,
    clearError,
    reset,
  } = useSessionStore();

  // Local state
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [dragActive, setDragActive] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showReferencePanel, setShowReferencePanel] = useState(false);
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
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid'); // 3컬럼 그리드 vs 리스트
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  const [gpuStatus, setGpuStatus] = useState<GPUStatus | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [isClearingCache, setIsClearingCache] = useState(false);

  // Upload mode (like Streamlit radio)
  const [uploadMode, setUploadMode] = useState<'upload' | 'test'>('upload');
  const [testImages, setTestImages] = useState<TestImage[]>([]);
  const [selectedTestImage, setSelectedTestImage] = useState<string>('');

  // Model selection (like Streamlit)
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>(['yolo_v11n']);
  const [enableOCR, setEnableOCR] = useState(false);

  // Manual labeling state
  const [manualLabel, setManualLabel] = useState({
    class_name: '',
    x1: 0,
    y1: 0,
    x2: 0,
    y2: 0,
  });

  // Ground Truth comparison state
  const [gtCompareResult, setGtCompareResult] = useState<GTCompareResponse | null>(null);
  const [isLoadingGT, setIsLoadingGT] = useState(false);
  const [showGTSection, setShowGTSection] = useState(true);

  // Detection config
  const [config, setConfig] = useState<Partial<DetectionConfig>>({
    confidence: 0.7,
    iou_threshold: 0.45,
    model_id: 'yolo_v11n',
  });

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('darkMode', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('darkMode', 'false');
    }
  }, [darkMode]);

  // Load sessions, classes, test images, and models on mount
  useEffect(() => {
    loadSessions();
    loadAvailableClasses();
    loadSystemStatus();
    loadTestImages();
    loadModels();
  }, [loadSessions]);

  // Load test images
  const loadTestImages = async () => {
    try {
      const result = await testImagesApi.list();
      setTestImages(result.images || []);
    } catch {
      console.error('Failed to load test images');
    }
  };

  // Load available models
  const loadModels = async () => {
    try {
      const result = await modelsApi.list();
      setAvailableModels(result.models || []);
    } catch {
      console.error('Failed to load models');
    }
  };

  // Handle test image selection
  const handleTestImageSelect = async (filename: string) => {
    if (!filename) return;
    setSelectedTestImage(filename);

    try {
      const result = await testImagesApi.load(filename);
      if (result.session_id) {
        await loadSession(result.session_id);
        loadSessions();
      }
    } catch (err) {
      console.error('Failed to load test image:', err);
    }
  };

  // Load GPU and system status periodically
  const loadSystemStatus = async () => {
    try {
      const [gpu, info] = await Promise.all([
        systemApi.getGPUStatus(),
        systemApi.getInfo(),
      ]);
      setGpuStatus(gpu);
      setSystemInfo(info);
    } catch {
      console.error('Failed to load system status');
    }
  };

  // Refresh GPU status every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      systemApi.getGPUStatus().then(setGpuStatus).catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  // Load available classes for dropdown
  const loadAvailableClasses = async () => {
    try {
      const result = await detectionApi.getClasses();
      setAvailableClasses(result.classes || []);
    } catch {
      console.error('Failed to load classes');
    }
  };

  // Clear cache handler
  const handleClearCache = async (cacheType: 'all' | 'uploads' | 'memory') => {
    setIsClearingCache(true);
    try {
      const result = await systemApi.clearCache(cacheType);
      alert(result.message);
      loadSystemStatus();
    } catch {
      alert('캐시 정리 실패');
    } finally {
      setIsClearingCache(false);
    }
  };

  // Auto-advance workflow step based on session state
  useEffect(() => {
    if (!currentSession) {
      setCurrentStep('upload');
      return;
    }

    if (bomData) {
      setCurrentStep('bom');
    } else if (detections.length > 0) {
      setCurrentStep('verification');
    } else if (currentSession.status === 'uploaded') {
      setCurrentStep('detection');
    }
  }, [currentSession, detections, bomData]);

  // Reset pagination when detections change
  useEffect(() => {
    setCurrentPage(1);
  }, [detections.length]);

  // Stats
  const stats = useMemo(() => {
    const pending = detections.filter(d => d.verification_status === 'pending').length;
    const approved = detections.filter(d => ['approved', 'modified', 'manual'].includes(d.verification_status)).length;
    const rejected = detections.filter(d => d.verification_status === 'rejected').length;
    return { total: detections.length, pending, approved, rejected };
  }, [detections]);

  // Extended stats (Streamlit-like) - 중복 검출 및 신뢰도 분포
  const extendedStats = useMemo(() => {
    // 클래스별 카운트
    const classCounts: Record<string, number> = {};
    detections.forEach(d => {
      classCounts[d.class_name] = (classCounts[d.class_name] || 0) + 1;
    });

    // 중복 검출 (같은 클래스가 2개 이상)
    const duplicateClasses = Object.entries(classCounts).filter(([_, count]) => count > 1);
    const totalDuplicates = duplicateClasses.reduce((sum, [_, count]) => sum + count - 1, 0);

    // 신뢰도 분포
    const highConfidence = detections.filter(d => d.confidence >= 0.9).length;
    const mediumConfidence = detections.filter(d => d.confidence >= 0.7 && d.confidence < 0.9).length;
    const lowConfidence = detections.filter(d => d.confidence < 0.7).length;

    // 평균 신뢰도
    const avgConfidence = detections.length > 0
      ? detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length
      : 0;

    // 고유 클래스 수
    const uniqueClasses = Object.keys(classCounts).length;

    return {
      classCounts,
      duplicateClasses,
      totalDuplicates,
      highConfidence,
      mediumConfidence,
      lowConfidence,
      avgConfidence,
      uniqueClasses,
    };
  }, [detections]);

  // 승인된 심볼 목록 (Streamlit-like)
  const approvedSymbols = useMemo(() => {
    return detections
      .filter(d => ['approved', 'modified', 'manual'].includes(d.verification_status))
      .reduce((acc: Record<string, { count: number; avgConf: number; totalConf: number }>, d) => {
        if (!acc[d.class_name]) {
          acc[d.class_name] = { count: 0, avgConf: 0, totalConf: 0 };
        }
        acc[d.class_name].count += 1;
        acc[d.class_name].totalConf += d.confidence;
        acc[d.class_name].avgConf = acc[d.class_name].totalConf / acc[d.class_name].count;
        return acc;
      }, {});
  }, [detections]);

  // Ground Truth 비교 함수
  const handleCompareGT = async () => {
    if (!currentSession || !imageSize) return;
    setIsLoadingGT(true);
    try {
      const detectionsForCompare = detections.map(d => ({
        class_name: d.class_name,
        bbox: d.bbox,
      }));
      const result = await groundTruthApi.compare(
        currentSession.filename,
        detectionsForCompare,
        imageSize.width,
        imageSize.height,
        0.5 // IoU threshold
      );
      setGtCompareResult(result);
    } catch (err) {
      console.error('GT comparison failed:', err);
      setGtCompareResult(null);
    } finally {
      setIsLoadingGT(false);
    }
  };

  // Handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files?.[0]) {
      try {
        await uploadImage(files[0]);
        setCurrentStep('detection');
      } catch {
        // Error handled in store
      }
    }
  }, [uploadImage]);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files?.[0]) {
      try {
        await uploadImage(files[0]);
        setCurrentStep('detection');
      } catch {
        // Error handled in store
      }
    }
  }, [uploadImage]);

  const handleDetect = async () => {
    await runDetection(config);
    setCurrentStep('verification');
  };

  const handleGenerateBOM = async () => {
    await generateBOM();
    setCurrentStep('bom');
  };

  const handleSessionSelect = async (sessionId: string) => {
    await loadSession(sessionId);
  };

  const handleNewSession = () => {
    reset();
    setCurrentStep('upload');
  };

  // Handle reset detections
  const handleResetDetections = async () => {
    if (!currentSession) return;
    if (!confirm('모든 검출 결과를 초기화하시겠습니까?')) return;
    try {
      // Delete all detections
      for (const detection of detections) {
        await detectionApi.deleteDetection(currentSession.session_id, detection.id);
      }
      // Reload session
      await loadSession(currentSession.session_id);
      setCurrentStep('detection');
    } catch (err) {
      console.error('Failed to reset detections:', err);
    }
  };

  // Render workflow steps
  const renderWorkflowSteps = () => (
    <div className="space-y-2">
      {[
        { id: 'upload', label: '1. 이미지 업로드', icon: Upload },
        { id: 'detection', label: '2. 객체 검출', icon: Play },
        { id: 'verification', label: '3. 검증 및 수정', icon: CheckCircle },
        { id: 'bom', label: '4. BOM 생성', icon: FileSpreadsheet },
      ].map(({ id, label, icon: Icon }) => {
        const isActive = currentStep === id;
        const isCompleted =
          (id === 'upload' && currentSession) ||
          (id === 'detection' && detections.length > 0) ||
          (id === 'verification' && stats.approved > 0) ||
          (id === 'bom' && bomData);

        return (
          <button
            key={id}
            onClick={() => setCurrentStep(id as WorkflowStep)}
            disabled={!currentSession && id !== 'upload'}
            className={`
              w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors
              ${isActive
                ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                : isCompleted
                  ? 'bg-green-50 text-green-700 hover:bg-green-100'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }
              ${!currentSession && id !== 'upload' ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <Icon className={`w-5 h-5 ${isCompleted && !isActive ? 'text-green-500' : ''}`} />
            <span className="font-medium">{label}</span>
            {isCompleted && !isActive && <Check className="w-4 h-4 ml-auto text-green-500" />}
          </button>
        );
      })}
    </div>
  );

  // Tooltip wrapper for icons
  const IconWithTooltip = ({ children, title }: { children: React.ReactNode; title: string }) => (
    <span className="inline-flex cursor-help" title={title}>
      {children}
    </span>
  );

  // Render sidebar
  const renderSidebar = () => (
    <aside className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen transition-colors">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Blueprint AI BOM</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">도면 분석 및 BOM 생성</p>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            title={darkMode ? '라이트 모드로 전환' : '다크 모드로 전환'}
          >
            {darkMode ? <Sun className="w-5 h-5 text-yellow-500" /> : <Moon className="w-5 h-5 text-gray-600" />}
          </button>
        </div>

        {/* GPU 상태 (상세) */}
        <div className="mt-3">
          {gpuStatus?.available ? (
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-xs">
                <Cpu className="w-4 h-4 text-green-500" />
                <span className="text-green-600 dark:text-green-400 font-medium">
                  GPU 사용 중 ({gpuStatus.gpu_util}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${gpuStatus.memory_percent}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                메모리: {gpuStatus.memory_used}MB / {gpuStatus.memory_total}MB
              </p>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-xs text-blue-600 dark:text-blue-400">
              <Cpu className="w-4 h-4" />
              <span>CPU 모드로 실행 중</span>
            </div>
          )}
        </div>
      </div>

      {/* 시스템 정보 */}
      <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setShowSystemInfo(!showSystemInfo)}
          className="w-full flex items-center justify-between text-sm text-gray-700 dark:text-gray-300"
        >
          <span className="flex items-center space-x-2">
            <Info className="w-4 h-4" />
            <span>시스템 정보</span>
          </span>
          {showSystemInfo ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
        {showSystemInfo && systemInfo && (
          <div className="mt-2 space-y-1 text-xs text-gray-600 dark:text-gray-400 pl-6">
            <p>✅ 모델: {systemInfo.model_name}</p>
            <p>✅ 클래스: {systemInfo.class_count}개</p>
            <p>✅ 가격 데이터: {systemInfo.pricing_count}개 부품</p>
            <p>✅ 세션: {systemInfo.session_count}개</p>
            <p>✅ 버전: {systemInfo.version}</p>
          </div>
        )}
      </div>

      {/* Workflow Steps */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2 mb-3">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">워크플로우</h2>
          <IconWithTooltip title="단계별로 도면 분석을 진행합니다. 업로드 → 검출 → 검증 → BOM 생성">
            <HelpCircle className="w-4 h-4 text-gray-400" />
          </IconWithTooltip>
        </div>
        {renderWorkflowSteps()}
      </div>

      {/* Current Session Info */}
      {currentSession && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">현재 세션</h2>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
            <p className="font-medium text-gray-900 dark:text-white truncate">{currentSession.filename}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {new Date(currentSession.created_at).toLocaleString('ko-KR')}
            </p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div className="bg-blue-50 dark:bg-blue-900/30 rounded px-2 py-1">
                <span className="text-blue-600 dark:text-blue-400">검출: {stats.total}</span>
              </div>
              <div className="bg-green-50 dark:bg-green-900/30 rounded px-2 py-1">
                <span className="text-green-600 dark:text-green-400">승인: {stats.approved}</span>
              </div>
            </div>
            <button
              onClick={handleNewSession}
              className="mt-3 w-full text-sm text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 flex items-center justify-center space-x-1"
              title="현재 세션을 초기화하고 새로운 분석을 시작합니다"
            >
              <Trash2 className="w-4 h-4" />
              <span>새 세션 시작</span>
            </button>
          </div>
        </div>
      )}

      {/* Recent Sessions */}
      <div className="flex-1 overflow-y-auto p-4">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">최근 세션</h2>
        {sessions.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">세션이 없습니다.</p>
        ) : (
          <ul className="space-y-2">
            {sessions.slice(0, 10).map(session => (
              <li
                key={session.session_id}
                className={`
                  group relative p-2 rounded-lg text-sm transition-colors
                  ${currentSession?.session_id === session.session_id
                    ? 'bg-primary-50 dark:bg-primary-900/30 border border-primary-200 dark:border-primary-700'
                    : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600'
                  }
                `}
              >
                <div
                  onClick={() => handleSessionSelect(session.session_id)}
                  className="cursor-pointer pr-6"
                  title="클릭하여 이 세션을 불러옵니다"
                >
                  <p className="font-medium truncate text-gray-900 dark:text-white">{session.filename}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{session.detection_count}개 검출</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('이 세션을 삭제하시겠습니까?')) {
                      deleteSession(session.session_id);
                    }
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 dark:hover:bg-red-900/50 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-all"
                  title="세션 삭제"
                >
                  <X className="w-4 h-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Settings Toggle */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          title="YOLO 모델의 검출 설정을 조정합니다"
        >
          <span className="flex items-center space-x-2 text-gray-700 dark:text-gray-300">
            <Settings className="w-4 h-4" />
            <span className="text-sm">검출 설정</span>
          </span>
          {showSettings ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
        </button>
        {showSettings && (
          <div className="mt-3 space-y-3">
            <div>
              <div className="flex items-center space-x-1">
                <label className="text-xs text-gray-600 dark:text-gray-400">신뢰도: {config.confidence}</label>
                <IconWithTooltip title="검출 신뢰도 임계값. 높을수록 정확하지만 검출 수가 줄어듭니다.">
                  <HelpCircle className="w-3 h-3 text-gray-400" />
                </IconWithTooltip>
              </div>
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
              <div className="flex items-center space-x-1">
                <label className="text-xs text-gray-600 dark:text-gray-400">IOU: {config.iou_threshold}</label>
                <IconWithTooltip title="IoU (Intersection over Union) 임계값. 중복 검출 제거에 사용됩니다.">
                  <HelpCircle className="w-3 h-3 text-gray-400" />
                </IconWithTooltip>
              </div>
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
          </div>
        )}
      </div>

      {/* 캐시 관리 */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center space-x-2">
          <Trash2 className="w-4 h-4" />
          <span>캐시 관리</span>
        </h2>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleClearCache('memory')}
            disabled={isClearingCache}
            className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 text-xs transition-colors disabled:opacity-50"
            title="Python 메모리 가비지 컬렉션을 실행합니다"
          >
            {isClearingCache ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            <span>메모리 정리</span>
          </button>
          <button
            onClick={() => handleClearCache('all')}
            disabled={isClearingCache}
            className="flex items-center justify-center space-x-1 px-2 py-1.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 text-xs transition-colors disabled:opacity-50"
            title="7일 이상 된 업로드 파일과 메모리를 정리합니다"
          >
            {isClearingCache ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
            <span>전체 정리</span>
          </button>
        </div>
      </div>
    </aside>
  );

  // Render main content based on step
  const renderMainContent = () => {
    if (error) {
      return (
        <div className="m-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
          <button onClick={clearError} className="text-red-500 hover:text-red-700 text-xl">×</button>
        </div>
      );
    }

    switch (currentStep) {
      case 'upload':
        return renderUploadStep();
      case 'detection':
        return renderDetectionStep();
      case 'verification':
        return renderVerificationStep();
      case 'bom':
        return renderBOMStep();
      default:
        return null;
    }
  };

  // Upload Step (Streamlit-like with radio and test images)
  const renderUploadStep = () => (
    <div className="flex-1 p-6 dark:bg-gray-900">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">📁 도면 파일 선택</h2>

      {/* Upload method radio (like Streamlit) */}
      <div className="mb-6">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">파일 선택 방법:</label>
        <div className="flex space-x-4">
          <label className={`flex items-center px-4 py-2 rounded-lg cursor-pointer transition-colors ${
            uploadMode === 'upload'
              ? 'bg-primary-100 dark:bg-primary-900/50 border-2 border-primary-500'
              : 'bg-gray-100 dark:bg-gray-700 border-2 border-transparent hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}>
            <input
              type="radio"
              name="uploadMode"
              value="upload"
              checked={uploadMode === 'upload'}
              onChange={() => setUploadMode('upload')}
              className="sr-only"
            />
            <Upload className="w-4 h-4 mr-2" />
            <span className="text-sm dark:text-white">📤 새 파일 업로드</span>
          </label>
          <label className={`flex items-center px-4 py-2 rounded-lg cursor-pointer transition-colors ${
            uploadMode === 'test'
              ? 'bg-primary-100 dark:bg-primary-900/50 border-2 border-primary-500'
              : 'bg-gray-100 dark:bg-gray-700 border-2 border-transparent hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}>
            <input
              type="radio"
              name="uploadMode"
              value="test"
              checked={uploadMode === 'test'}
              onChange={() => setUploadMode('test')}
              className="sr-only"
            />
            <ImageIcon className="w-4 h-4 mr-2" />
            <span className="text-sm dark:text-white">📂 테스트 이미지 선택</span>
          </label>
        </div>
      </div>

      {/* Upload area or Test image dropdown */}
      {uploadMode === 'upload' ? (
        <div
          className={`
            relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors
            ${dragActive
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800'
            }
            ${isLoading ? 'opacity-50 pointer-events-none' : ''}
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".png,.jpg,.jpeg,.pdf"
            className="hidden"
            onChange={handleFileSelect}
            disabled={isLoading}
          />
          {isLoading ? (
            <Loader2 className="w-16 h-16 mx-auto mb-4 text-primary-500 animate-spin" />
          ) : (
            <Upload className={`w-16 h-16 mx-auto mb-4 ${dragActive ? 'text-primary-500' : 'text-gray-400'}`} />
          )}
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
            {isLoading ? '업로드 중...' : '도면 파일을 드래그하거나 클릭하여 선택'}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">PNG, JPG, JPEG, PDF (최대 50MB)</p>
        </div>
      ) : (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">테스트 이미지 선택:</label>
          {testImages.length > 0 ? (
            <select
              value={selectedTestImage}
              onChange={(e) => handleTestImageSelect(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              disabled={isLoading}
            >
              <option value="">선택하세요...</option>
              {testImages.map((img) => (
                <option key={img.filename} value={img.filename}>
                  {img.filename} ({(img.size / 1024).toFixed(1)} KB)
                </option>
              ))}
            </select>
          ) : (
            <div className="text-gray-500 dark:text-gray-400 py-4">
              ⚠️ test_drawings 폴더에 테스트 파일이 없습니다.
            </div>
          )}
        </div>
      )}

      {/* Current loaded file info (like Streamlit) */}
      {currentSession && imageData && (
        <div className="mt-6">
          <hr className="border-gray-200 dark:border-gray-700 my-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📋 현재 로드된 파일 정보</h3>

          {/* File info metrics (like Streamlit columns) - 확장된 상세 정보 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">📄 파일명</p>
              <p className="font-semibold text-gray-900 dark:text-white truncate" title={currentSession.filename}>
                {currentSession.filename}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">📁 파일 타입</p>
              <p className="font-semibold text-gray-900 dark:text-white uppercase">
                {currentSession.filename.split('.').pop()}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">📐 해상도</p>
              <p className="font-semibold text-gray-900 dark:text-white">
                {imageSize ? `${imageSize.width} × ${imageSize.height}` : '로딩...'}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">📊 종횡비</p>
              <p className="font-semibold text-gray-900 dark:text-white">
                {imageSize ? `${(imageSize.width / imageSize.height).toFixed(2)}:1` : '로딩...'}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                {imageSize && imageSize.width > imageSize.height ? '가로' : imageSize && imageSize.width < imageSize.height ? '세로' : '정방형'}
              </p>
            </div>
          </div>

          {/* 추가 도면 정보 (Streamlit 스타일) */}
          {imageSize && (
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="bg-blue-50 dark:bg-blue-900/30 p-3 rounded-lg border border-blue-200 dark:border-blue-700">
                <p className="text-xs text-blue-600 dark:text-blue-400 mb-1">총 픽셀 수</p>
                <p className="font-semibold text-blue-700 dark:text-blue-300">
                  {(imageSize.width * imageSize.height / 1000000).toFixed(2)} MP
                </p>
              </div>
              <div className="bg-green-50 dark:bg-green-900/30 p-3 rounded-lg border border-green-200 dark:border-green-700">
                <p className="text-xs text-green-600 dark:text-green-400 mb-1">권장 검출 설정</p>
                <p className="font-semibold text-green-700 dark:text-green-300">
                  {imageSize.width >= 3000 || imageSize.height >= 3000 ? '고해상도' :
                   imageSize.width >= 1500 || imageSize.height >= 1500 ? '중해상도' : '저해상도'}
                </p>
              </div>
              <div className="bg-purple-50 dark:bg-purple-900/30 p-3 rounded-lg border border-purple-200 dark:border-purple-700">
                <p className="text-xs text-purple-600 dark:text-purple-400 mb-1">DPI 추정 (A3 기준)</p>
                <p className="font-semibold text-purple-700 dark:text-purple-300">
                  {Math.round(imageSize.width / 16.54)} DPI
                </p>
              </div>
            </div>
          )}

          {/* Preview image */}
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
            <img src={imageData} alt="도면" className="max-h-96 mx-auto object-contain" />
          </div>

          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg text-green-700 dark:text-green-300">
            ✅ 파일이 성공적으로 로드되었습니다!
          </div>

          <button
            onClick={() => setCurrentStep('detection')}
            className="mt-4 flex items-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <span>다음: AI 모델 선택 및 검출</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );

  // Detection Step (Streamlit-like with model selection)
  const renderDetectionStep = () => (
    <div className="flex-1 p-6 overflow-y-auto dark:bg-gray-900">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">🤖 AI 모델 선택 및 검출</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Model Selection */}
        <div className="space-y-6">
          {/* Model Selection (like Streamlit) */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📦 사용할 모델 선택</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">하나 이상의 모델을 선택하세요. 여러 모델 선택 시 앙상블 검출을 수행합니다.</p>

            <div className="space-y-3">
              {availableModels.map((model) => (
                <label
                  key={model.id}
                  className={`flex items-start p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                    selectedModels.includes(model.id)
                      ? 'bg-primary-50 dark:bg-primary-900/30 border-primary-500'
                      : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:border-primary-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(model.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedModels([...selectedModels, model.id]);
                      } else {
                        setSelectedModels(selectedModels.filter(id => id !== model.id));
                      }
                    }}
                    className="mt-1 h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                  />
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900 dark:text-white">
                        {model.emoji} {model.name}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          model.speed === 'fast' ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300' :
                          model.speed === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300' :
                          'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300'
                        }`}>
                          {model.speed === 'fast' ? '⚡ 빠름' : model.speed === 'medium' ? '⏱️ 보통' : '🐢 느림'}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          정확도: {(model.accuracy * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{model.description}</p>
                  </div>
                </label>
              ))}
            </div>

            {/* Selected models summary */}
            {selectedModels.length > 0 && (
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg text-sm text-blue-700 dark:text-blue-300">
                ✅ {selectedModels.length}개 모델 선택됨
                {selectedModels.length > 1 && ' (앙상블 모드)'}
              </div>
            )}
          </div>

          {/* Detection Settings (like Streamlit expander) */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">⚙️ 검출 설정</h3>

            <div className="space-y-4">
              {/* Confidence */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    신뢰도 임계값
                  </label>
                  <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
                    {config.confidence}
                  </span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.05"
                  value={config.confidence}
                  onChange={(e) => setConfig({ ...config, confidence: parseFloat(e.target.value) })}
                  className="w-full accent-primary-600"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  높을수록 정확하지만 검출 수가 줄어듭니다
                </p>
              </div>

              {/* IOU */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    NMS IoU 임계값
                  </label>
                  <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
                    {config.iou_threshold}
                  </span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={config.iou_threshold}
                  onChange={(e) => setConfig({ ...config, iou_threshold: parseFloat(e.target.value) })}
                  className="w-full accent-primary-600"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  중복 검출 제거를 위한 IoU 임계값
                </p>
              </div>

              {/* Enhanced OCR option */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableOCR}
                    onChange={(e) => setEnableOCR(e.target.checked)}
                    className="h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                    🔤 Enhanced OCR 활성화
                  </span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-7">
                  검출된 텍스트 영역에 대해 OCR 분석을 추가로 수행합니다
                </p>
              </div>
            </div>
          </div>

          {/* Run Detection Button */}
          <div className="flex gap-3">
            <button
              onClick={handleDetect}
              disabled={isLoading || !imageData || selectedModels.length === 0}
              className={`flex-1 flex items-center justify-center space-x-3 px-6 py-4 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed text-lg font-semibold transition-colors ${
                isLoading
                  ? 'bg-blue-500 cursor-wait'
                  : 'bg-primary-600 hover:bg-primary-700'
              }`}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span>검출 중...</span>
                </>
              ) : (
                <>
                  <Play className="w-6 h-6" />
                  <span>🚀 검출 시작</span>
                </>
              )}
            </button>
            {isLoading && (
              <button
                onClick={cancelDetection}
                className="flex items-center justify-center space-x-2 px-6 py-4 bg-red-500 text-white rounded-xl hover:bg-red-600 text-lg font-semibold transition-colors"
                title="검출 취소"
              >
                <StopCircle className="w-6 h-6" />
                <span>취소</span>
              </button>
            )}
          </div>

          {/* Progress bar during detection */}
          {isLoading && (
            <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-2">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                  AI 모델로 검출 수행 중...
                </span>
              </div>
              <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Preview & Results */}
        <div className="space-y-6">
          {/* Image Preview */}
          {imageData && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">📋 미리보기</h3>
              </div>
              <div className="relative bg-gray-100 dark:bg-gray-900">
                <img src={imageData} alt="도면" className="w-full max-h-[500px] object-contain" />

                {/* Bounding boxes overlay */}
                {imageSize && detections.length > 0 && (
                  <svg
                    className="absolute top-0 left-0 w-full h-full pointer-events-none"
                    viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                    preserveAspectRatio="xMidYMid meet"
                  >
                    {detections.map((detection, idx) => {
                      // 🟢approved:초록 🟣manual:보라 🟠modified:주황 🔴rejected:빨강 🟡pending:노랑
                      const color = detection.verification_status === 'approved' ? '#22c55e'
                        : detection.verification_status === 'manual' ? '#a855f7'
                        : detection.verification_status === 'modified' ? '#f97316'
                        : detection.verification_status === 'rejected' ? '#ef4444'
                        : '#eab308';
                      return (
                        <g key={detection.id}>
                          <rect
                            x={detection.bbox.x1}
                            y={detection.bbox.y1}
                            width={detection.bbox.x2 - detection.bbox.x1}
                            height={detection.bbox.y2 - detection.bbox.y1}
                            fill="none"
                            stroke={color}
                            strokeWidth={2}
                          />
                          <text
                            x={detection.bbox.x2 + 5}
                            y={detection.bbox.y1 + 15}
                            fill={color}
                            fontSize="14"
                            fontWeight="bold"
                          >
                            {idx + 1}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                )}
              </div>
            </div>
          )}

          {/* Detection Results */}
          {detections.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📊 검출 결과</h3>

              {/* Result metrics (like Streamlit columns) */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{detections.length}</p>
                  <p className="text-xs text-blue-700 dark:text-blue-300">총 검출</p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {(detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-300">평균 신뢰도</p>
                </div>
                <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {new Set(detections.map(d => d.class_name)).size}
                  </p>
                  <p className="text-xs text-purple-700 dark:text-purple-300">클래스 종류</p>
                </div>
              </div>

              {/* Class distribution */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">클래스별 검출:</h4>
                {Object.entries(
                  detections.reduce((acc, d) => {
                    acc[d.class_name] = (acc[d.class_name] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>)
                ).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([className, count]) => (
                  <div key={className} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400 truncate flex-1">{className}</span>
                    <span className="font-medium text-gray-900 dark:text-white ml-2">{count}개</span>
                  </div>
                ))}
              </div>

              {/* Next step button */}
              <button
                onClick={() => setCurrentStep('verification')}
                className="w-full mt-4 flex items-center justify-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                <span>다음: 검증 단계</span>
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Model filter state (only selectedModelFilter is used)
  const [selectedModelFilter] = useState<string>('all');

  // Filter detections by selected model
  const filteredDetections = useMemo(() => {
    if (selectedModelFilter === 'all') return detections;
    return detections.filter(d => d.model_id === selectedModelFilter);
  }, [detections, selectedModelFilter]);

  // Filtered pagination
  const filteredTotalPages = Math.max(1, Math.ceil(filteredDetections.length / ITEMS_PER_PAGE));
  const filteredPaginatedDetections = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredDetections.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredDetections, currentPage]);

  // Verification Step (Streamlit-like simplified layout)
  const renderVerificationStep = () => {
    return (
      <div className="flex-1 flex overflow-hidden">
        {/* Main verification area */}
        <div className="flex-1 p-6 overflow-y-auto bg-gray-50 dark:bg-gray-900">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">✅ 검출 검증</h2>
              <p className="text-gray-500 dark:text-gray-400 mt-1">각 검출 결과를 승인, 거부, 또는 수정하세요</p>
            </div>
            <div className="flex items-center space-x-3">
              {/* View mode toggle */}
              <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'grid'
                      ? 'bg-white dark:bg-gray-700 shadow text-primary-600 dark:text-primary-400'
                      : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                  title="3열 그리드 보기 (Streamlit 스타일)"
                >
                  <LayoutGrid className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'list'
                      ? 'bg-white dark:bg-gray-700 shadow text-primary-600 dark:text-primary-400'
                      : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                  title="리스트 보기"
                >
                  <List className="w-5 h-5" />
                </button>
              </div>
              <button
                onClick={() => setShowReferencePanel(!showReferencePanel)}
                className={`flex items-center space-x-2 px-4 py-2 border rounded-lg transition-colors ${
                  showReferencePanel
                    ? 'bg-primary-50 dark:bg-primary-900/30 border-primary-500 text-primary-700 dark:text-primary-400'
                    : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                }`}
                title="심볼 참조 이미지 패널을 열어 올바른 심볼과 비교합니다"
              >
                <ImageIcon className="w-5 h-5" />
                <span>참조 이미지</span>
              </button>
            </div>
          </div>

          {/* Streamlit-style: No tabs, sequential layout */}

          {/* Stats bar - 기본 검증 현황 */}
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 text-center" title="검출된 전체 객체 수">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</p>
              <p className="text-sm text-blue-700 dark:text-blue-300">전체</p>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/30 rounded-lg p-4 text-center" title="아직 검증되지 않은 객체">
              <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.pending}</p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">대기중</p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 text-center" title="승인된 객체 (BOM에 포함됨)">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.approved}</p>
              <p className="text-sm text-green-700 dark:text-green-300">승인</p>
            </div>
            <div className="bg-red-50 dark:bg-red-900/30 rounded-lg p-4 text-center" title="거부된 객체 (BOM에서 제외됨)">
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.rejected}</p>
              <p className="text-sm text-red-700 dark:text-red-300">거부</p>
            </div>
          </div>

          {/* 색상 범례 - Streamlit 스타일 */}
          <div className="flex items-center justify-center space-x-4 mb-4 text-xs">
            <span className="text-gray-500 dark:text-gray-400">바운딩 박스 색상:</span>
            <span className="flex items-center space-x-1">
              <span className="w-3 h-3 rounded-sm bg-[#22c55e]"></span>
              <span className="text-gray-600 dark:text-gray-300">승인</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-3 h-3 rounded-sm bg-[#a855f7]"></span>
              <span className="text-gray-600 dark:text-gray-300">수작업</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-3 h-3 rounded-sm bg-[#f97316]"></span>
              <span className="text-gray-600 dark:text-gray-300">수정</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-3 h-3 rounded-sm bg-[#ef4444]"></span>
              <span className="text-gray-600 dark:text-gray-300">거부</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-3 h-3 rounded-sm bg-[#eab308]"></span>
              <span className="text-gray-600 dark:text-gray-300">대기</span>
            </span>
          </div>

          {/* Extended Stats bar - Streamlit 스타일 추가 통계 */}
          <div className="grid grid-cols-5 gap-3 mb-6">
            <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-3 text-center" title="고유한 심볼 클래스 수">
              <p className="text-xl font-bold text-purple-600 dark:text-purple-400">{extendedStats.uniqueClasses}</p>
              <p className="text-xs text-purple-700 dark:text-purple-300">고유 클래스</p>
            </div>
            <div className="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-3 text-center" title="동일 클래스 중복 검출">
              <p className="text-xl font-bold text-orange-600 dark:text-orange-400">{extendedStats.totalDuplicates}</p>
              <p className="text-xs text-orange-700 dark:text-orange-300">중복 검출</p>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-900/30 rounded-lg p-3 text-center" title="90% 이상 신뢰도">
              <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{extendedStats.highConfidence}</p>
              <p className="text-xs text-emerald-700 dark:text-emerald-300">높음 (90%+)</p>
            </div>
            <div className="bg-amber-50 dark:bg-amber-900/30 rounded-lg p-3 text-center" title="70-90% 신뢰도">
              <p className="text-xl font-bold text-amber-600 dark:text-amber-400">{extendedStats.mediumConfidence}</p>
              <p className="text-xs text-amber-700 dark:text-amber-300">중간 (70-90%)</p>
            </div>
            <div className="bg-rose-50 dark:bg-rose-900/30 rounded-lg p-3 text-center" title="70% 미만 신뢰도">
              <p className="text-xl font-bold text-rose-600 dark:text-rose-400">{extendedStats.lowConfidence}</p>
              <p className="text-xs text-rose-700 dark:text-rose-300">낮음 (&lt;70%)</p>
            </div>
          </div>

          {/* Bulk actions - Streamlit style */}
          <div className="flex items-center space-x-3 mb-6">
            <button
              onClick={approveAll}
              disabled={isLoading || stats.pending === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-300 dark:border-green-700 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 disabled:opacity-50 transition-colors"
              title="대기중인 모든 검출을 승인합니다"
            >
              <Check className="w-4 h-4" />
              <span>모두 승인</span>
            </button>
            <button
              onClick={rejectAll}
              disabled={isLoading || stats.pending === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 disabled:opacity-50 transition-colors"
              title="대기중인 모든 검출을 거부합니다"
            >
              <X className="w-4 h-4" />
              <span>모두 거부</span>
            </button>
            <button
              onClick={handleResetDetections}
              disabled={isLoading || stats.total === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
              title="모든 검출 결과를 초기화합니다"
            >
              <RotateCcw className="w-4 h-4" />
              <span>초기화</span>
            </button>
            <div className="flex-1" />
            <button
              onClick={handleGenerateBOM}
              disabled={isLoading || stats.approved === 0}
              className="flex items-center space-x-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
              title="승인된 검출 결과로 부품 명세서(BOM)를 생성합니다"
            >
              <FileSpreadsheet className="w-5 h-5" />
              <span>BOM 생성</span>
            </button>
          </div>

          {/* Pagination */}
          {filteredTotalPages > 1 && (
            <div className="flex items-center justify-center space-x-2 mb-4">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                {currentPage} / {filteredTotalPages} 페이지 ({filteredDetections.length}개)
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(filteredTotalPages, p + 1))}
                disabled={currentPage === filteredTotalPages}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 transition-colors"
              >
                <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>
          )}

          {/* Detection cards - Streamlit style 3-column grid */}
          <div className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6'
              : 'space-y-4 mb-6'
          }>
            {filteredPaginatedDetections.map((detection, pageIndex) => {
              const globalIndex = (currentPage - 1) * ITEMS_PER_PAGE + pageIndex;
              return (
                <DetectionCard
                  key={detection.id}
                  detection={detection}
                  index={globalIndex}
                  imageData={imageData}
                  imageSize={imageSize}
                  availableClasses={availableClasses}
                  onVerify={(status: VerificationStatus, modifiedClassName?: string) =>
                    verifyDetection(detection.id, status, modifiedClassName)
                  }
                />
              );
            })}
          </div>

          {/* 최종 검증 이미지 - Streamlit style */}
          {imageData && imageSize && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 mb-6 overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">🖼️ 최종 검증 결과 이미지</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  🟢 승인 | 🔴 거부 | 🟡 대기
                </p>
              </div>
              <div className="relative bg-gray-100 dark:bg-gray-900 p-4">
                <img src={imageData} alt="검증 결과" className="w-full max-h-[500px] object-contain" />
                <svg
                  className="absolute top-4 left-4 right-4 bottom-4 pointer-events-none"
                  style={{ width: 'calc(100% - 2rem)', height: 'calc(100% - 2rem)' }}
                  viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                  preserveAspectRatio="xMidYMid meet"
                >
                  {detections.map((detection, idx) => {
                    // 🟢approved:초록 🟣manual:보라 🟠modified:주황 🔴rejected:빨강 🟡pending:노랑
                    const color = detection.verification_status === 'approved' ? '#22c55e'
                      : detection.verification_status === 'manual' ? '#a855f7'
                      : detection.verification_status === 'modified' ? '#f97316'
                      : detection.verification_status === 'rejected' ? '#ef4444'
                      : '#eab308';
                    return (
                      <g key={detection.id}>
                        <rect
                          x={detection.bbox.x1}
                          y={detection.bbox.y1}
                          width={detection.bbox.x2 - detection.bbox.x1}
                          height={detection.bbox.y2 - detection.bbox.y1}
                          fill={color}
                          fillOpacity={0.15}
                          stroke={color}
                          strokeWidth={2}
                        />
                        <text
                          x={detection.bbox.x1 + 4}
                          y={detection.bbox.y1 + 16}
                          fill="white"
                          fontSize="14"
                          fontWeight="bold"
                          style={{ textShadow: '1px 1px 2px black' }}
                        >
                          {idx + 1}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          )}

          {/* Manual Labeling Section - Streamlit style with Canvas Drawing (더 넓게 표시) */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 mb-6 -mx-4 sm:-mx-6 lg:-mx-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">✏️ 수작업 라벨 추가</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
              AI가 검출하지 못한 심볼을 수동으로 추가합니다.
            </p>

            {/* 클래스 선택 (캔버스와 수동 입력 공통) */}
            <div className={`mb-4 p-4 rounded-lg ${manualLabel.class_name ? 'bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-700' : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700'}`}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                1. 클래스 선택 (필수) {!manualLabel.class_name && <span className="text-red-500 animate-pulse">← 먼저 선택하세요!</span>}
              </label>
              <select
                value={manualLabel.class_name}
                onChange={(e) => setManualLabel({ ...manualLabel, class_name: e.target.value })}
                className={`w-full md:w-1/2 border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 ${!manualLabel.class_name ? 'border-yellow-400 dark:border-yellow-600' : 'border-green-400 dark:border-green-600'}`}
              >
                <option value="">클래스 선택...</option>
                {availableClasses.map((cls) => (
                  <option key={cls} value={cls}>{cls}</option>
                ))}
              </select>
              {manualLabel.class_name && (
                <p className="mt-2 text-sm text-green-600 dark:text-green-400">
                  ✓ 선택됨: <strong>{manualLabel.class_name}</strong>
                </p>
              )}
            </div>

            {/* 캔버스 기반 그리기 */}
            {imageData && imageSize && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  2. 바운딩 박스 그리기 (이미지 위에서 드래그)
                </label>
                <DrawingCanvas
                  imageData={imageData}
                  imageSize={imageSize}
                  selectedClass={manualLabel.class_name}
                  existingBoxes={detections.map(d => ({
                    bbox: d.bbox,
                    label: `${detections.indexOf(d) + 1}`,
                    // 🟢approved:초록 🟣manual:보라 🟠modified:주황 🔴rejected:빨강 🟡pending:노랑
                    color: d.verification_status === 'approved' ? '#22c55e' :
                           d.verification_status === 'manual' ? '#a855f7' :
                           d.verification_status === 'modified' ? '#f97316' :
                           d.verification_status === 'rejected' ? '#ef4444' : '#eab308'
                  }))}
                  onBoxDrawn={(box) => {
                    if (manualLabel.class_name) {
                      // 캔버스에서 그린 박스로 수작업 라벨 추가
                      detectionApi.addManual(currentSession!.session_id, {
                        class_name: manualLabel.class_name,
                        bbox: box,
                      }).then(() => {
                        loadSession(currentSession!.session_id);
                      }).catch((err) => {
                        console.error('Failed to add manual detection:', err);
                      });
                    }
                  }}
                />
              </div>
            )}

            {/* 수작업 라벨 목록 */}
            {detections.filter(d => d.verification_status === 'manual').length > 0 && (
              <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
                  추가된 수작업 라벨 ({detections.filter(d => d.verification_status === 'manual').length}개)
                </h4>
                <div className="space-y-2 max-h-[250px] overflow-y-auto">
                  {detections.filter(d => d.verification_status === 'manual').map((d, idx) => (
                  <div key={d.id} className="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded border border-blue-200 dark:border-blue-700">
                    <div className="flex items-center space-x-2">
                      <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                        {idx + 1}
                      </span>
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white text-sm">{d.class_name}</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                          ({d.bbox.x1}, {d.bbox.y1}) - ({d.bbox.x2}, {d.bbox.y2})
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => detectionApi.deleteDetection(currentSession!.session_id, d.id).then(() => loadSession(currentSession!.session_id))}
                      className="text-red-500 hover:text-red-700 p-1"
                      title="삭제"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                </div>
              </div>
            )}
          </div>

          {/* Ground Truth 비교 - Streamlit 스타일 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">📊 Ground Truth 비교 (정확도 평가)</h3>
              <button
                onClick={() => setShowGTSection(!showGTSection)}
                className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
              >
                {showGTSection ? '접기' : '펼치기'}
              </button>
            </div>

            {showGTSection && (
              <div className="space-y-4">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  테스트 이미지에 대한 Ground Truth 라벨이 있는 경우, 검출 결과와 비교하여 정확도를 평가할 수 있습니다.
                </p>

                <button
                  onClick={handleCompareGT}
                  disabled={isLoadingGT || !currentSession}
                  className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {isLoadingGT ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>비교 중...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      <span>GT와 비교</span>
                    </>
                  )}
                </button>

                {gtCompareResult && gtCompareResult.has_ground_truth && (
                  <div className="space-y-4">
                    {/* F1/Precision/Recall 메트릭 */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                          {(gtCompareResult.metrics.precision * 100).toFixed(1)}%
                        </p>
                        <p className="text-sm text-blue-700 dark:text-blue-300">Precision (정밀도)</p>
                        <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                          검출 중 실제 맞춘 비율
                        </p>
                      </div>
                      <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                          {(gtCompareResult.metrics.recall * 100).toFixed(1)}%
                        </p>
                        <p className="text-sm text-green-700 dark:text-green-300">Recall (재현율)</p>
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                          실제 중 검출한 비율
                        </p>
                      </div>
                      <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                          {(gtCompareResult.metrics.f1_score * 100).toFixed(1)}%
                        </p>
                        <p className="text-sm text-purple-700 dark:text-purple-300">F1 Score</p>
                        <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                          정밀도·재현율 조화평균
                        </p>
                      </div>
                    </div>

                    {/* TP/FP/FN 상세 */}
                    <div className="grid grid-cols-4 gap-3">
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
                        <p className="text-xl font-bold text-gray-700 dark:text-gray-300">{gtCompareResult.gt_count}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">GT 라벨</p>
                      </div>
                      <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-3 text-center">
                        <p className="text-xl font-bold text-green-600 dark:text-green-400">{gtCompareResult.metrics.tp}</p>
                        <p className="text-xs text-green-700 dark:text-green-300">True Positive</p>
                      </div>
                      <div className="bg-red-50 dark:bg-red-900/30 rounded-lg p-3 text-center">
                        <p className="text-xl font-bold text-red-600 dark:text-red-400">{gtCompareResult.metrics.fp}</p>
                        <p className="text-xs text-red-700 dark:text-red-300">False Positive</p>
                      </div>
                      <div className="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-3 text-center">
                        <p className="text-xl font-bold text-orange-600 dark:text-orange-400">{gtCompareResult.metrics.fn}</p>
                        <p className="text-xs text-orange-700 dark:text-orange-300">False Negative</p>
                      </div>
                    </div>

                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      IoU 임계값: {gtCompareResult.metrics.iou_threshold}
                    </p>
                  </div>
                )}

                {gtCompareResult && !gtCompareResult.has_ground_truth && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      ⚠️ 이 파일에 대한 Ground Truth 라벨이 없습니다.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 승인된 심볼 목록 - Streamlit 스타일 */}
          {stats.approved > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">✅ 승인된 심볼 목록</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-2 text-sm font-medium text-gray-600 dark:text-gray-400">클래스명</th>
                      <th className="text-center py-2 text-sm font-medium text-gray-600 dark:text-gray-400">수량</th>
                      <th className="text-right py-2 text-sm font-medium text-gray-600 dark:text-gray-400">평균 신뢰도</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(approvedSymbols)
                      .sort((a, b) => b[1].count - a[1].count)
                      .map(([className, data]) => (
                        <tr key={className} className="border-b border-gray-100 dark:border-gray-800">
                          <td className="py-3 text-sm text-gray-900 dark:text-white truncate max-w-[200px]" title={className}>
                            {className}
                          </td>
                          <td className="py-3 text-sm text-center text-gray-700 dark:text-gray-300">
                            {data.count}개
                          </td>
                          <td className="py-3 text-sm text-right">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              data.avgConf >= 0.9 ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300' :
                              data.avgConf >= 0.7 ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300' :
                              'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300'
                            }`}>
                              {(data.avgConf * 100).toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-gray-50 dark:bg-gray-900">
                      <td className="py-3 text-sm font-medium text-gray-700 dark:text-gray-300">합계</td>
                      <td className="py-3 text-sm font-bold text-center text-gray-900 dark:text-white">
                        {Object.values(approvedSymbols).reduce((sum, d) => sum + d.count, 0)}개
                      </td>
                      <td className="py-3 text-sm font-medium text-right text-gray-500 dark:text-gray-400">
                        평균: {(extendedStats.avgConfidence * 100).toFixed(1)}%
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Reference panel */}
        {showReferencePanel && (
          <ReferencePanel
            onClose={() => setShowReferencePanel(false)}
          />
        )}
      </div>
    );
  };

  // BOM Step
  const renderBOMStep = () => {
    if (!bomData) {
      return (
        <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="text-center text-gray-500 dark:text-gray-400">
            <FileSpreadsheet className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>BOM 데이터가 없습니다.</p>
            <p className="text-sm">검출 결과를 승인하고 BOM을 생성하세요.</p>
          </div>
        </div>
      );
    }

    // Class distribution for chart
    const classDistribution: Record<string, number> = {};
    bomData.items.forEach(item => {
      classDistribution[item.class_name] = (classDistribution[item.class_name] || 0) + item.quantity;
    });
    const sortedClasses = Object.entries(classDistribution).sort((a, b) => b[1] - a[1]);
    const maxQuantity = Math.max(...Object.values(classDistribution));
    const chartColors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-orange-500'];

    return (
      <div className="flex-1 p-6 overflow-y-auto bg-gray-50 dark:bg-gray-900">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">📊 BOM 생성</h2>
            <p className="text-gray-500 dark:text-gray-400 mt-1">승인된 검출 결과로 생성된 부품 명세서입니다</p>
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="excel">Excel (.xlsx)</option>
              <option value="csv">CSV (.csv)</option>
              <option value="json">JSON (.json)</option>
              <option value="pdf">PDF (.pdf)</option>
            </select>
            <a
              href={`http://localhost:5020/bom/${currentSession?.session_id}/download?format=${exportFormat}`}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              download
            >
              <Download className="w-5 h-5" />
              <span>다운로드</span>
            </a>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">부품 종류</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{bomData.summary.total_items}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">총 수량</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{bomData.summary.total_quantity}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">소계</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">₩{bomData.summary.subtotal.toLocaleString()}</p>
          </div>
          <div className="bg-primary-50 dark:bg-primary-900/30 rounded-lg border border-primary-200 dark:border-primary-700 p-4">
            <p className="text-sm text-primary-600 dark:text-primary-400">합계</p>
            <p className="text-2xl font-bold text-primary-700 dark:text-primary-300">₩{bomData.summary.total.toLocaleString()}</p>
          </div>
        </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Class Distribution Chart (like Streamlit) */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📊 클래스별 분포</h3>
                <div className="space-y-3">
                  {sortedClasses.slice(0, 8).map(([className, count], idx) => (
                    <div key={className}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-400 truncate max-w-[150px]" title={className}>
                          {className}
                        </span>
                        <span className="font-medium text-gray-900 dark:text-white">{count}개</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                        <div
                          className={`${chartColors[idx % chartColors.length]} h-3 rounded-full transition-all`}
                          style={{ width: `${(count / maxQuantity) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                  {sortedClasses.length > 8 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      ... 외 {sortedClasses.length - 8}개 클래스
                    </p>
                  )}
                </div>
              </div>

              {/* Price Distribution (like Streamlit pie chart) */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">💰 가격 분포</h3>
                <div className="space-y-3">
                  {bomData.items.sort((a, b) => b.total_price - a.total_price).slice(0, 5).map((item, idx) => {
                    const percentage = (item.total_price / bomData.summary.subtotal) * 100;
                    return (
                      <div key={item.item_no}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-600 dark:text-gray-400 truncate max-w-[120px]" title={item.class_name}>
                            {item.class_name}
                          </span>
                          <span className="font-medium text-gray-900 dark:text-white">
                            {percentage.toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                          <div
                            className={`${chartColors[(idx + 3) % chartColors.length]} h-3 rounded-full`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Confidence Distribution */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">🎯 신뢰도 분포</h3>
                <div className="space-y-3">
                  {(() => {
                    const high = bomData.items.filter(i => i.avg_confidence >= 0.9).length;
                    const medium = bomData.items.filter(i => i.avg_confidence >= 0.7 && i.avg_confidence < 0.9).length;
                    const low = bomData.items.filter(i => i.avg_confidence < 0.7).length;
                    const total = bomData.items.length;
                    return (
                      <>
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-green-600 dark:text-green-400">높음 (90%+)</span>
                            <span className="font-medium text-gray-900 dark:text-white">{high}개 ({((high/total)*100).toFixed(0)}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                            <div className="bg-green-500 h-3 rounded-full" style={{ width: `${(high/total)*100}%` }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-yellow-600 dark:text-yellow-400">중간 (70-90%)</span>
                            <span className="font-medium text-gray-900 dark:text-white">{medium}개 ({((medium/total)*100).toFixed(0)}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                            <div className="bg-yellow-500 h-3 rounded-full" style={{ width: `${(medium/total)*100}%` }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-red-600 dark:text-red-400">낮음 (70% 미만)</span>
                            <span className="font-medium text-gray-900 dark:text-white">{low}개 ({((low/total)*100).toFixed(0)}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                            <div className="bg-red-500 h-3 rounded-full" style={{ width: `${(low/total)*100}%` }} />
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            </div>

            {/* Top 10 Cost Items (Streamlit-like) */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">💎 비용 상위 10개 부품</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-2 text-sm font-medium text-gray-600 dark:text-gray-400">순위</th>
                      <th className="text-left py-2 text-sm font-medium text-gray-600 dark:text-gray-400">부품명</th>
                      <th className="text-center py-2 text-sm font-medium text-gray-600 dark:text-gray-400">수량</th>
                      <th className="text-right py-2 text-sm font-medium text-gray-600 dark:text-gray-400">단가</th>
                      <th className="text-right py-2 text-sm font-medium text-gray-600 dark:text-gray-400">합계</th>
                      <th className="text-right py-2 text-sm font-medium text-gray-600 dark:text-gray-400">비율</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bomData.items
                      .sort((a, b) => b.total_price - a.total_price)
                      .slice(0, 10)
                      .map((item, idx) => {
                        const percentage = (item.total_price / bomData.summary.subtotal) * 100;
                        return (
                          <tr key={item.item_no} className="border-b border-gray-100 dark:border-gray-800">
                            <td className="py-3">
                              <span className={`w-6 h-6 inline-flex items-center justify-center rounded-full text-xs font-bold ${
                                idx < 3 ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                              }`}>
                                {idx + 1}
                              </span>
                            </td>
                            <td className="py-3 text-sm font-medium text-gray-900 dark:text-white max-w-[200px] truncate" title={item.class_name}>
                              {item.class_name}
                            </td>
                            <td className="py-3 text-sm text-center text-gray-600 dark:text-gray-400">{item.quantity}개</td>
                            <td className="py-3 text-sm text-right text-gray-600 dark:text-gray-400">₩{item.unit_price.toLocaleString()}</td>
                            <td className="py-3 text-sm text-right font-bold text-gray-900 dark:text-white">₩{item.total_price.toLocaleString()}</td>
                            <td className="py-3 text-sm text-right">
                              <div className="flex items-center justify-end space-x-2">
                                <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                  <div
                                    className="bg-primary-500 h-2 rounded-full"
                                    style={{ width: `${Math.min(percentage, 100)}%` }}
                                  />
                                </div>
                                <span className="text-gray-600 dark:text-gray-400 w-12">{percentage.toFixed(1)}%</span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                  <tfoot>
                    <tr className="bg-gray-50 dark:bg-gray-900">
                      <td colSpan={4} className="py-3 text-sm font-medium text-gray-700 dark:text-gray-300 text-right">
                        상위 10개 소계:
                      </td>
                      <td className="py-3 text-sm font-bold text-right text-primary-600 dark:text-primary-400">
                        ₩{bomData.items.sort((a, b) => b.total_price - a.total_price).slice(0, 10).reduce((sum, item) => sum + item.total_price, 0).toLocaleString()}
                      </td>
                      <td className="py-3 text-sm font-bold text-right text-primary-600 dark:text-primary-400">
                        {((bomData.items.sort((a, b) => b.total_price - a.total_price).slice(0, 10).reduce((sum, item) => sum + item.total_price, 0) / bomData.summary.subtotal) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* BOM Table */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">📝 상세 BOM 테이블</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">No.</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">부품명</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">모델명</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">수량</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">단가</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">합계</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">공급업체</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">리드타임</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">신뢰도</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {bomData.items.map((item) => (
                      <tr key={item.item_no} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">{item.item_no}</td>
                        <td className="px-4 py-4 text-sm font-medium text-gray-900 dark:text-white max-w-[200px] truncate" title={item.class_name}>
                          {item.class_name}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">{item.model_name || '-'}</td>
                        <td className="px-4 py-4 text-sm text-gray-900 dark:text-white text-right">{item.quantity}</td>
                        <td className="px-4 py-4 text-sm text-gray-900 dark:text-white text-right">₩{item.unit_price.toLocaleString()}</td>
                        <td className="px-4 py-4 text-sm font-medium text-gray-900 dark:text-white text-right">₩{item.total_price.toLocaleString()}</td>
                        <td className="px-4 py-4 text-sm text-gray-600 dark:text-gray-400">{item.supplier || '-'}</td>
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400 text-center">
                          <span className="px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">{item.lead_time || '-'}</span>
                        </td>
                        <td className="px-4 py-4 text-sm text-right">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            item.avg_confidence >= 0.9 ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300' :
                            item.avg_confidence >= 0.7 ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300' :
                            'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300'
                          }`}>
                            {(item.avg_confidence * 100).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Meta info */}
            <div className="mt-6 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-700">
              <p>📅 생성일: {new Date(bomData.created_at).toLocaleString('ko-KR')}</p>
              <p>🔍 검출 수: {bomData.detection_count}개 / 승인 수: {bomData.approved_count}개</p>
            </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {renderSidebar()}
      <main className="flex-1 flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-900">
        {renderMainContent()}
      </main>
    </div>
  );
}
