/**
 * Workflow Page - Streamlit 스타일 단일 페이지 레이아웃
 * 모든 섹션을 한 페이지에 표시
 *
 * 리팩토링: 2025-12-26
 * - useWorkflowState: 상태 관리 중앙화
 * - useWorkflowEffects: 사이드 이펙트 중앙화
 * - 섹션 컴포넌트: UI 모듈화
 */

import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import { detectionApi, systemApi } from '../lib/api';
import logger from '../lib/logger';
import { API_BASE_URL } from '../lib/constants';
import type { VerificationStatus } from '../types';
import { ReferencePanel } from '../components/ReferencePanel';

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
  ReferenceDrawingSection,
  DrawingInfoSection,
  ActiveFeaturesSection,
  VLMClassificationSection,
  PIDFeaturesSection,
} from './workflow';

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

  // Centralized state management
  const state = useWorkflowState();

  // Side effects
  useWorkflowEffects({
    state,
    currentSession,
    detections,
    imageSize,
    loadSessions,
    loadSession,
    urlSessionId,
  });

  // Feature hooks
  const midTermFeatures = useMidTermFeatures();
  const longTermFeatures = useLongTermFeatures();
  const pidFeatures = usePIDFeaturesHandlers();

  // Handler hooks
  const analysisHandlers = useAnalysisHandlers({
    sessionId: currentSession?.session_id,
    setIsAnalyzing: state.setIsRunningAnalysis,
    setAnalysisOptions: () => {},
    setLines: state.setLines,
    setIntersections: state.setIntersections,
    setConnectivity: state.setConnectivityData,
    loadSession,
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
    if (currentSession?.drawing_type && currentSession.drawing_type !== 'auto') {
      return currentSession.drawing_type;
    }
    if (state.classification?.drawing_type) {
      return state.classification.drawing_type;
    }
    return 'auto';
  }, [currentSession?.drawing_type, state.classification?.drawing_type]);

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
  }, [loadSession, state]);

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
        config={state.config}
        setConfig={state.setConfig}
        showSettings={state.showSettings}
        setShowSettings={state.setShowSettings}
        showAnalysisOptions={state.showAnalysisOptions}
        setShowAnalysisOptions={state.setShowAnalysisOptions}
        currentSession={currentSession}
        sessions={sessions}
        detectionCount={detections.length}
        onNewSession={handleNewSession}
        onLoadSession={handleLoadSessionWithGTReset}
        onDeleteSession={deleteSession}
        onRunDetection={runDetection}
        onClearCache={handleClearCache}
        onAnalysisOptionsChange={analysisHandlers.handleAnalysisOptionsChange}
        onRunAnalysis={analysisHandlers.handleRunAnalysis}
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

          {/* 원본 도면 */}
          {imageData && (
            <ReferenceDrawingSection
              imageData={imageData}
              imageSize={imageSize}
              detectionCount={detections.length}
              approvedCount={stats.approved}
              onImageClick={() => state.setShowImageModal(true)}
            />
          )}

          {/* 도면 정보 (빌더에서 설정한 경우) */}
          {currentSession?.drawing_type && currentSession.drawing_type !== 'auto' && (
            <DrawingInfoSection drawingType={currentSession.drawing_type} />
          )}

          {/* 활성화된 기능 */}
          {effectiveFeatures && effectiveFeatures.length > 0 && (
            <ActiveFeaturesSection features={effectiveFeatures} />
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

          {/* AI 검출 결과 */}
          {detections.length > 0 && (
            <DetectionResultsSection
              detections={detections}
              imageData={imageData}
              imageSize={imageSize}
              gtCompareResult={state.gtCompareResult}
              stats={stats}
            />
          )}

          {/* 심볼 검증 */}
          {detections.length > 0 && (
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
              setDimensions={state.setDimensions}
              setDimensionStats={state.setDimensionStats}
              showVerificationQueue={state.showVerificationQueue}
              setShowVerificationQueue={state.setShowVerificationQueue}
              imageData={imageData}
              imageSize={imageSize}
              isRunningAnalysis={state.isRunningAnalysis}
              onVerify={dimensionHandlers.handleDimensionVerify}
              onEdit={dimensionHandlers.handleDimensionEdit}
              onDelete={dimensionHandlers.handleDimensionDelete}
              onBulkApprove={dimensionHandlers.handleBulkApproveDimensions}
            />
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
          {state.verificationFinalized && imageData && imageSize && (stats.approved + stats.manual) > 0 && (
            <FinalResultsSection
              detections={detections}
              imageData={imageData}
              imageSize={imageSize}
              stats={stats}
              onImageClick={() => state.setShowImageModal(true)}
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
          {state.verificationFinalized && detections.length > 0 && currentSession && (
            <BOMSection
              sessionId={currentSession.session_id}
              detections={detections}
              bomData={bomData}
              stats={stats}
              exportFormat={state.exportFormat}
              setExportFormat={state.setExportFormat}
              onGenerateBOM={handleGenerateBOM}
              isLoading={isLoading}
              apiBaseUrl={API_BASE_URL}
            />
          )}
        </div>
      </main>

      {/* 심볼 참조 패널 */}
      <ReferencePanel onClose={() => {}} />
    </div>
  );
}

export default WorkflowPage;
