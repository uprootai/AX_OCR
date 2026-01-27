/**
 * Workflow Sidebar Component
 * 워크플로우 사이드바 - 세션 관리, 설정, 캐시 관리
 * Phase 2C: 이미지 검토 기능 통합
 */

import React, { useRef, useState, useCallback, useEffect } from 'react';
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
  RefreshCw,
  Download,
  Upload,
  ImagePlus,
  Images,
  FileArchive,
  Cpu,
  Zap,
  Package,
  FileJson,
  CheckCircle,
  CheckSquare,
  Square,
  ChevronsLeft,
  ChevronsRight,
  BookOpen,
  Link2,
  FolderPlus,
  FolderOpen,
} from 'lucide-react';
import { sessionApi } from '../../../lib/api';
import { API_BASE_URL } from '../../../lib/constants';
import type { GPUStatus } from '../../../lib/api';
import type { SessionImage } from '../../../types';

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
};

// 도면 유형 옵션 (기본 제공)
const DRAWING_TYPE_OPTIONS: { value: string; label: string; description: string }[] = [
  { value: 'auto', label: '자동 감지', description: 'VLM이 자동으로 분류' },
  { value: 'electrical', label: '전기 도면', description: '전기 회로도, 배선도' },
  { value: 'pid', label: 'P&ID', description: '배관 계장도' },
  { value: 'sld', label: 'SLD', description: '단선 결선도' },
  { value: 'mechanical', label: '기계 도면', description: '기계 부품도, 조립도' },
];

// 참조 세트 타입
interface ReferenceSet {
  id: string;
  name: string;
  description?: string;
  image_count: number;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}


// 페이지네이션 상수
const IMAGES_PER_PAGE = 20;

