/**
 * Workflow Page - Streamlit 스타일 단일 페이지 레이아웃
 * 모든 섹션을 한 페이지에 표시
 *
 * 리팩토링: 2025-12-26
 * - useWorkflowState: 상태 관리 중앙화
 * - useWorkflowEffects: 사이드 이펙트 중앙화
 * - 섹션 컴포넌트: UI 모듈화
 */

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import { detectionApi, systemApi, groundTruthApi, sessionApi } from '../lib/api';
import type { SessionImage } from '../types';
import logger from '../lib/logger';
import { API_BASE_URL } from '../lib/constants';
import type { VerificationStatus } from '../types';
import { ReferencePanel } from '../components/ReferencePanel';
import { ZoomableImage } from '../components/ZoomableImage';
import { InfoTooltip } from '../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../components/tooltipContent';

// Workflow 모듈 (리팩토링된 섹션)
import {
  // Types
  type Dimension,
  // Config
  getSectionVisibility,
  validateFeatureDependencies,
  ITEMS_PER_PAGE,
  // Hooks
  useWorkflowState,
  useWorkflowEffects,
  useLongTermFeatures,
  useMidTermFeatures,
  useAnalysisHandlers,
  useDimensionHandlers,
  useGDTHandlers,
  useRelationHandlers,
  useTitleBlockHandlers,
  usePIDFeaturesHandlers,
  // Components
  WorkflowSidebar,
  ImageModal,
  // Sections
  LongTermSection,
  MidTermSection,
  TitleBlockSection,
  ConnectivitySection,
  GDTSection,
  DimensionSection,
  LineDetectionSection,
  RelationSection,
  SymbolVerificationSection,
  DetectionResultsSection,
  FinalResultsSection,
  BOMSection,
  ActiveFeaturesSection,
  VLMClassificationSection,
  PIDFeaturesSection,
  TableExtractionSection,
  BmtWorkflowSection,
  // GTComparisonSection - GT 관리 기능이 DetectionResultsSection에 통합됨
} from './workflow';

