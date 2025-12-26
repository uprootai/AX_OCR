/**
 * useWorkflowState - Workflow 페이지 상태 관리 훅
 * 모든 useState 선언을 중앙화하여 관리
 */

import { useState } from 'react';
import type {
  GPUStatus,
  GTCompareResponse,
  ConnectivityResult,
  TitleBlockData,
} from '../../../lib/api';
import type { DetectionConfig, ExportFormat } from '../../../types';
import type { FeatureControlFrame, DatumFeature, GDTSummary } from '../../../components/GDTEditor';
import type { DimensionRelation, RelationStatistics } from '../../../types';
import type { Dimension, DimensionStats } from '../types/workflow';

// ==================== Type Definitions ====================

export interface ClassExample {
  class_name: string;
  image_base64: string;
}

export interface ClassificationData {
  drawing_type: string;
  confidence: number;
  suggested_preset: string;
  provider: string;
}

export interface LineData {
  id: string;
  start: { x: number; y: number };
  end: { x: number; y: number };
  length: number;
  angle: number;
  line_type: string;
  line_style: string;
  color?: string;
  confidence: number;
  thickness?: number;
}

export interface IntersectionData {
  id: string;
  point: { x: number; y: number };
  line_ids: string[];
  intersection_type?: string;
}

export interface ManualLabelState {
  class_name: string;
}

// ==================== Hook Definition ====================

export function useWorkflowState() {
  // UI State
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
    confidence: 0.4,
    iou_threshold: 0.5,
    model_id: 'yolo',
  });

  // Class examples
  const [classExamples, setClassExamples] = useState<ClassExample[]>([]);

  // GT comparison
  const [gtCompareResult, setGtCompareResult] = useState<GTCompareResponse | null>(null);
  const [isLoadingGT, setIsLoadingGT] = useState(false);
  const [showGTImages, setShowGTImages] = useState(true);
  const [showRefImages, setShowRefImages] = useState(true);

  // Manual label
  const [showManualLabel, setShowManualLabel] = useState(false);
  const [manualLabel, setManualLabel] = useState<ManualLabelState>({ class_name: '' });

  // Cache clearing
  const [isClearingCache, setIsClearingCache] = useState(false);

  // Verification finalized
  const [verificationFinalized, setVerificationFinalized] = useState(false);

  // Image modal
  const [showImageModal, setShowImageModal] = useState(false);

  // Dimension OCR
  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [dimensionStats, setDimensionStats] = useState<DimensionStats | null>(null);
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);
  const [selectedDimensionId, setSelectedDimensionId] = useState<string | null>(null);
  const [showAnalysisOptions, setShowAnalysisOptions] = useState(false);

  // Verification queue
  const [showVerificationQueue, setShowVerificationQueue] = useState(false);

  // VLM Classification
  const [classification, setClassification] = useState<ClassificationData | null>(null);
  const [showClassifier, setShowClassifier] = useState(true);

  // Line detection
  const [lines, setLines] = useState<LineData[]>([]);
  const [intersections, setIntersections] = useState<IntersectionData[]>([]);
  const [showLines, setShowLines] = useState(true);

  // P&ID connectivity
  const [connectivityData, setConnectivityData] = useState<ConnectivityResult | null>(null);
  const [selectedSymbolId, setSelectedSymbolId] = useState<string | null>(null);
  const [highlightPath, setHighlightPath] = useState<string[] | null>(null);

  // Title block OCR
  const [titleBlockData, setTitleBlockData] = useState<TitleBlockData | null>(null);
  const [editingTitleBlock, setEditingTitleBlock] = useState<Partial<TitleBlockData> | null>(null);

  // Relation extraction
  const [relations, setRelations] = useState<DimensionRelation[]>([]);
  const [relationStats, setRelationStats] = useState<RelationStatistics | null>(null);
  const [showRelations, setShowRelations] = useState(true);

  // GD&T
  const [fcfList, setFcfList] = useState<FeatureControlFrame[]>([]);
  const [gdtDatums, setGdtDatums] = useState<DatumFeature[]>([]);
  const [gdtSummary, setGdtSummary] = useState<GDTSummary | null>(null);
  const [showGDT, setShowGDT] = useState(true);
  const [selectedFCFId, setSelectedFCFId] = useState<string | null>(null);
  const [selectedDatumId, setSelectedDatumId] = useState<string | null>(null);

  return {
    // UI State
    showSettings, setShowSettings,
    currentPage, setCurrentPage,
    exportFormat, setExportFormat,
    availableClasses, setAvailableClasses,
    darkMode, setDarkMode,
    sidebarCollapsed, setSidebarCollapsed,
    gpuStatus, setGpuStatus,
    config, setConfig,

    // Class examples
    classExamples, setClassExamples,

    // GT comparison
    gtCompareResult, setGtCompareResult,
    isLoadingGT, setIsLoadingGT,
    showGTImages, setShowGTImages,
    showRefImages, setShowRefImages,

    // Manual label
    showManualLabel, setShowManualLabel,
    manualLabel, setManualLabel,

    // Cache clearing
    isClearingCache, setIsClearingCache,

    // Verification finalized
    verificationFinalized, setVerificationFinalized,

    // Image modal
    showImageModal, setShowImageModal,

    // Dimension OCR
    dimensions, setDimensions,
    dimensionStats, setDimensionStats,
    isRunningAnalysis, setIsRunningAnalysis,
    selectedDimensionId, setSelectedDimensionId,
    showAnalysisOptions, setShowAnalysisOptions,

    // Verification queue
    showVerificationQueue, setShowVerificationQueue,

    // VLM Classification
    classification, setClassification,
    showClassifier, setShowClassifier,

    // Line detection
    lines, setLines,
    intersections, setIntersections,
    showLines, setShowLines,

    // P&ID connectivity
    connectivityData, setConnectivityData,
    selectedSymbolId, setSelectedSymbolId,
    highlightPath, setHighlightPath,

    // Title block OCR
    titleBlockData, setTitleBlockData,
    editingTitleBlock, setEditingTitleBlock,

    // Relation extraction
    relations, setRelations,
    relationStats, setRelationStats,
    showRelations, setShowRelations,

    // GD&T
    fcfList, setFcfList,
    gdtDatums, setGdtDatums,
    gdtSummary, setGdtSummary,
    showGDT, setShowGDT,
    selectedFCFId, setSelectedFCFId,
    selectedDatumId, setSelectedDatumId,
  };
}

export type WorkflowState = ReturnType<typeof useWorkflowState>;