// 이미지 + GT 상태
interface ImageWithGT extends SessionImage {
  has_gt?: boolean;
  gt_filename?: string;
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
  detectionCount: number;
  // Image management (Phase 2C)
  sessionImageCount?: number;
  onImagesAdded?: () => void;
  onImageSelect?: (imageId: string, image: SessionImage) => void;
  onImagesSelect?: (imageIds: string[], images: SessionImage[]) => void;  // 다중 선택 콜백
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
  const imageUploadRef = useRef<HTMLInputElement>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isExportingSelfContained, setIsExportingSelfContained] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isUploadingImages, setIsUploadingImages] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // 이미지 목록 관련 상태
  const [images, setImages] = useState<ImageWithGT[]>([]);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [selectedImageIds, setSelectedImageIds] = useState<Set<string>>(new Set());  // 다중 선택
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);  // 다중 선택 모드
  const [currentPage, setCurrentPage] = useState(1);  // 페이지네이션
  const [isLoadingImages, setIsLoadingImages] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [showImageReview, setShowImageReview] = useState(true);

  // 참조 도면 유형 상태
  const [localDrawingType, setLocalDrawingType] = useState<string>('auto');
  const effectiveDrawingType = externalDrawingType || localDrawingType || currentSession?.drawing_type || 'auto';

  // 커스텀 참조 세트 상태
  const [referenceSets, setReferenceSets] = useState<ReferenceSet[]>([]);
  const [isLoadingRefSets, setIsLoadingRefSets] = useState(false);
  const [showRefSetManager, setShowRefSetManager] = useState(false);
  const [isUploadingRefSet, setIsUploadingRefSet] = useState(false);
  const refSetUploadRef = useRef<HTMLInputElement>(null);
  const [newRefSetName, setNewRefSetName] = useState('');
  const [newRefSetDescription, setNewRefSetDescription] = useState('');

  // GT 업로드 관련 상태
  const gtUploadRef = useRef<HTMLInputElement>(null);
  const [uploadingGTFor, setUploadingGTFor] = useState<string | null>(null);  // 어떤 이미지에 GT 업로드 중인지

  // 도면 유형 변경 핸들러
  const handleDrawingTypeChange = useCallback((newType: string) => {
    setLocalDrawingType(newType);
    onDrawingTypeChange?.(newType);
  }, [onDrawingTypeChange]);

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

  // 컴포넌트 마운트 시 참조 세트 로드
  useEffect(() => {
    loadReferenceSets();
  }, [loadReferenceSets]);

  // 참조 세트 업로드 핸들러
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
      if (newRefSetDescription) {
        formData.append('description', newRefSetDescription);
      }

      const response = await fetch(`${API_BASE_URL}/reference-sets`, {
        method: 'POST',
        body: formData,
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
      if (refSetUploadRef.current) {
        refSetUploadRef.current.value = '';
      }
    }
  }, [newRefSetName, newRefSetDescription]);

  // 참조 세트 삭제 핸들러
  const handleDeleteRefSet = useCallback(async (setId: string, setName: string) => {
    if (!confirm(`"${setName}" 세트를 삭제하시겠습니까?`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/reference-sets/${setId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Delete failed');
      }

      setReferenceSets(prev => prev.filter(s => s.id !== setId));
      // 삭제한 세트가 현재 선택된 세트면 auto로 변경
      if (effectiveDrawingType === setId) {
        handleDrawingTypeChange('auto');
      }
    } catch (error) {
      console.error('Reference set delete failed:', error);
      alert('참조 세트 삭제에 실패했습니다.');
    }
  }, [effectiveDrawingType, handleDrawingTypeChange]);

  // 이미지 목록 로드 (메인 이미지 포함)
  const loadImageData = useCallback(async () => {
    if (!currentSession) return;
    setIsLoadingImages(true);
    setImageError(null);
    try {
      const imageList = await sessionApi.listImages(currentSession.session_id);

      // 세션의 메인 이미지를 첫 번째 항목으로 추가 (세션 생성 시 업로드된 이미지)
      const mainImage: ImageWithGT = {
        image_id: 'main',  // 특별한 ID로 메인 이미지 구분
        filename: currentSession.filename,
        file_path: '',
        review_status: 'processed',
        detections: [],
        detection_count: 0,
        verified_count: 0,
        approved_count: 0,
        rejected_count: 0,
        order_index: 0,
        has_gt: false,  // TODO: 실제 GT 상태 확인
      };

      // 메인 이미지 + 추가 이미지 목록 (GT 상태 포함)
      const imagesWithGT: ImageWithGT[] = imageList.map(img => ({
        ...img,
        has_gt: (img as ImageWithGT).has_gt || false,
        gt_filename: (img as ImageWithGT).gt_filename,
      }));

      setImages([mainImage, ...imagesWithGT]);
    } catch (err) {
      console.error('Failed to load images:', err);
      setImageError('이미지 목록 로드 실패');
    } finally {
      setIsLoadingImages(false);
    }
  }, [currentSession]);

  // GT 파일 업로드 핸들러
  const handleGTUpload = useCallback(async (imageId: string, file: File) => {
    if (!onUploadGT) return;
    setUploadingGTFor(imageId);
    try {
      await onUploadGT(imageId, file);
      // GT 상태 업데이트
      setImages(prev => prev.map(img =>
        img.image_id === imageId
          ? { ...img, has_gt: true, gt_filename: file.name }
          : img
      ));
    } catch (err) {
      console.error('GT upload failed:', err);
      alert('GT 파일 업로드에 실패했습니다.');
    } finally {
      setUploadingGTFor(null);
      if (gtUploadRef.current) {
        gtUploadRef.current.value = '';
      }
    }
  }, [onUploadGT]);

  // GT 파일 선택 핸들러
  const handleGTFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>, imageId: string) => {
    const file = e.target.files?.[0];
    if (file) {
      handleGTUpload(imageId, file);
    }
  }, [handleGTUpload]);

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
        `${API_BASE_URL}/sessions/${currentSession.session_id}/images/bulk-upload`,
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
      // 업로드 후 이미지 목록 새로고침
      await loadImageData();
    } catch (error) {
      console.error('Image upload failed:', error);
      alert('이미지 업로드에 실패했습니다.');
    } finally {
      setIsUploadingImages(false);
      if (imageUploadRef.current) {
        imageUploadRef.current.value = '';
      }
    }
  }, [currentSession, onImagesAdded, loadImageData]);

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

  // 세션 변경 시 이미지 데이터 로드
  useEffect(() => {
    if (currentSession) {
      loadImageData();
    } else {
      setImages([]);
      setSelectedImageId(null);
    }
  }, [currentSession?.session_id, loadImageData]);

  // 페이지네이션 계산
  const totalPages = Math.ceil(images.length / IMAGES_PER_PAGE);
  const paginatedImages = images.slice(
    (currentPage - 1) * IMAGES_PER_PAGE,
    currentPage * IMAGES_PER_PAGE
  );

  // 페이지 변경 시 범위 확인
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [totalPages, currentPage]);

  // 이미지 선택 → 메인 화면에서 검토
  const handleSelectImage = (imageId: string) => {
    if (isMultiSelectMode) {
      // 다중 선택 모드: 체크박스 토글
      setSelectedImageIds(prev => {
        const newSet = new Set(prev);
        if (newSet.has(imageId)) {
          newSet.delete(imageId);
        } else {
          newSet.add(imageId);
        }
        // 콜백 호출
        const selectedImages = images.filter(img => newSet.has(img.image_id));
        onImagesSelect?.(Array.from(newSet), selectedImages);
        return newSet;
      });
    } else {
      // 단일 선택 모드
      setSelectedImageId(imageId);
      const image = images.find((img) => img.image_id === imageId);
      if (image) {
        onImageSelect?.(imageId, image);
      }
    }
  };

  // 전체 선택
  const handleSelectAll = () => {
    const allIds = new Set(images.map(img => img.image_id));
    setSelectedImageIds(allIds);
    onImagesSelect?.(Array.from(allIds), images);
  };

  // 전체 선택 해제
  const handleDeselectAll = () => {
    setSelectedImageIds(new Set());
    onImagesSelect?.([], []);
  };

  // 현재 페이지 전체 선택
  const handleSelectCurrentPage = () => {
    setSelectedImageIds(prev => {
      const newSet = new Set(prev);
      paginatedImages.forEach(img => newSet.add(img.image_id));
      const selectedImages = images.filter(img => newSet.has(img.image_id));
      onImagesSelect?.(Array.from(newSet), selectedImages);
      return newSet;
    });
  };

  // 다중 선택 모드 토글
  const toggleMultiSelectMode = () => {
    setIsMultiSelectMode(prev => !prev);
    if (isMultiSelectMode) {
      // 다중 선택 모드 해제 시 선택 초기화
      setSelectedImageIds(new Set());
      onImagesSelect?.([], []);
    }
  };

  const handleLoadSession = (sessionId: string) => {
    onLoadSession(sessionId);
  };

  // Export 핸들러 (JSON)
  const handleExportSession = async () => {
    if (!currentSession) return;
    setIsExporting(true);
    setShowExportMenu(false);
    try {
      await sessionApi.exportJson(currentSession.session_id, true, true);
    } catch (error) {
      console.error('Export failed:', error);
      alert('세션 백업에 실패했습니다.');
    } finally {
      setIsExporting(false);
    }
  };

  // Self-contained Export 핸들러 (배포 패키지)
  const [exportResult, setExportResult] = useState<{
    filename: string;
    fileSizeGB: string;
    importInstructions: string;
  } | null>(null);

  const handleSelfContainedExport = async () => {
    if (!currentSession) return;
    setIsExportingSelfContained(true);
    setShowExportMenu(false);
    try {
      const response = await fetch(
        `${API_BASE_URL}/export/sessions/${currentSession.session_id}/self-contained`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ include_docker: true, compress_images: true }),
        }
      );

      if (!response.ok) throw new Error('Export failed');

      const result = await response.json();
      setExportResult({
        filename: result.filename,
        fileSizeGB: (result.file_size_bytes / 1024 / 1024 / 1024).toFixed(2),
        importInstructions: result.import_instructions || '',
      });
    } catch (error) {
      console.error('Self-contained export failed:', error);
      alert('배포 패키지 생성에 실패했습니다.');
    } finally {
      setIsExportingSelfContained(false);
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

        {/* API Status per Feature - GPU 사용 API만 표시 */}
        {!sidebarCollapsed && currentSession?.features && currentSession.features.includes('symbol_detection') && (
          <div className="mt-3 space-y-1">
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

        {/* 참조 도면 유형 선택 */}
        {!sidebarCollapsed && currentSession && (
          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-purple-500" />
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">참조 도면 유형</span>
              </div>
              <button
                onClick={() => setShowRefSetManager(!showRefSetManager)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded text-gray-500 hover:text-purple-500 transition-colors"
                title="커스텀 참조 세트 관리"
              >
                <FolderPlus className="w-3.5 h-3.5" />
              </button>
            </div>
            <select
              value={effectiveDrawingType}
              onChange={(e) => handleDrawingTypeChange(e.target.value)}
              className="w-full px-2 py-1.5 text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-700 dark:text-gray-300"
            >
              <optgroup label="기본 제공">
                {DRAWING_TYPE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </optgroup>
              {referenceSets.filter(s => !s.is_builtin).length > 0 && (
                <optgroup label="커스텀 세트">
                  {referenceSets.filter(s => !s.is_builtin).map(set => (
                    <option key={set.id} value={set.id}>
                      {set.name} ({set.image_count}개)
                    </option>
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
                    <button
                      onClick={loadReferenceSets}
                      className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                      title="새로고침"
                    >
                      <RefreshCw className="w-3 h-3 text-gray-400" />
                    </button>
                  )}
                </div>

                {/* 커스텀 세트 목록 */}
                <div className="space-y-1 max-h-24 overflow-y-auto mb-2">
                  {referenceSets.filter(s => !s.is_builtin).length === 0 ? (
                    <p className="text-[10px] text-gray-400 text-center py-2">
                      업로드된 커스텀 세트가 없습니다
                    </p>
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
                        <div
                          className="flex-1 cursor-pointer"
                          onClick={() => handleDrawingTypeChange(set.id)}
                        >
                          <div className="font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                            <FolderOpen className="w-3 h-3 text-purple-500" />
                            {set.name}
                          </div>
                          <div className="text-gray-400">{set.image_count}개 이미지</div>
                        </div>
                        <button
                          onClick={() => handleDeleteRefSet(set.id, set.name)}
                          className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-gray-400 hover:text-red-500"
                          title="삭제"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* 새 세트 업로드 */}
                <div className="border-t border-gray-200 dark:border-gray-600 pt-2">
                  <div className="text-[10px] font-semibold text-gray-600 dark:text-gray-400 mb-1">새 세트 추가</div>
                  <input
                    type="text"
                    placeholder="세트 이름"
                    value={newRefSetName}
                    onChange={(e) => setNewRefSetName(e.target.value)}
                    className="w-full px-2 py-1 text-[10px] bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 rounded mb-1 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  />
                  <input
                    type="text"
                    placeholder="설명 (선택)"
                    value={newRefSetDescription}
                    onChange={(e) => setNewRefSetDescription(e.target.value)}
                    className="w-full px-2 py-1 text-[10px] bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 rounded mb-1.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  />
                  <button
                    onClick={() => refSetUploadRef.current?.click()}
                    disabled={isUploadingRefSet || !newRefSetName.trim()}
                    className="w-full flex items-center justify-center space-x-1 px-2 py-1.5 bg-purple-500 hover:bg-purple-600 text-white rounded text-[10px] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isUploadingRefSet ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>업로드 중...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-3 h-3" />
                        <span>ZIP 파일 선택</span>
                      </>
                    )}
                  </button>
                  <input
                    ref={refSetUploadRef}
                    type="file"
                    accept=".zip"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleRefSetUpload(file);
                    }}
                    className="hidden"
                  />
                  <p className="text-[9px] text-gray-400 mt-1 text-center">
                    이미지 파일명 = 클래스명
                  </p>
                </div>
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
            </div>
            {currentSession ? (
              <div className="text-sm">
                <p className="font-medium text-gray-900 dark:text-white truncate">
                  {currentSession.filename}
                </p>
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
              {/* Export 드롭다운 */}
              <div className="relative">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  disabled={!currentSession || isExporting || isExportingSelfContained}
                  className="w-full flex items-center justify-center space-x-1 px-2 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {(isExporting || isExportingSelfContained) ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Download className="w-3 h-3" />
                  )}
                  <span>Export</span>
                  <ChevronDown className="w-3 h-3" />
                </button>

                {/* 드롭다운 메뉴 */}
                {showExportMenu && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 overflow-hidden">
                    <button
                      onClick={handleExportSession}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <FileJson className="w-3.5 h-3.5 text-blue-500" />
                      <div className="text-left">
                        <div className="font-medium">세션 백업</div>
                        <div className="text-[10px] text-gray-500">JSON, 수 MB</div>
                      </div>
                    </button>
                    <button
                      onClick={handleSelfContainedExport}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors border-t border-gray-100 dark:border-gray-700"
                    >
                      <Package className="w-3.5 h-3.5 text-purple-500" />
                      <div className="text-left">
                        <div className="font-medium">배포 패키지</div>
                        <div className="text-[10px] text-gray-500">Docker 포함, 수 GB</div>
                      </div>
                    </button>
                  </div>
                )}
              </div>

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
              {/* GT 파일 업로드용 hidden input */}
              <input
                ref={gtUploadRef}
                type="file"
                accept=".txt,.json,.xml"
                onChange={(e) => uploadingGTFor && handleGTFileSelect(e, uploadingGTFor)}
                className="hidden"
              />
            </div>

            {/* 세션 이미지 목록 (간소화) */}
            {currentSession && (
              <div className="mt-3 border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
                {/* 헤더 */}
                <div
                  className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                  onClick={() => setShowImageReview(!showImageReview)}
                  title="클릭하여 이미지 목록 펼치기/접기"
                >
                  <span className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    <Images className="w-4 h-4" />
                    <span>세션 이미지</span>
                    <span className="text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full">
                      {images.length}
                    </span>
                  </span>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); loadImageData(); }}
                      disabled={isLoadingImages}
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-500 rounded"
                      title="이미지 목록 새로고침"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${isLoadingImages ? 'animate-spin' : ''}`} />
                    </button>
                    {showImageReview ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </div>
                </div>

                {showImageReview && (
                  <div className="p-2 space-y-2">
                    {/* 에러 메시지 */}
                    {imageError && (
                      <p className="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">{imageError}</p>
                    )}

                    {/* 다중 선택 컨트롤 */}
                    {images.length > 1 && (
                      <div className="flex items-center justify-between gap-1 pb-1 border-b border-gray-100 dark:border-gray-700">
                        <button
                          onClick={toggleMultiSelectMode}
                          className={`flex items-center space-x-1 px-2 py-1 rounded text-[10px] transition-colors ${
                            isMultiSelectMode
                              ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                          }`}
                          title="다중 선택 모드 토글"
                        >
                          {isMultiSelectMode ? <CheckSquare className="w-3 h-3" /> : <Square className="w-3 h-3" />}
                          <span>다중 선택</span>
                        </button>

                        {isMultiSelectMode && (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={handleSelectAll}
                              className="px-1.5 py-0.5 text-[9px] bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-900"
                              title="전체 선택"
                            >
                              전체
                            </button>
                            <button
                              onClick={handleSelectCurrentPage}
                              className="px-1.5 py-0.5 text-[9px] bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-900"
                              title="현재 페이지 선택"
                            >
                              페이지
                            </button>
                            <button
                              onClick={handleDeselectAll}
                              className="px-1.5 py-0.5 text-[9px] bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                              title="선택 해제"
                            >
                              해제
                            </button>
                          </div>
                        )}

                        {isMultiSelectMode && selectedImageIds.size > 0 && (
                          <span className="text-[9px] text-blue-600 dark:text-blue-400 font-medium">
                            {selectedImageIds.size}개
                          </span>
                        )}
                      </div>
                    )}

                    {/* 이미지 목록 */}
                    {isLoadingImages && images.length === 0 ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                      </div>
                    ) : images.length === 0 ? (
                      <div className="text-center py-3 text-gray-400">
                        <Images className="w-6 h-6 mx-auto mb-1 opacity-50" />
                        <p className="text-xs">이미지가 없습니다</p>
                        <p className="text-[10px] mt-0.5">아래에서 이미지/ZIP을 추가하세요</p>
                      </div>
                    ) : (
                      <div className="space-y-1 max-h-48 overflow-y-auto">
                        {paginatedImages.map((image, index) => {
                          const globalIndex = (currentPage - 1) * IMAGES_PER_PAGE + index;
                          const isMainImage = image.image_id === 'main';
                          const isSelected = isMultiSelectMode
                            ? selectedImageIds.has(image.image_id)
                            : selectedImageId === image.image_id || (selectedImageId === null && isMainImage);
                          return (
                            <div
                              key={image.image_id}
                              className={`flex items-center space-x-2 p-2 rounded-lg cursor-pointer transition-all ${
                                isSelected
                                  ? 'bg-blue-100 dark:bg-blue-900/40 border-2 border-blue-400 shadow-sm'
                                  : 'hover:bg-gray-100 dark:hover:bg-gray-700 border-2 border-transparent'
                              }`}
                              onClick={() => handleSelectImage(image.image_id)}
                              title={isMainImage
                                ? '세션 생성 시 업로드된 원본 이미지입니다'
                                : `클릭하여 "${image.filename}" 이미지를 ${isMultiSelectMode ? '선택/해제' : '메인 화면에서 검토'}합니다`}
                            >
                              {/* 다중 선택 모드: 체크박스 */}
                              {isMultiSelectMode ? (
                                <div className={`w-5 h-5 flex items-center justify-center rounded border-2 transition-colors ${
                                  isSelected
                                    ? 'bg-blue-500 border-blue-500 text-white'
                                    : 'border-gray-300 dark:border-gray-500 bg-white dark:bg-gray-700'
                                }`}>
                                  {isSelected && <CheckCircle className="w-3.5 h-3.5" />}
                                </div>
                              ) : isMainImage ? (
                                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                  isSelected
                                    ? 'bg-green-500 text-white'
                                    : 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300'
                                }`}>
                                  원본
                                </span>
                              ) : (
                                <span className={`w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-bold ${
                                  isSelected
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                                }`}>
                                  {globalIndex}
                                </span>
                              )}
                              {/* 썸네일 */}
                              <div className="w-8 h-8 rounded bg-gray-200 dark:bg-gray-600 overflow-hidden flex-shrink-0">
                                {image.thumbnail_base64 ? (
                                  <img
                                    src={`data:image/jpeg;base64,${image.thumbnail_base64}`}
                                    alt={image.filename}
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center">
                                    <Images className="w-3 h-3 text-gray-400" />
                                  </div>
                                )}
                              </div>
                              {/* 파일명 */}
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                                  {image.filename}
                                </p>
                                <div className="flex items-center gap-1 text-[10px]">
                                  {image.detection_count > 0 && (
                                    <span className="text-gray-400">
                                      {image.detection_count}개
                                    </span>
                                  )}
                                  {/* GT 상태 표시 */}
                                  {(image as ImageWithGT).has_gt ? (
                                    <span className="flex items-center gap-0.5 px-1.5 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 rounded" title={`GT: ${(image as ImageWithGT).gt_filename}`}>
                                      <Link2 className="w-3 h-3" />
                                      GT
                                    </span>
                                  ) : (
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setUploadingGTFor(image.image_id);
                                        gtUploadRef.current?.click();
                                      }}
                                      disabled={uploadingGTFor === image.image_id}
                                      className="flex items-center gap-0.5 px-1.5 py-0.5 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50 rounded transition-colors"
                                      title="GT 라벨 업로드 (.txt, .json, .xml)"
                                    >
                                      {uploadingGTFor === image.image_id ? (
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                      ) : (
                                        <Upload className="w-3 h-3" />
                                      )}
                                      GT
                                    </button>
                                  )}
                                </div>
                              </div>
                              {/* 선택 표시 (단일 선택 모드에서만) */}
                              {!isMultiSelectMode && isSelected && (
                                <CheckCircle className="w-4 h-4 text-blue-500 flex-shrink-0" />
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* 페이지네이션 (20개 이상일 때 표시) */}
                    {images.length > IMAGES_PER_PAGE && (
                      <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700">
                        <button
                          onClick={() => setCurrentPage(1)}
                          disabled={currentPage === 1}
                          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                          title="첫 페이지"
                        >
                          <ChevronsLeft className="w-3.5 h-3.5 text-gray-500" />
                        </button>
                        <button
                          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                          title="이전 페이지"
                        >
                          <ChevronLeft className="w-3.5 h-3.5 text-gray-500" />
                        </button>

                        <div className="flex items-center space-x-1">
                          <input
                            type="number"
                            min={1}
                            max={totalPages}
                            value={currentPage}
                            onChange={(e) => {
                              const page = Math.max(1, Math.min(totalPages, parseInt(e.target.value) || 1));
                              setCurrentPage(page);
                            }}
                            className="w-8 h-5 text-center text-[10px] border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                          />
                          <span className="text-[10px] text-gray-500">/ {totalPages}</span>
                        </div>

                        <button
                          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                          title="다음 페이지"
                        >
                          <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
                        </button>
                        <button
                          onClick={() => setCurrentPage(totalPages)}
                          disabled={currentPage === totalPages}
                          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                          title="마지막 페이지"
                        >
                          <ChevronsRight className="w-3.5 h-3.5 text-gray-500" />
                        </button>
                      </div>
                    )}

                    {/* 이미지 추가 영역 */}
                    <div
                      className={`p-2 rounded border-2 border-dashed transition-colors ${
                        isDragging
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                      }`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                    >
                      <button
                        onClick={() => imageUploadRef.current?.click()}
                        disabled={isUploadingImages}
                        className="w-full flex items-center justify-center space-x-2 px-2 py-1.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {isUploadingImages ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>업로드 중...</span>
                          </>
                        ) : (
                          <>
                            <ImagePlus className="w-3.5 h-3.5" />
                            <span>이미지 추가</span>
                          </>
                        )}
                      </button>
                      <p className="mt-1 text-[9px] text-center text-gray-400">
                        <FileArchive className="w-2.5 h-2.5 inline mr-0.5" />
                        드래그 앤 드롭 (이미지/ZIP)
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
                  </div>
                )}
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
                    <p className="text-xs text-gray-500">
                      {session.features && session.features.length > 0
                        ? session.features.map(f => FEATURE_NAMES[f] || f).join(' · ')
                        : `${session.detection_count}개 검출`}
                    </p>
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

          {/* 분석 실행 (간소화) */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            {/* 활성화된 기능 표시 (읽기전용) */}
            {currentSession?.features && currentSession.features.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Settings className="w-4 h-4 text-gray-500" />
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">활성화된 기능</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full">
                    Builder
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {currentSession.features.map((feature) => (
                    <span
                      key={feature}
                      className="text-[10px] px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full"
                    >
                      {FEATURE_NAMES[feature] || feature}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 분석 실행 버튼 */}
            <button
              onClick={onRunAnalysis}
              disabled={isLoading || !currentSession}
              className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
              title="Builder에서 설정된 워크플로우로 분석을 실행합니다"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>분석 중...</span>
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  <span>분석 실행</span>
                </>
              )}
            </button>

            {/* 세션 없을 때 안내 */}
            {!currentSession && (
              <p className="mt-2 text-[10px] text-center text-gray-400">
                세션을 선택하거나 이미지를 업로드하세요
              </p>
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

      {/* Export 결과 모달 */}
      {exportResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
            <div className="p-4 bg-green-500 text-white flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Package className="w-5 h-5" />
                <span className="font-semibold">배포 패키지 생성 완료</span>
              </div>
              <button onClick={() => setExportResult(null)} className="hover:bg-green-600 rounded p-1">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* 파일 정보 */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <div className="text-sm text-gray-600 dark:text-gray-400">생성된 파일</div>
                <div className="font-mono text-sm mt-1 text-gray-900 dark:text-white break-all">{exportResult.filename}</div>
                <div className="text-xs text-gray-500 mt-1">크기: {exportResult.fileSizeGB} GB</div>
              </div>

              {/* Import 가이드 */}
              <div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">📦 새 환경에서 Import 방법</div>
                <div className="bg-gray-900 text-green-400 rounded-lg p-3 font-mono text-xs space-y-1 overflow-x-auto">
                  <div className="text-gray-500"># 1. 패키지 압축 해제</div>
                  <div>unzip {exportResult.filename}</div>
                  <div className="text-gray-500 mt-2"># 2. Import 스크립트 실행</div>
                  <div>chmod +x scripts/import.sh</div>
                  <div>./scripts/import.sh</div>
                  <div className="text-gray-500 mt-2"># 3. 서비스 확인</div>
                  <div>cd docker && docker-compose ps</div>
                </div>
              </div>

              {/* 포트 정보 */}
              <div className="text-xs text-gray-600 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                <div className="font-semibold text-blue-700 dark:text-blue-300 mb-1">💡 접속 정보</div>
                <div>• 포트 오프셋: +10000 (예: 5020 → 15020)</div>
                <div>• UI 접속: http://localhost:13000</div>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 flex justify-end">
              <button
                onClick={() => setExportResult(null)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                확인
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