export function WorkflowPage() {
  // URL Parameters
  const [searchParams, setSearchParams] = useSearchParams();
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
    loadImage,
    deleteSession,
    verifyDetection,
    deleteDetection,
    approveAll,
    rejectAll,
    generateBOM,
    clearError,
    reset,
  } = useSessionStore();

  // Multi-image session state (Phase 2C)
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [selectedImageAnalyzed, setSelectedImageAnalyzed] = useState(false);
  const [sessionImageCount, setSessionImageCount] = useState(0);

  // 참조 도면 유형 (사용자 오버라이드)
  const [userDrawingType, setUserDrawingType] = useState<string | null>(null);
  // drawingZoom은 ZoomableImage 컴포넌트 내부에서 관리

  // BOM ↔ 도면 하이라이트 연동 (P2-2)
  const [bomHighlightClass, setBomHighlightClass] = useState<string | null>(null);

  // 이미지를 새 팝업 창에서 확대 보기
  const openImagePopup = useCallback((imgSrc: string, title = '도면 확대') => {
    const popup = window.open('', '_blank', 'width=1400,height=900,scrollbars=yes,resizable=yes');
    if (popup) {
      popup.document.write(`<!DOCTYPE html><html><head><title>${title}</title></head><body style="margin:0;background:#111;display:flex;align-items:center;justify-content:center;min-height:100vh"><img src="${imgSrc}" style="max-width:100%;max-height:100vh;object-fit:contain"/></body></html>`);
      popup.document.close();
    }
  }, []);

  // 치수 오버레이가 포함된 이미지를 새 팝업 창에서 확대 보기
  const openOverlayPopup = useCallback((imgSrc: string, dims: Dimension[], title = '치수 오버레이') => {
    const STATUS_COLORS: Record<string, string> = {
      pending: '#eab308', approved: '#22c55e', rejected: '#ef4444',
      modified: '#3b82f6', manual: '#a855f7',
    };
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.drawImage(img, 0, 0);

      for (const dim of dims) {
        const { x1, y1, x2, y2 } = dim.bbox;
        const w = x2 - x1;
        const h = y2 - y1;
        const color = STATUS_COLORS[dim.verification_status] || STATUS_COLORS.pending;

        // 반투명 채우기
        ctx.globalAlpha = 0.18;
        ctx.fillStyle = color;
        ctx.fillRect(x1, y1, w, h);
        ctx.globalAlpha = 1;

        // 테두리
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(x1, y1, w, h);

        // 라벨 (원본 해상도 기준 크기)
        const label = dim.modified_value || dim.value;
        const fontSize = Math.max(28, Math.round(img.naturalHeight * 0.012));
        ctx.font = `bold ${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        const tw = ctx.measureText(label).width;
        const lh = fontSize + 4;
        ctx.fillStyle = color;
        ctx.fillRect(x1 + w / 2 - tw / 2 - 6, y1 - lh - 2, tw + 12, lh);
        ctx.fillStyle = '#fff';
        ctx.fillText(label, x1 + w / 2, y1 - 8);
      }
      ctx.textAlign = 'start'; // reset

      const dataUrl = canvas.toDataURL('image/png');
      const popup = window.open('', '_blank', 'width=1400,height=900,scrollbars=yes,resizable=yes');
      if (popup) {
        popup.document.write(`<!DOCTYPE html><html><head><title>${title}</title></head><body style="margin:0;background:#111;display:flex;align-items:center;justify-content:center;min-height:100vh"><img src="${dataUrl}" style="max-width:100%;max-height:100vh;object-fit:contain"/></body></html>`);
        popup.document.close();
      }
    };
    img.src = imgSrc;
  }, []);

  // 세션 이미지 개수 로드
  const loadSessionImageCount = useCallback(async () => {
    if (!currentSession) {
      setSessionImageCount(0);
      return;
    }
    try {
      const progress = await sessionApi.getImageProgress(currentSession.session_id);
      setSessionImageCount(progress.total_images);
    } catch (err) {
      logger.error('Failed to load image count:', err);
    }
  }, [currentSession]);

  // Centralized state management
  const state = useWorkflowState();

  // Side effects
  const { reloadGTComparison } = useWorkflowEffects({
    state,
    currentSession,
    detections,
    imageSize,
    loadSessions,
    loadSession,
    urlSessionId,
  });

  // Load image count when session changes
  useEffect(() => {
    loadSessionImageCount();
  }, [loadSessionImageCount]);

  // Feature hooks
  const midTermFeatures = useMidTermFeatures();
  const longTermFeatures = useLongTermFeatures();
  const pidFeatures = usePIDFeaturesHandlers();

  // Handler hooks
  const analysisHandlers = useAnalysisHandlers({
    sessionId: currentSession?.session_id,
    selectedImageId,
    setIsAnalyzing: state.setIsRunningAnalysis,
    setAnalysisOptions: () => {},
    setLines: state.setLines,
    setIntersections: state.setIntersections,
    setConnectivity: state.setConnectivityData,
    loadSession,
    loadImage,
    setDimensions: state.setDimensions,
    setDimensionStats: state.setDimensionStats,
    setRelations: state.setRelations,
    setRelationStats: state.setRelationStats,
  });

  const dimensionHandlers = useDimensionHandlers({
    sessionId: currentSession?.session_id,
    setDimensions: state.setDimensions,
    setDimensionStats: state.setDimensionStats,
  });

  const gdtHandlers = useGDTHandlers({
    sessionId: currentSession?.session_id,
    setGdtFcfList: state.setFcfList,
    setGdtDatums: state.setGdtDatums,
    setGdtSummary: state.setGdtSummary,
  });

  const relationHandlers = useRelationHandlers({
    sessionId: currentSession?.session_id,
    setRelations: state.setRelations,
    setRelationStats: state.setRelationStats,
  });

  const titleBlockHandlers = useTitleBlockHandlers({
    sessionId: currentSession?.session_id,
    setTitleBlockData: state.setTitleBlockData,
    editingTitleBlock: state.editingTitleBlock,
    setEditingTitleBlock: state.setEditingTitleBlock,
  });

  // Derived values
  const links = useMemo(() => {
    return state.dimensions
      .filter((d: Dimension) => d.linked_to)
      .map((d: Dimension) => ({ dimension_id: d.id, symbol_id: d.linked_to! }));
  }, [state.dimensions]);

  const stats = useMemo(() => {
    const total = detections.length;
    const approved = detections.filter(d => d.verification_status === 'approved').length;
    const rejected = detections.filter(d => d.verification_status === 'rejected').length;
    const pending = detections.filter(d => d.verification_status === 'pending').length;
    const manual = detections.filter(d => d.verification_status === 'manual').length;
    return { total, approved, rejected, pending, manual };
  }, [detections]);

  const effectiveDrawingType = useMemo(() => {
    // 1. 사용자가 사이드바에서 수동 선택한 경우 우선
    if (userDrawingType && userDrawingType !== 'auto') {
      return userDrawingType;
    }
    // 2. 세션에 지정된 경우
    if (currentSession?.drawing_type && currentSession.drawing_type !== 'auto') {
      return currentSession.drawing_type;
    }
    // 3. VLM 분류 결과
    if (state.classification?.drawing_type) {
      return state.classification.drawing_type;
    }
    return 'auto';
  }, [userDrawingType, currentSession?.drawing_type, state.classification?.drawing_type]);

  const effectiveFeatures = useMemo(() => {
    if (currentSession?.features && currentSession.features.length > 0) {
      return currentSession.features;
    }
    return undefined;
  }, [currentSession?.features]);

  // Pagination
  const totalPages = Math.ceil(detections.length / ITEMS_PER_PAGE);
  const paginatedDetections = useMemo(() => {
    const start = (state.currentPage - 1) * ITEMS_PER_PAGE;
    return detections.slice(start, start + ITEMS_PER_PAGE);
  }, [detections, state.currentPage]);

  // Handlers
  const handleVerify = useCallback(async (detectionId: string, status: VerificationStatus, modifiedClassName?: string) => {
    if (!currentSession) return;
    try {
      await verifyDetection(detectionId, status, modifiedClassName);
    } catch (err) {
      logger.error('Verification failed:', err);
    }
  }, [currentSession, verifyDetection]);

  const handleGenerateBOM = useCallback(async () => {
    if (!currentSession) return;
    try {
      await generateBOM();
    } catch (err) {
      logger.error('BOM generation failed:', err);
    }
  }, [currentSession, generateBOM]);

  const handleClearCache = useCallback(async (cacheType: 'all' | 'memory') => {
    state.setIsClearingCache(true);
    try {
      await systemApi.clearCache(cacheType);
    } catch (err) {
      logger.error('Cache clear failed:', err);
    } finally {
      state.setIsClearingCache(false);
    }
  }, [state]);

  const handleNewSession = useCallback(() => {
    reset();
    state.setGtCompareResult(null);
    state.setCurrentPage(1);
    state.setDimensions([]);
    state.setDimensionStats(null);
    state.setSelectedDimensionId(null);
    state.setLines([]);
    state.setIntersections([]);
  }, [reset, state]);

  const handleAddManualDetection = useCallback(async (box: { x1: number; y1: number; x2: number; y2: number }) => {
    if (!state.manualLabel.class_name) {
      alert('클래스를 먼저 선택해주세요!');
      return;
    }
    if (!currentSession) return;
    try {
      await detectionApi.addManual(currentSession.session_id, {
        class_name: state.manualLabel.class_name,
        bbox: box,
      });
      await loadSession(currentSession.session_id);
    } catch (error) {
      logger.error('Failed to add manual detection:', error);
      alert('수작업 라벨 추가 실패');
    }
  }, [state.manualLabel.class_name, currentSession, loadSession]);

  const handleLoadSessionWithGTReset = useCallback((sessionId: string) => {
    loadSession(sessionId);
    state.setGtCompareResult(null);
    // URL 업데이트 (세션 이동 시)
    setSearchParams({ session: sessionId });
  }, [loadSession, state, setSearchParams]);

  // 다중 이미지 세션에서 이미지 선택 핸들러 (Phase 2C)
  const handleImageSelect = useCallback(async (imageId: string, image: SessionImage) => {
    if (!currentSession) return;
    setSelectedImageId(imageId);
    // 서브이미지 분석 여부: dimension_count 또는 detection_count로 판단
    const isImageAnalyzed = imageId === 'main'
      ? false  // 메인은 세션 status로 판단
      : (image.dimension_count ?? 0) > 0 || image.detection_count > 0;
    setSelectedImageAnalyzed(isImageAnalyzed);
    try {
      if (imageId === 'main') {
        // 'main'은 세션 생성 시 업로드된 메인 이미지
        await loadSession(currentSession.session_id);
        logger.info('Main session image loaded');
      } else {
        // 추가 업로드된 이미지
        await loadImage(currentSession.session_id, imageId);
        logger.info('Image loaded:', image.filename);
      }
    } catch (err) {
      logger.error('Failed to load image:', err);
    }
  }, [currentSession, loadSession, loadImage]);

  // 이미지별 GT 파일 업로드 핸들러
  const handleUploadGTForImage = useCallback(async (imageId: string, file: File) => {
    if (!currentSession || !imageSize) return;
    try {
      // GT 파일을 이미지 파일명과 연결하여 업로드
      const imageName = imageId === 'main' ? currentSession.filename : `image_${imageId}`;
      await groundTruthApi.upload(file, imageName, imageSize.width, imageSize.height);
      logger.info('GT uploaded for image:', imageId, file.name);

      // GT 업로드 후 자동 비교 실행
      await reloadGTComparison();
    } catch (err) {
      logger.error('GT upload failed:', err);
      throw err;
    }
  }, [currentSession, imageSize, reloadGTComparison]);

  // 참조 도면 유형 변경 핸들러
  const handleDrawingTypeChange = useCallback((newType: string) => {
    setUserDrawingType(newType === 'auto' ? null : newType);
    logger.info('Drawing type changed to:', newType);
  }, []);

  // Section visibility
  const visibility = getSectionVisibility(effectiveDrawingType, effectiveFeatures);

  // Feature dependency validation
  const dependencyValidation = useMemo(() => {
    if (!effectiveFeatures || effectiveFeatures.length === 0) {
      return { valid: true, warnings: [] };
    }
    return validateFeatureDependencies(effectiveFeatures);
  }, [effectiveFeatures]);

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      <WorkflowSidebar
        sidebarCollapsed={state.sidebarCollapsed}
        setSidebarCollapsed={state.setSidebarCollapsed}
        darkMode={state.darkMode}
        setDarkMode={state.setDarkMode}
        gpuStatus={state.gpuStatus}
        currentSession={currentSession}
        sessions={sessions}
        projectId={currentSession?.project_id}
        detectionCount={detections.length}
        sessionImageCount={sessionImageCount}
        onImagesAdded={loadSessionImageCount}
        onImageSelect={handleImageSelect}
        onExportReady={() => logger.info('All images reviewed, export ready')}
        onNewSession={handleNewSession}
        onLoadSession={handleLoadSessionWithGTReset}
        onDeleteSession={deleteSession}
        onClearCache={handleClearCache}
        onRunAnalysis={analysisHandlers.handleRunAnalysis}
        drawingType={effectiveDrawingType}
        onDrawingTypeChange={handleDrawingTypeChange}
        onUploadGT={handleUploadGTForImage}
        isLoading={isLoading}
        isClearingCache={state.isClearingCache}
      />

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

          {/* Feature Dependency Warnings */}
          {!dependencyValidation.valid && dependencyValidation.warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 dark:bg-amber-900/20 dark:border-amber-700 rounded-lg px-4 py-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-medium text-amber-800 dark:text-amber-300 mb-1">
                    ⚠️ Feature 의존성 경고
                  </h4>
                  <ul className="text-sm text-amber-700 dark:text-amber-400 space-y-1">
                    {dependencyValidation.warnings.map((warning, index) => (
                      <li key={index} className="flex items-start gap-1">
                        <span className="text-amber-500">•</span>
                        <span>{warning.message}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="text-xs text-amber-600 dark:text-amber-500 mt-2">
                    💡 Builder에서 필수 기능을 추가하거나, 위 기능의 결과가 제한될 수 있습니다.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Title */}
          <div className="text-center mb-2">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🎯 AI 기반 BOM 추출 결과</h1>
            {currentSession && (
              <p className="text-sm text-gray-500 mt-1">📄 {currentSession.filename}</p>
            )}
          </div>

          {/* BMT 도면-BOM 교차검증 — Human-in-the-Loop 워크플로우 */}
          {currentSession && (
            <BmtWorkflowSection
              sessionId={currentSession.session_id}
              apiBaseUrl={API_BASE_URL}
            />
          )}

          {/* 원본 도면 */}
          {imageData && imageSize && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1">
                📐 원본 도면
                <InfoTooltip content={FEATURE_TOOLTIPS.referenceDrawing.description} position="right" />
              </h2>
              <ZoomableImage
                src={imageData}
                alt="원본 도면"
                initialZoom={50}
                minZoom={10}
                maxZoom={200}
                onFullscreen={() => openImagePopup(imageData, '원본 도면')}
              />
            </section>
          )}

          {/* 다중 이미지 검토 (Phase 2C) - 사이드바로 이동됨 */}

          {/* 도면 정보: 사이드바 "참조 도면 유형" 드롭다운으로 통합, DrawingInfoSection 제거 */}

          {/* 활성화된 기능 */}
          {effectiveFeatures && effectiveFeatures.length > 0 && (
            <ActiveFeaturesSection
              features={effectiveFeatures}
              onRunAnalysis={analysisHandlers.handleRunAnalysis}
              isLoading={isLoading}
              sessionStatus={currentSession?.status}
              selectedImageId={selectedImageId}
              imageAnalyzed={selectedImageAnalyzed}
            />
          )}

          {/* VLM 도면 분류 */}
          {currentSession && imageData && (!currentSession.drawing_type || currentSession.drawing_type === 'auto') && !effectiveFeatures && (
            <VLMClassificationSection
              sessionId={currentSession.session_id}
              imageBase64={imageData.replace(/^data:image\/[a-z]+;base64,/, '')}
              apiBaseUrl={API_BASE_URL}
              showClassifier={state.showClassifier}
              classification={state.classification}
              onClassificationComplete={state.setClassification}
              onPresetApply={() => {
                state.setShowAnalysisOptions(true);
                // 프리셋 적용 후 세션 새로고침 (features 반영)
                if (currentSession?.session_id) {
                  loadSession(currentSession.session_id);
                }
              }}
              onShowClassifierChange={state.setShowClassifier}
            />
          )}

          {/* AI 검출 결과 (GT 관리 통합) - symbol_detection 활성화 시만 표시 */}
          {detections.length > 0 && visibility.symbolDetection && (
            <DetectionResultsSection
              detections={detections}
              imageData={imageData}
              imageSize={imageSize}
              gtCompareResult={state.gtCompareResult}
              stats={stats}
            />
          )}

          {/* GT 비교 섹션 - GT 미로드 상태에서만 표시 (통합으로 인해 숨김 처리)
              Note: GT 관리 기능이 DetectionResultsSection에 통합되어 이 섹션은 더 이상 필요하지 않음
          */}

          {/* 심볼 검증 - symbol_detection 활성화 시만 표시 */}
          {detections.length > 0 && visibility.symbolDetection && (
            <SymbolVerificationSection
              detections={detections}
              paginatedDetections={paginatedDetections}
              imageData={imageData}
              imageSize={imageSize}
              availableClasses={state.availableClasses}
              classExamples={state.classExamples}
              gtCompareResult={state.gtCompareResult}
              currentPage={state.currentPage}
              totalPages={totalPages}
              itemsPerPage={ITEMS_PER_PAGE}
              setCurrentPage={state.setCurrentPage}
              stats={stats}
              showGTImages={state.showGTImages}
              setShowGTImages={state.setShowGTImages}
              showRefImages={state.showRefImages}
              setShowRefImages={state.setShowRefImages}
              showManualLabel={state.showManualLabel}
              setShowManualLabel={state.setShowManualLabel}
              manualLabel={state.manualLabel}
              setManualLabel={state.setManualLabel}
              verificationFinalized={state.verificationFinalized}
              setVerificationFinalized={state.setVerificationFinalized}
              onApproveAll={approveAll}
              onRejectAll={rejectAll}
              onVerify={handleVerify}
              onDelete={deleteDetection}
              onAddManualDetection={handleAddManualDetection}
              isLoading={isLoading}
            />
          )}

          {/* 치수 OCR */}
          {state.dimensions.length > 0 && currentSession && visibility.dimensionOCR && (
            <DimensionSection
              sessionId={currentSession.session_id}
              dimensions={state.dimensions}
              dimensionStats={state.dimensionStats}
              selectedDimensionId={state.selectedDimensionId}
              setSelectedDimensionId={state.setSelectedDimensionId}
              imageData={imageData}
              imageSize={imageSize}
              isRunningAnalysis={state.isRunningAnalysis}
              onVerify={dimensionHandlers.handleDimensionVerify}
              onEdit={dimensionHandlers.handleDimensionEdit}
              onDelete={dimensionHandlers.handleDimensionDelete}
              onBulkApprove={dimensionHandlers.handleBulkApproveDimensions}
              onAutoApprove={dimensionHandlers.handleAutoApprove}
              onReset={dimensionHandlers.handleResetVerification}
              isAutoApproving={dimensionHandlers.isLoading}
              onAddManualDimension={dimensionHandlers.handleAddManualDimension}
              onImagePopup={imageData ? () => openOverlayPopup(imageData, state.dimensions, '치수 OCR 오버레이') : undefined}
            />
          )}

          {/* 테이블 추출 결과 */}
          {currentSession && visibility.tableExtraction && (
            <TableExtractionSection
              sessionId={currentSession.session_id}
              apiBaseUrl={API_BASE_URL}
            />
          )}

          {/* 치수 전용 검증 완료 (심볼 검출 없는 워크플로우) */}
          {state.dimensions.length > 0 && !visibility.symbolDetection && currentSession && visibility.dimensionOCR && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">검증 진행 상황</h2>
                  <p className="text-sm text-gray-500 mt-1">
                    {state.dimensionStats
                      ? `전체 ${state.dimensions.length}개 중 ${state.dimensionStats.approved + (state.dimensionStats.modified || 0) + (state.dimensionStats.manual || 0)}개 승인됨`
                      : '치수 검증을 진행해주세요'}
                  </p>
                </div>
                <button
                  onClick={() => state.setVerificationFinalized(!state.verificationFinalized)}
                  className={`px-6 py-2 rounded-lg font-bold ${
                    state.verificationFinalized
                      ? 'bg-green-500 text-white'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {state.verificationFinalized ? 'V 검증 완료됨' : '검증 완료'}
                </button>
              </div>
              {state.dimensionStats && (
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
                      style={{
                        width: `${Math.round(((state.dimensionStats.approved + (state.dimensionStats.modified || 0) + (state.dimensionStats.manual || 0)) / Math.max(state.dimensions.length, 1)) * 100)}%`
                      }}
                    />
                  </div>
                </div>
              )}
            </section>
          )}

          {/* 선 검출 */}
          {currentSession && imageData && imageSize && visibility.lineDetection && (
            <LineDetectionSection
              imageData={imageData}
              imageSize={imageSize}
              lines={state.lines}
              intersections={state.intersections}
              detections={detections}
              dimensions={state.dimensions}
              links={links}
              showLines={state.showLines}
              setShowLines={state.setShowLines}
              isRunningLineDetection={analysisHandlers.isRunningLineDetection}
              onRunLineDetection={analysisHandlers.handleRunLineDetection}
              onLinkDimensionsToSymbols={analysisHandlers.handleLinkDimensionsToSymbols}
            />
          )}

          {/* 관계 추출 */}
          {currentSession && state.dimensions.length > 0 && imageData && imageSize && visibility.relationExtraction && (
            <RelationSection
              imageData={imageData}
              imageSize={imageSize}
              relations={state.relations}
              relationStats={state.relationStats}
              dimensions={state.dimensions}
              detections={detections}
              selectedDimensionId={state.selectedDimensionId}
              setSelectedDimensionId={state.setSelectedDimensionId}
              showRelations={state.showRelations}
              setShowRelations={state.setShowRelations}
              isExtractingRelations={relationHandlers.isExtractingRelations}
              onExtractRelations={relationHandlers.handleExtractRelations}
              onManualLink={relationHandlers.handleManualLink}
              onDeleteRelation={relationHandlers.handleDeleteRelation}
            />
          )}

          {/* P&ID 연결성 */}
          {currentSession && imageData && imageSize && visibility.pidConnectivity && (
            <ConnectivitySection
              imageData={imageData}
              imageSize={imageSize}
              detections={detections}
              connectivityData={state.connectivityData}
              selectedSymbolId={state.selectedSymbolId}
              setSelectedSymbolId={state.setSelectedSymbolId}
              highlightPath={state.highlightPath}
              setHighlightPath={state.setHighlightPath}
              isAnalyzingConnectivity={analysisHandlers.isAnalyzingConnectivity}
              onAnalyzeConnectivity={analysisHandlers.handleAnalyzeConnectivity}
              onFindPath={analysisHandlers.handleFindPath}
            />
          )}

          {/* 표제란 OCR */}
          {currentSession && imageData && visibility.titleBlockOcr && (
            <TitleBlockSection
              titleBlockData={state.titleBlockData}
              editingTitleBlock={state.editingTitleBlock}
              setEditingTitleBlock={state.setEditingTitleBlock}
              isExtractingTitleBlock={titleBlockHandlers.isExtractingTitleBlock}
              onExtractTitleBlock={titleBlockHandlers.handleExtractTitleBlock}
              onUpdateTitleBlock={titleBlockHandlers.handleUpdateTitleBlock}
            />
          )}

          {/* GD&T */}
          {currentSession && imageData && imageSize && visibility.gdtParsing && (
            <GDTSection
              sessionId={currentSession.session_id}
              imageData={imageData}
              imageSize={imageSize}
              fcfList={state.fcfList}
              gdtDatums={state.gdtDatums}
              gdtSummary={state.gdtSummary}
              showGDT={state.showGDT}
              setShowGDT={state.setShowGDT}
              selectedFCFId={state.selectedFCFId}
              setSelectedFCFId={state.setSelectedFCFId}
              selectedDatumId={state.selectedDatumId}
              setSelectedDatumId={state.setSelectedDatumId}
              isParsingGDT={gdtHandlers.isParsingGDT}
              onParseGDT={gdtHandlers.handleParseGDT}
              onFCFUpdate={gdtHandlers.handleFCFUpdate}
              onFCFDelete={gdtHandlers.handleFCFDelete}
              onDatumDelete={gdtHandlers.handleDatumDelete}
            />
          )}

          {/* 중기 로드맵 기능 */}
          <MidTermSection
            sessionId={currentSession?.session_id}
            imageData={imageData}
            visibility={visibility}
            detections={detections}
            weldingResult={midTermFeatures.weldingResult}
            isParsingWelding={midTermFeatures.isParsingWelding}
            selectedWeldingId={midTermFeatures.selectedWeldingId}
            onSelectWelding={midTermFeatures.setSelectedWeldingId}
            onParseWelding={() => midTermFeatures.handleParseWelding(currentSession?.session_id || '')}
            roughnessResult={midTermFeatures.roughnessResult}
            isParsingRoughness={midTermFeatures.isParsingRoughness}
            selectedRoughnessId={midTermFeatures.selectedRoughnessId}
            onSelectRoughness={midTermFeatures.setSelectedRoughnessId}
            onParseRoughness={() => midTermFeatures.handleParseRoughness(currentSession?.session_id || '')}
            quantityResult={midTermFeatures.quantityResult}
            isExtractingQuantity={midTermFeatures.isExtractingQuantity}
            selectedQuantityId={midTermFeatures.selectedQuantityId}
            onSelectQuantity={midTermFeatures.setSelectedQuantityId}
            onExtractQuantity={() => midTermFeatures.handleExtractQuantity(currentSession?.session_id || '')}
            balloonResult={midTermFeatures.balloonResult}
            isMatchingBalloons={midTermFeatures.isMatchingBalloons}
            selectedBalloonId={midTermFeatures.selectedBalloonId}
            onSelectBalloon={midTermFeatures.setSelectedBalloonId}
            onMatchBalloons={() => midTermFeatures.handleMatchBalloons(currentSession?.session_id || '')}
            onLinkBalloon={(balloonId, symbolId) => midTermFeatures.handleLinkBalloon(currentSession?.session_id || '', balloonId, symbolId)}
          />

          {/* 장기 로드맵 기능 */}
          <LongTermSection
            currentSession={currentSession}
            imageData={imageData}
            visibility={visibility}
            sessions={sessions}
            drawingRegions={longTermFeatures.drawingRegions}
            isSegmentingRegions={longTermFeatures.isSegmentingRegions}
            selectedRegionId={longTermFeatures.selectedRegionId}
            onSelectRegion={longTermFeatures.setSelectedRegionId}
            onSegmentRegions={() => longTermFeatures.handleSegmentRegions(currentSession?.session_id || '')}
            extractedNotes={longTermFeatures.extractedNotes}
            isExtractingNotes={longTermFeatures.isExtractingNotes}
            selectedNoteId={longTermFeatures.selectedNoteId}
            onSelectNote={longTermFeatures.setSelectedNoteId}
            onExtractNotes={() => longTermFeatures.handleExtractNotes(currentSession?.session_id || '')}
            revisionChanges={longTermFeatures.revisionChanges}
            isComparingRevisions={longTermFeatures.isComparingRevisions}
            comparisonSessionId={longTermFeatures.comparisonSessionId}
            onComparisonSessionChange={longTermFeatures.setComparisonSessionId}
            onCompareRevisions={() => longTermFeatures.handleCompareRevisions(currentSession?.session_id || '', longTermFeatures.comparisonSessionId)}
            vlmClassification={longTermFeatures.vlmClassification}
            isVlmClassifying={longTermFeatures.isVlmClassifying}
            onVlmClassify={() => longTermFeatures.handleVlmClassify(currentSession?.session_id || '')}
          />

          {/* P&ID 분석 (features 기반 동적 렌더링) */}
          {(visibility.valveSignalList || visibility.equipmentList || visibility.bwmsChecklist || visibility.deviationList) && (
            <PIDFeaturesSection
              sessionId={currentSession?.session_id || null}
              visibility={visibility}
              valves={pidFeatures.valves}
              isDetectingValves={pidFeatures.isDetectingValves}
              onDetectValves={() => pidFeatures.handleDetectValves(currentSession?.session_id || '')}
              onVerifyValve={(id, status) => pidFeatures.handleVerifyValve(currentSession?.session_id || '', id, status)}
              equipment={pidFeatures.equipment}
              isDetectingEquipment={pidFeatures.isDetectingEquipment}
              onDetectEquipment={() => pidFeatures.handleDetectEquipment(currentSession?.session_id || '')}
              onVerifyEquipment={(id, status) => pidFeatures.handleVerifyEquipment(currentSession?.session_id || '', id, status)}
              checklistItems={pidFeatures.checklistItems}
              isCheckingDesign={pidFeatures.isCheckingDesign}
              onCheckDesign={() => pidFeatures.handleCheckDesign(currentSession?.session_id || '')}
              onVerifyChecklist={(id, status) => pidFeatures.handleVerifyChecklist(currentSession?.session_id || '', id, status)}
              deviations={pidFeatures.deviations}
              isAnalyzingDeviations={pidFeatures.isAnalyzingDeviations}
              onAnalyzeDeviations={() => pidFeatures.handleAnalyzeDeviations(currentSession?.session_id || '')}
              onVerifyDeviation={(id, status) => pidFeatures.handleVerifyDeviation(currentSession?.session_id || '', id, status)}
              onExport={(type) => pidFeatures.handleExport(currentSession?.session_id || '', type)}
              onExportPDF={(type) => pidFeatures.handleExportPDF(currentSession?.session_id || '', type)}
            />
          )}

          {/* 최종 결과 */}
          {state.verificationFinalized && imageData && imageSize && (
            (stats.approved + stats.manual) > 0 ||
            (state.dimensionStats && (state.dimensionStats.approved + (state.dimensionStats.modified || 0) + (state.dimensionStats.manual || 0)) > 0)
          ) && (
            <FinalResultsSection
              detections={detections}
              imageData={imageData}
              imageSize={imageSize}
              stats={stats}
              onImageClick={() => state.setShowImageModal(true)}
              selectedClassName={bomHighlightClass}
              onClassSelect={setBomHighlightClass}
              dimensions={state.dimensions}
              dimensionStats={state.dimensionStats}
            />
          )}

          {/* 이미지 모달 */}
          {state.showImageModal && imageData && imageSize && (
            <ImageModal
              imageData={imageData}
              imageSize={imageSize}
              detections={detections}
              onClose={() => state.setShowImageModal(false)}
            />
          )}

          {/* BOM 생성 */}
          {state.verificationFinalized && (detections.length > 0 || state.dimensions.length > 0) && currentSession && (
            <BOMSection
              sessionId={currentSession.session_id}
              detections={detections}
              bomData={bomData}
              stats={stats}
              dimensionStats={state.dimensionStats}
              exportFormat={state.exportFormat}
              setExportFormat={state.setExportFormat}
              onGenerateBOM={handleGenerateBOM}
              isLoading={isLoading}
              apiBaseUrl={API_BASE_URL}
              hasCustomPricing={currentSession.has_custom_pricing}
              selectedClassName={bomHighlightClass}
              onClassSelect={setBomHighlightClass}
            />
          )}
        </div>
      </main>

      {/* 심볼 참조 패널 - symbol_detection 기능이 활성화된 경우만 표시 */}
      {effectiveFeatures?.includes('symbol_detection') && (
        <ReferencePanel onClose={() => {}} drawingType={effectiveDrawingType} />
      )}
    </div>
  );
}

export default WorkflowPage;
