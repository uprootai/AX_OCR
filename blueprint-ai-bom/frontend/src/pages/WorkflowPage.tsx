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
  CheckCircle,
  Ruler,
} from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import axios from 'axios';
import { detectionApi, systemApi, groundTruthApi, blueprintFlowApi, analysisApi, longtermApi } from '../lib/api';
import logger from '../lib/logger';
import { API_BASE_URL } from '../lib/constants';
import type {
  GPUStatus,
  GTCompareResponse,
  ConnectivityResult,
  TitleBlockData,
  // 중기 로드맵 기능 타입 (2025-12-24)
  WeldingParsingResult,
  SurfaceRoughnessResult,
  QuantityExtractionResult,
  BalloonMatchingResult,
  // 장기 로드맵 기능 타입 (2025-12-24)
  DrawingRegion,
  ExtractedNote,
  RevisionChange,
  VLMClassificationResult,
} from '../lib/api';

interface ClassExample {
  class_name: string;
  image_base64: string;
}
import type { VerificationStatus, DetectionConfig, ExportFormat } from '../types';
import { ReferencePanel } from '../components/ReferencePanel';
import { DrawingCanvas } from '../components/DrawingCanvas';
import { AnalysisOptions } from '../components/AnalysisOptions';
import { DimensionList } from '../components/DimensionList';
import { IntegratedOverlay } from '../components/IntegratedOverlay';
import { VerificationQueue } from '../components/VerificationQueue';
import { DrawingClassifier } from '../components/DrawingClassifier';
import { RelationList } from '../components/RelationList';
import { RelationOverlay } from '../components/RelationOverlay';
import { InfoTooltip } from '../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../components/tooltipContent';
import GDTEditor from '../components/GDTEditor';
import type { FeatureControlFrame, DatumFeature, GDTSummary } from '../components/GDTEditor';
import type { DimensionRelation, RelationStatistics } from '../types';
import { ConnectivityDiagram } from '../components/ConnectivityDiagram';

// Dimension types
interface Dimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  raw_text: string;
  unit: string | null;
  tolerance: string | null;
  dimension_type: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';
  modified_value: string | null;
  linked_to: string | null;
}

interface DimensionStats {
  pending: number;
  approved: number;
  rejected: number;
  modified: number;
  manual: number;
}

interface AnalysisOptionsData {
  enable_symbol_detection: boolean;
  enable_dimension_ocr: boolean;
  enable_line_detection: boolean;
  enable_text_extraction: boolean;
  ocr_engine: string;
  confidence_threshold: number;
  symbol_model_type: string;
  preset: string | null;
}

// 도면 타입별 섹션 가시성 설정
interface SectionVisibility {
  symbolDetection: boolean;    // 심볼 검출 (YOLO)
  dimensionOCR: boolean;       // 치수 OCR (eDOCr2)
  lineDetection: boolean;      // 선 검출
  gdtParsing: boolean;         // GD&T 기하공차
  relationExtraction: boolean; // 치수-객체 관계
  // 단기 로드맵 기능 (2025-12-24)
  pidConnectivity: boolean;    // P&ID 연결성 분석
  titleBlockOcr: boolean;      // 표제란 OCR
  // 중기 로드맵 기능 (2025-12-24)
  weldingSymbolParsing: boolean;      // 용접 기호 파싱
  surfaceRoughnessParsing: boolean;   // 표면 거칠기 파싱
  quantityExtraction: boolean;        // 수량 추출
  balloonMatching: boolean;           // 벌룬 번호 매칭
  // 장기 로드맵 기능 (2025-12-24)
  drawingRegionSegmentation: boolean; // 도면 영역 세분화
  notesExtraction: boolean;           // 주석/노트 추출
  revisionComparison: boolean;        // 리비전 비교
  vlmAutoClassification: boolean;     // VLM 자동 분류
}

const DRAWING_TYPE_SECTIONS: Record<string, SectionVisibility> = {
  // 전력 설비: 심볼만 필요
  electrical_panel: {
    symbolDetection: true,
    dimensionOCR: false,
    lineDetection: false,
    gdtParsing: false,
    relationExtraction: false,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: false,
    surfaceRoughnessParsing: false,
    quantityExtraction: false,
    balloonMatching: false,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  electrical: {
    symbolDetection: true,
    dimensionOCR: false,
    lineDetection: false,
    gdtParsing: false,
    relationExtraction: false,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: false,
    surfaceRoughnessParsing: false,
    quantityExtraction: false,
    balloonMatching: false,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  electrical_circuit: {
    symbolDetection: true,
    dimensionOCR: false,
    lineDetection: false,
    gdtParsing: false,
    relationExtraction: false,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: false,
    surfaceRoughnessParsing: false,
    quantityExtraction: false,
    balloonMatching: false,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  // 기계 부품도: 치수 + GD&T + 용접 + 표면 거칠기
  mechanical_part: {
    symbolDetection: false,
    dimensionOCR: true,
    lineDetection: false,
    gdtParsing: true,
    relationExtraction: true,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: true,
    surfaceRoughnessParsing: true,
    quantityExtraction: true,
    balloonMatching: true,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  mechanical: {
    symbolDetection: false,
    dimensionOCR: true,
    lineDetection: false,
    gdtParsing: true,
    relationExtraction: true,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: true,
    surfaceRoughnessParsing: true,
    quantityExtraction: true,
    balloonMatching: true,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  dimension: {
    symbolDetection: false,
    dimensionOCR: true,
    lineDetection: false,
    gdtParsing: false,
    relationExtraction: false,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: false,
    surfaceRoughnessParsing: true,
    quantityExtraction: false,
    balloonMatching: false,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  dimension_bom: {
    symbolDetection: false,
    dimensionOCR: true,
    lineDetection: false,
    gdtParsing: true,
    relationExtraction: true,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: true,
    surfaceRoughnessParsing: true,
    quantityExtraction: true,
    balloonMatching: true,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  // P&ID: 심볼 + 선 + 연결성
  pid: {
    symbolDetection: true,
    dimensionOCR: false,
    lineDetection: true,
    gdtParsing: false,
    relationExtraction: true,
    pidConnectivity: true,
    titleBlockOcr: true,
    weldingSymbolParsing: false,
    surfaceRoughnessParsing: false,
    quantityExtraction: true,
    balloonMatching: true,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  // 조립도: 심볼 + 치수 + 선 + 벌룬 + 수량
  assembly: {
    symbolDetection: true,
    dimensionOCR: true,
    lineDetection: true,
    gdtParsing: false,
    relationExtraction: true,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: true,
    surfaceRoughnessParsing: false,
    quantityExtraction: true,
    balloonMatching: true,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  // 건축 도면: 치수 + 선
  architectural: {
    symbolDetection: false,
    dimensionOCR: true,
    lineDetection: true,
    gdtParsing: false,
    relationExtraction: false,
    pidConnectivity: false,
    titleBlockOcr: true,
    weldingSymbolParsing: false,
    surfaceRoughnessParsing: false,
    quantityExtraction: false,
    balloonMatching: false,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  // 기본값 (auto 또는 unknown): 모두 표시
  auto: {
    symbolDetection: true,
    dimensionOCR: true,
    lineDetection: true,
    gdtParsing: true,
    relationExtraction: true,
    pidConnectivity: true,
    titleBlockOcr: true,
    weldingSymbolParsing: true,
    surfaceRoughnessParsing: true,
    quantityExtraction: true,
    balloonMatching: true,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
  unknown: {
    symbolDetection: true,
    dimensionOCR: true,
    lineDetection: true,
    gdtParsing: true,
    relationExtraction: true,
    pidConnectivity: true,
    titleBlockOcr: true,
    weldingSymbolParsing: true,
    surfaceRoughnessParsing: true,
    quantityExtraction: true,
    balloonMatching: true,
    drawingRegionSegmentation: true,
    notesExtraction: true,
    revisionComparison: true,
    vlmAutoClassification: true,
  },
};

// 섹션 가시성 헬퍼 함수 (2025-12-24: features 기반 지원 추가)
const getSectionVisibility = (drawingType: string | undefined, features?: string[]): SectionVisibility => {
  // features가 제공된 경우 features 기반 가시성 사용
  if (features && features.length > 0) {
    return {
      symbolDetection: features.includes('symbol_detection'),
      dimensionOCR: features.includes('dimension_ocr'),
      lineDetection: features.includes('line_detection'),
      gdtParsing: features.includes('gdt_parsing'),
      relationExtraction: features.includes('relation_extraction'),
      pidConnectivity: features.includes('pid_connectivity'),
      titleBlockOcr: features.includes('title_block_ocr'),
      // 중기 로드맵 기능 (2025-12-24)
      weldingSymbolParsing: features.includes('welding_symbol_parsing'),
      surfaceRoughnessParsing: features.includes('surface_roughness_parsing'),
      quantityExtraction: features.includes('quantity_extraction'),
      balloonMatching: features.includes('balloon_matching'),
      // 장기 로드맵 기능 (2025-12-24)
      drawingRegionSegmentation: features.includes('drawing_region_segmentation'),
      notesExtraction: features.includes('notes_extraction'),
      revisionComparison: features.includes('revision_comparison'),
      vlmAutoClassification: features.includes('vlm_auto_classification'),
    };
  }
  // features가 없으면 drawing_type 기반 폴백
  const type = drawingType || 'auto';
  return DRAWING_TYPE_SECTIONS[type] || DRAWING_TYPE_SECTIONS.auto;
};

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

  // Verification finalized state (검증 완료 버튼 클릭 시 true)
  const [verificationFinalized, setVerificationFinalized] = useState(false);

  // Image modal state (이미지 확대 모달)
  const [showImageModal, setShowImageModal] = useState(false);

  // Dimension OCR state
  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [dimensionStats, setDimensionStats] = useState<DimensionStats | null>(null);
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);
  const [selectedDimensionId, setSelectedDimensionId] = useState<string | null>(null);
  const [showAnalysisOptions, setShowAnalysisOptions] = useState(false);

  // Active Learning verification queue
  const [showVerificationQueue, setShowVerificationQueue] = useState(false);

  // VLM Classification (Phase 4)
  interface ClassificationData {
    drawing_type: string;
    confidence: number;
    suggested_preset: string;
    provider: string;
  }
  const [classification, setClassification] = useState<ClassificationData | null>(null);
  const [showClassifier, setShowClassifier] = useState(true);

  // Line detection state
  interface LineData {
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
  interface IntersectionData {
    id: string;
    point: { x: number; y: number };
    line_ids: string[];
    intersection_type?: string;
  }
  const [lines, setLines] = useState<LineData[]>([]);
  const [intersections, setIntersections] = useState<IntersectionData[]>([]);
  const [isRunningLineDetection, setIsRunningLineDetection] = useState(false);
  const [showLines, setShowLines] = useState(true);

  // P&ID 연결성 분석 상태 (2025-12-24)
  const [connectivityData, setConnectivityData] = useState<ConnectivityResult | null>(null);
  const [isAnalyzingConnectivity, setIsAnalyzingConnectivity] = useState(false);
  const [selectedSymbolId, setSelectedSymbolId] = useState<string | null>(null);
  const [highlightPath, setHighlightPath] = useState<string[] | null>(null);

  // 표제란 OCR 상태 (2025-12-24)
  const [titleBlockData, setTitleBlockData] = useState<TitleBlockData | null>(null);
  const [isExtractingTitleBlock, setIsExtractingTitleBlock] = useState(false);
  const [editingTitleBlock, setEditingTitleBlock] = useState<Partial<TitleBlockData> | null>(null);

  // 중기 로드맵 기능 상태 (2025-12-24)
  // 1. 용접 기호 파싱
  const [weldingResult, setWeldingResult] = useState<WeldingParsingResult | null>(null);
  const [isParsingWelding, setIsParsingWelding] = useState(false);
  const [selectedWeldingId, setSelectedWeldingId] = useState<string | null>(null);

  // 2. 표면 거칠기 파싱
  const [roughnessResult, setRoughnessResult] = useState<SurfaceRoughnessResult | null>(null);
  const [isParsingRoughness, setIsParsingRoughness] = useState(false);
  const [selectedRoughnessId, setSelectedRoughnessId] = useState<string | null>(null);

  // 3. 수량 추출
  const [quantityResult, setQuantityResult] = useState<QuantityExtractionResult | null>(null);
  const [isExtractingQuantity, setIsExtractingQuantity] = useState(false);
  const [selectedQuantityId, setSelectedQuantityId] = useState<string | null>(null);

  // 4. 벌룬 매칭
  const [balloonResult, setBalloonResult] = useState<BalloonMatchingResult | null>(null);
  const [isMatchingBalloons, setIsMatchingBalloons] = useState(false);
  const [selectedBalloonId, setSelectedBalloonId] = useState<string | null>(null);

  // Phase 2: Relation state (치수선 기반 관계 추출)
  const [relations, setRelations] = useState<DimensionRelation[]>([]);
  const [relationStats, setRelationStats] = useState<RelationStatistics | null>(null);
  const [showRelations, setShowRelations] = useState(true);
  const [isExtractingRelations, setIsExtractingRelations] = useState(false);

  // Phase 7: GD&T state (기하공차 파싱)
  const [fcfList, setFcfList] = useState<FeatureControlFrame[]>([]);
  const [gdtDatums, setGdtDatums] = useState<DatumFeature[]>([]);
  const [gdtSummary, setGdtSummary] = useState<GDTSummary | null>(null);
  const [showGDT, setShowGDT] = useState(true);
  const [isParsingGDT, setIsParsingGDT] = useState(false);
  const [selectedFCFId, setSelectedFCFId] = useState<string | null>(null);
  const [selectedDatumId, setSelectedDatumId] = useState<string | null>(null);

  // 장기 로드맵 기능 (2025-12-24)
  // 1. 도면 영역 세분화
  const [drawingRegions, setDrawingRegions] = useState<DrawingRegion[]>([]);
  const [isSegmentingRegions, setIsSegmentingRegions] = useState(false);
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);

  // 2. 주석/노트 추출
  const [extractedNotes, setExtractedNotes] = useState<ExtractedNote[]>([]);
  const [isExtractingNotes, setIsExtractingNotes] = useState(false);
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);

  // 3. 리비전 비교
  const [revisionChanges, setRevisionChanges] = useState<RevisionChange[]>([]);
  const [isComparingRevisions, setIsComparingRevisions] = useState(false);
  const [comparisonSessionId, setComparisonSessionId] = useState<string>('');

  // 4. VLM 자동 분류
  const [vlmClassification, setVlmClassification] = useState<VLMClassificationResult | null>(null);
  const [isVlmClassifying, setIsVlmClassifying] = useState(false);

  // Derive links from dimensions for IntegratedOverlay
  const links = useMemo(() => {
    return dimensions
      .filter(d => d.linked_to)
      .map(d => ({ dimension_id: d.id, symbol_id: d.linked_to! }));
  }, [dimensions]);

  // Fetch YOLO defaults from BlueprintFlow API
  useEffect(() => {
    const fetchYOLODefaults = async () => {
      const defaults = await blueprintFlowApi.getYOLODefaults();
      setConfig(prev => ({
        ...prev,
        confidence: defaults.confidence,
        iou_threshold: defaults.iou,
      }));
      logger.log('📊 BlueprintFlow YOLO defaults loaded:', defaults);
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

  // Load initial data (컴포넌트 마운트 시 1회만 실행)
  useEffect(() => {
    loadSessions();
    loadClasses();
    loadClassExamples();
    loadSystemStatus();
    const interval = setInterval(loadSystemStatus, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load session from URL parameter
  useEffect(() => {
    if (urlSessionId && (!currentSession || currentSession.session_id !== urlSessionId)) {
      loadSession(urlSessionId);
    }
  }, [urlSessionId, currentSession, loadSession]);

  // Reset verificationFinalized when session changes
  useEffect(() => {
    setVerificationFinalized(false);
  }, [currentSession?.session_id]);

  // Auto-load dimensions when session changes
  useEffect(() => {
    const fetchDimensions = async () => {
      if (currentSession?.session_id) {
        try {
          const { data } = await axios.get(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}`);
          setDimensions(data.dimensions || []);
          setDimensionStats(data.stats || null);
        } catch (err) {
          logger.error('Failed to auto-load dimensions:', err);
        }
      }
    };
    fetchDimensions();
  }, [currentSession?.session_id]);

  // Auto-load relations when session changes (Phase 2)
  useEffect(() => {
    const fetchRelations = async () => {
      if (currentSession?.session_id) {
        try {
          const { data } = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}`);
          setRelations(data.relations || []);
          // Fetch statistics separately
          const statsRes = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}/statistics`);
          setRelationStats(statsRes.data || null);
        } catch (err) {
          // Relations might not exist yet, that's ok
          logger.log('No relations found:', err);
          setRelations([]);
          setRelationStats(null);
        }
      }
    };
    fetchRelations();
  }, [currentSession?.session_id]);

  // Auto-load GD&T when session changes (Phase 7)
  useEffect(() => {
    const fetchGDT = async () => {
      if (currentSession?.session_id) {
        try {
          const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}`);
          setFcfList(data.fcf_list || []);
          setGdtDatums(data.datums || []);
          // Fetch summary
          const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/summary`);
          setGdtSummary(summaryRes.data || null);
        } catch (err) {
          // GD&T might not exist yet, that's ok
          logger.log('No GD&T found:', err);
          setFcfList([]);
          setGdtDatums([]);
          setGdtSummary(null);
        }
      }
    };
    fetchGDT();
  }, [currentSession?.session_id]);

  // Auto-load GT when detections are available (의도적으로 session_id, imageSize, detections.length만 의존)
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSession?.session_id, imageSize, detections.length]);

  // Load functions
  const loadClasses = async () => {
    try {
      const { classes } = await detectionApi.getClasses();
      setAvailableClasses(classes);
    } catch (err) {
      logger.error('Failed to load classes:', err);
    }
  };

  const loadClassExamples = async () => {
    try {
      const { data } = await axios.get<{ examples: ClassExample[] }>(
        `${API_BASE_URL}/api/config/class-examples`
      );
      setClassExamples(data.examples || []);
    } catch (err) {
      logger.error('Failed to load class examples:', err);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const gpu = await systemApi.getGPUStatus();
      setGpuStatus(gpu);
    } catch (err) {
      logger.error('Failed to load system status:', err);
    }
  };

  // Handlers
  const handleVerify = async (detectionId: string, status: VerificationStatus) => {
    if (!currentSession) return;
    try {
      await verifyDetection(detectionId, status);
    } catch (err) {
      logger.error('Verification failed:', err);
    }
  };

  const handleGenerateBOM = async () => {
    if (!currentSession) return;
    try {
      await generateBOM();
    } catch (err) {
      logger.error('BOM generation failed:', err);
    }
  };

  const handleClearCache = async (cacheType: 'all' | 'memory') => {
    setIsClearingCache(true);
    try {
      await systemApi.clearCache(cacheType);
    } catch (err) {
      logger.error('Cache clear failed:', err);
    } finally {
      setIsClearingCache(false);
    }
  };

  const handleNewSession = () => {
    reset();
    setGtCompareResult(null);
    setCurrentPage(1);
    setDimensions([]);
    setDimensionStats(null);
    setSelectedDimensionId(null);
    setLines([]);
    setIntersections([]);
  };

  // Dimension handlers
  const loadDimensions = async (sessionId: string) => {
    try {
      const { data } = await axios.get(`${API_BASE_URL}/analysis/dimensions/${sessionId}`);
      setDimensions(data.dimensions || []);
      setDimensionStats(data.stats || null);
    } catch (err) {
      logger.error('Failed to load dimensions:', err);
    }
  };

  const handleRunAnalysis = async () => {
    if (!currentSession) return;

    setIsRunningAnalysis(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/analysis/run/${currentSession.session_id}`);

      // 심볼 검출 결과는 기존 detections로 처리
      if (data.detections && data.detections.length > 0) {
        // 세션 다시 로드하여 detections 업데이트
        await loadSession(currentSession.session_id);
      }

      // 치수 OCR 결과
      if (data.dimensions) {
        setDimensions(data.dimensions);
        // 통계 계산
        const stats = { pending: 0, approved: 0, rejected: 0, modified: 0, manual: 0 };
        data.dimensions.forEach((d: Dimension) => {
          const status = d.verification_status || 'pending';
          if (status in stats) stats[status as keyof typeof stats]++;
        });
        setDimensionStats(stats);
      }

      // Phase 2: 관계 추출 결과
      if (data.relations) {
        setRelations(data.relations);
        // 통계 다시 로드
        try {
          const statsRes = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}/statistics`);
          setRelationStats(statsRes.data || null);
        } catch {
          // 통계 로드 실패 시 기본값
          setRelationStats({
            total: data.relations.length,
            by_method: {},
            by_confidence: { high: 0, medium: 0, low: 0 },
            linked_count: 0,
            unlinked_count: data.relations.length,
          });
        }
        logger.log(`✅ 관계 추출 완료: ${data.relations.length}개`);
      }

      logger.log('분석 완료:', data);
    } catch (err) {
      logger.error('Analysis failed:', err);
    } finally {
      setIsRunningAnalysis(false);
    }
  };

  const handleDimensionVerify = async (id: string, status: 'approved' | 'rejected') => {
    if (!currentSession) return;

    try {
      await axios.put(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}/${id}`, {
        verification_status: status
      });

      // 로컬 상태 업데이트
      setDimensions(prev => prev.map(d =>
        d.id === id ? { ...d, verification_status: status } : d
      ));

      // 통계 업데이트
      await loadDimensions(currentSession.session_id);
    } catch (err) {
      logger.error('Dimension verification failed:', err);
    }
  };

  const handleDimensionEdit = async (id: string, newValue: string) => {
    if (!currentSession) return;

    try {
      await axios.put(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}/${id}`, {
        modified_value: newValue,
        verification_status: 'modified'
      });

      // 로컬 상태 업데이트
      setDimensions(prev => prev.map(d =>
        d.id === id ? { ...d, modified_value: newValue, verification_status: 'modified' } : d
      ));
    } catch (err) {
      logger.error('Dimension edit failed:', err);
    }
  };

  const handleDimensionDelete = async (id: string) => {
    if (!currentSession) return;

    try {
      await axios.delete(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}/${id}`);

      // 로컬 상태 업데이트
      setDimensions(prev => prev.filter(d => d.id !== id));

      // 통계 업데이트
      await loadDimensions(currentSession.session_id);
    } catch (err) {
      logger.error('Dimension delete failed:', err);
    }
  };

  const handleBulkApproveDimensions = async (ids: string[]) => {
    if (!currentSession) return;

    try {
      await axios.put(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}/verify/bulk`, {
        updates: ids.map(id => ({ dimension_id: id, status: 'approved' }))
      });

      // 로컬 상태 업데이트
      setDimensions(prev => prev.map(d =>
        ids.includes(d.id) ? { ...d, verification_status: 'approved' } : d
      ));

      // 통계 업데이트
      await loadDimensions(currentSession.session_id);
    } catch (err) {
      logger.error('Bulk approve failed:', err);
    }
  };

  const handleAnalysisOptionsChange = (options: AnalysisOptionsData) => {
    // 분석 옵션이 변경되면 콘솔에 로깅 (추후 활용)
    logger.log('Analysis options changed:', options);
  };

  // 선 검출 핸들러
  const handleRunLineDetection = async () => {
    if (!currentSession) return;

    setIsRunningLineDetection(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/analysis/lines/${currentSession.session_id}`);
      setLines(data.lines || []);
      setIntersections(data.intersections || []);
      logger.log('선 검출 완료:', data.lines?.length, '개 선');
    } catch (err) {
      logger.error('Line detection failed:', err);
    } finally {
      setIsRunningLineDetection(false);
    }
  };

  // 치수-심볼 연결 핸들러
  const handleLinkDimensionsToSymbols = async () => {
    if (!currentSession) return;

    try {
      const { data } = await axios.post(`${API_BASE_URL}/analysis/lines/${currentSession.session_id}/link-dimensions`);
      logger.log('치수-심볼 연결 완료:', data);

      // 치수 목록 다시 로드
      await loadDimensions(currentSession.session_id);
    } catch (err) {
      logger.error('Link dimensions failed:', err);
    }
  };

  // P&ID 연결성 분석 핸들러 (2025-12-24)
  const handleAnalyzeConnectivity = async () => {
    if (!currentSession) return;

    setIsAnalyzingConnectivity(true);
    try {
      const result = await analysisApi.analyzeConnectivity(currentSession.session_id);
      setConnectivityData(result.connectivity_graph);
      logger.log('P&ID 연결성 분석 완료:', result.connectivity_graph.statistics);
    } catch (err) {
      logger.error('Connectivity analysis failed:', err);
    } finally {
      setIsAnalyzingConnectivity(false);
    }
  };

  // P&ID 경로 찾기 핸들러 (2025-12-24)
  const handleFindPath = async (startId: string, endId: string) => {
    if (!currentSession) return;

    try {
      const result = await analysisApi.findPath(currentSession.session_id, startId, endId);
      setHighlightPath(result.path);
      logger.log('경로 찾기 완료:', result.path.length, '노드');
    } catch (err) {
      logger.error('Path finding failed:', err);
      setHighlightPath(null);
    }
  };

  // 표제란 OCR 추출 핸들러 (2025-12-24)
  const handleExtractTitleBlock = async () => {
    if (!currentSession) return;

    setIsExtractingTitleBlock(true);
    try {
      const result = await analysisApi.extractTitleBlock(currentSession.session_id);
      if (result.title_block) {
        setTitleBlockData(result.title_block);
        logger.log('표제란 OCR 완료:', result.title_block);
      } else {
        logger.warn('표제란을 찾을 수 없습니다');
      }
    } catch (err) {
      logger.error('Title block extraction failed:', err);
    } finally {
      setIsExtractingTitleBlock(false);
    }
  };

  // 표제란 정보 수정 핸들러 (2025-12-24)
  const handleUpdateTitleBlock = async () => {
    if (!currentSession || !editingTitleBlock) return;

    try {
      const result = await analysisApi.updateTitleBlock(currentSession.session_id, editingTitleBlock);
      setTitleBlockData(result.title_block);
      setEditingTitleBlock(null);
      logger.log('표제란 정보 수정 완료');
    } catch (err) {
      logger.error('Title block update failed:', err);
    }
  };

  // ==================== 중기 로드맵 핸들러 (2025-12-24) ====================

  // 1. 용접 기호 파싱 핸들러
  const handleParseWelding = async () => {
    if (!currentSession) return;
    setIsParsingWelding(true);
    try {
      const result = await analysisApi.parseWeldingSymbols(currentSession.session_id);
      setWeldingResult(result);
      logger.log(`🔩 용접 기호 파싱 완료: ${result.total_count}개`);
    } catch (err) {
      logger.error('Welding symbol parsing failed:', err);
    } finally {
      setIsParsingWelding(false);
    }
  };

  // 2. 표면 거칠기 파싱 핸들러
  const handleParseRoughness = async () => {
    if (!currentSession) return;
    setIsParsingRoughness(true);
    try {
      const result = await analysisApi.parseSurfaceRoughness(currentSession.session_id);
      setRoughnessResult(result);
      logger.log(`🪨 표면 거칠기 파싱 완료: ${result.total_count}개`);
    } catch (err) {
      logger.error('Surface roughness parsing failed:', err);
    } finally {
      setIsParsingRoughness(false);
    }
  };

  // 3. 수량 추출 핸들러
  const handleExtractQuantity = async () => {
    if (!currentSession) return;
    setIsExtractingQuantity(true);
    try {
      const result = await analysisApi.extractQuantities(currentSession.session_id);
      setQuantityResult(result);
      logger.log(`🔢 수량 추출 완료: ${result.total_items}개 항목, 총 ${result.total_quantity}개`);
    } catch (err) {
      logger.error('Quantity extraction failed:', err);
    } finally {
      setIsExtractingQuantity(false);
    }
  };

  // 4. 벌룬 매칭 핸들러
  const handleMatchBalloons = async () => {
    if (!currentSession) return;
    setIsMatchingBalloons(true);
    try {
      const result = await analysisApi.matchBalloons(currentSession.session_id);
      setBalloonResult(result);
      logger.log(`🎈 벌룬 매칭 완료: ${result.matched_count}/${result.total_balloons}개 매칭됨 (${result.match_rate.toFixed(1)}%)`);
    } catch (err) {
      logger.error('Balloon matching failed:', err);
    } finally {
      setIsMatchingBalloons(false);
    }
  };

  // 벌룬-심볼 수동 연결 핸들러
  const handleLinkBalloon = async (balloonId: string, symbolId: string) => {
    if (!currentSession) return;
    try {
      const result = await analysisApi.linkBalloonToSymbol(currentSession.session_id, balloonId, symbolId);
      // 결과 업데이트
      if (balloonResult) {
        const updated = balloonResult.balloons.map(b =>
          b.id === balloonId ? result.balloon : b
        );
        setBalloonResult({
          ...balloonResult,
          balloons: updated,
          matched_count: updated.filter(b => b.matched_symbol_id).length,
          unmatched_count: updated.filter(b => !b.matched_symbol_id).length,
          match_rate: (updated.filter(b => b.matched_symbol_id).length / updated.length) * 100,
        });
      }
      logger.log(`🎈 벌룬 ${balloonId} → 심볼 ${symbolId} 연결됨`);
    } catch (err) {
      logger.error('Balloon link failed:', err);
    }
  };

  // 장기 로드맵 핸들러 (2025-12-24)
  // 1. 도면 영역 세분화
  const handleSegmentRegions = async () => {
    if (!currentSession) return;
    setIsSegmentingRegions(true);
    try {
      const result = await longtermApi.segmentDrawingRegions(currentSession.session_id);
      setDrawingRegions(result.regions);
      logger.log(`🗺️ 도면 영역 세분화 완료: ${result.total_regions}개 영역 검출`);
    } catch (err) {
      logger.error('Region segmentation failed:', err);
    } finally {
      setIsSegmentingRegions(false);
    }
  };

  // 2. 주석/노트 추출
  const handleExtractNotes = async () => {
    if (!currentSession) return;
    setIsExtractingNotes(true);
    try {
      const result = await longtermApi.extractNotes(currentSession.session_id);
      setExtractedNotes(result.notes);
      logger.log(`📋 주석/노트 추출 완료: ${result.total_notes}개 추출`);
    } catch (err) {
      logger.error('Notes extraction failed:', err);
    } finally {
      setIsExtractingNotes(false);
    }
  };

  // 3. 리비전 비교
  const handleCompareRevisions = async () => {
    if (!currentSession || !comparisonSessionId) return;
    setIsComparingRevisions(true);
    try {
      const result = await longtermApi.compareRevisions(currentSession.session_id, comparisonSessionId);
      setRevisionChanges(result.changes);
      logger.log(`🔄 리비전 비교 완료: ${result.total_changes}개 변경점 감지`);
    } catch (err) {
      logger.error('Revision comparison failed:', err);
    } finally {
      setIsComparingRevisions(false);
    }
  };

  // 4. VLM 자동 분류
  const handleVlmClassify = async () => {
    if (!currentSession) return;
    setIsVlmClassifying(true);
    try {
      const result = await longtermApi.vlmClassify(currentSession.session_id);
      setVlmClassification(result);
      logger.log(`🤖 VLM 분류 완료: ${result.drawing_type} (${(result.drawing_type_confidence * 100).toFixed(1)}%)`);
    } catch (err) {
      logger.error('VLM classification failed:', err);
    } finally {
      setIsVlmClassifying(false);
    }
  };

  // Phase 2: 관계 추출 핸들러
  const handleExtractRelations = async () => {
    if (!currentSession) return;

    setIsExtractingRelations(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/relations/extract/${currentSession.session_id}?use_lines=true`);
      setRelations(data.relations || []);
      setRelationStats(data.statistics || null);
      logger.log(`✅ 관계 추출 완료: ${data.relations?.length}개`);
    } catch (err) {
      logger.error('Relation extraction failed:', err);
    } finally {
      setIsExtractingRelations(false);
    }
  };

  // Phase 2: 수동 관계 연결 핸들러
  const handleManualLink = async (dimensionId: string, targetId: string) => {
    if (!currentSession) return;

    try {
      await axios.post(`${API_BASE_URL}/relations/${currentSession.session_id}/link/${dimensionId}/${targetId}`);
      logger.log(`✅ 수동 연결: ${dimensionId} → ${targetId}`);

      // 관계 목록 다시 로드
      const { data } = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}`);
      setRelations(data.relations || []);

      // 통계 업데이트
      const statsRes = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}/statistics`);
      setRelationStats(statsRes.data || null);
    } catch (err) {
      logger.error('Manual link failed:', err);
    }
  };

  // Phase 2: 관계 삭제 핸들러
  const handleDeleteRelation = async (relationId: string) => {
    if (!currentSession) return;

    try {
      await axios.delete(`${API_BASE_URL}/relations/${currentSession.session_id}/${relationId}`);
      logger.log(`🗑️ 관계 삭제: ${relationId}`);

      // 관계 목록 다시 로드
      const { data } = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}`);
      setRelations(data.relations || []);

      // 통계 업데이트
      const statsRes = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}/statistics`);
      setRelationStats(statsRes.data || null);
    } catch (err) {
      logger.error('Delete relation failed:', err);
    }
  };

  // Phase 7: GD&T 파싱 핸들러
  const handleParseGDT = async () => {
    if (!currentSession) return;

    setIsParsingGDT(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/parse`);
      setFcfList(data.fcf_list || []);
      setGdtDatums(data.datums || []);
      logger.log(`✅ GD&T 파싱 완료: FCF ${data.total_fcf}개, 데이텀 ${data.total_datums}개`);

      // 요약 업데이트
      const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/summary`);
      setGdtSummary(summaryRes.data || null);
    } catch (err) {
      logger.error('GD&T parsing failed:', err);
    } finally {
      setIsParsingGDT(false);
    }
  };

  // Phase 7: FCF 업데이트 핸들러
  const handleFCFUpdate = async (fcfId: string, updates: Partial<FeatureControlFrame>) => {
    if (!currentSession) return;

    try {
      await axios.put(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/fcf/${fcfId}`, updates);
      logger.log(`✅ FCF 업데이트: ${fcfId}`);

      // FCF 목록 다시 로드
      const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}`);
      setFcfList(data.fcf_list || []);
      setGdtDatums(data.datums || []);
    } catch (err) {
      logger.error('FCF update failed:', err);
    }
  };

  // Phase 7: FCF 삭제 핸들러
  const handleFCFDelete = async (fcfId: string) => {
    if (!currentSession) return;

    try {
      await axios.delete(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/fcf/${fcfId}`);
      logger.log(`🗑️ FCF 삭제: ${fcfId}`);

      // FCF 목록 다시 로드
      const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}`);
      setFcfList(data.fcf_list || []);

      // 요약 업데이트
      const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/summary`);
      setGdtSummary(summaryRes.data || null);
    } catch (err) {
      logger.error('FCF delete failed:', err);
    }
  };

  // Phase 7: 데이텀 삭제 핸들러
  const handleDatumDelete = async (datumId: string) => {
    if (!currentSession) return;

    try {
      await axios.delete(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/datum/${datumId}`);
      logger.log(`🗑️ 데이텀 삭제: ${datumId}`);

      // GD&T 목록 다시 로드
      const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}`);
      setGdtDatums(data.datums || []);

      // 요약 업데이트
      const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/summary`);
      setGdtSummary(summaryRes.data || null);
    } catch (err) {
      logger.error('Datum delete failed:', err);
    }
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

  // Effective drawing type: session type or VLM classification result
  const effectiveDrawingType = useMemo(() => {
    // 세션에 명시적 타입이 설정된 경우 (빌더에서 설정)
    if (currentSession?.drawing_type && currentSession.drawing_type !== 'auto') {
      return currentSession.drawing_type;
    }
    // VLM 분류 결과가 있는 경우
    if (classification?.drawing_type) {
      return classification.drawing_type;
    }
    // 기본값
    return 'auto';
  }, [currentSession?.drawing_type, classification?.drawing_type]);

  // Effective features: 세션에서 전달된 features 배열 (2025-12-24: 기능 기반 재설계)
  const effectiveFeatures = useMemo(() => {
    // 세션에 features가 있으면 사용
    if (currentSession?.features && currentSession.features.length > 0) {
      return currentSession.features;
    }
    // features가 없으면 undefined 반환 (drawing_type 기반 폴백)
    return undefined;
  }, [currentSession?.features]);

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
                    className={`group relative p-2 rounded-lg text-sm cursor-pointer transition-colors ${currentSession?.session_id === session.session_id
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

            {/* 세션 전체 삭제 버튼 */}
            {sessions.length > 0 && (
              <button
                onClick={async () => {
                  if (confirm(`모든 세션(${sessions.length}개)을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
                    for (const session of sessions) {
                      await deleteSession(session.session_id);
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
                  onOptionsChange={handleAnalysisOptionsChange}
                  onRunAnalysis={handleRunAnalysis}
                  compact={true}
                />
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
      // eslint-disable-next-line react-hooks/exhaustive-deps
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
                  className={`p-2 rounded-lg transition-colors ${detection.verification_status === 'approved'
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
                  className={`p-2 rounded-lg transition-colors ${detection.verification_status === 'rejected'
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
                  className={`p-2 rounded-lg transition-colors ${detection.verification_status === 'modified'
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
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1">
                📐 참조 도면
                <InfoTooltip content={FEATURE_TOOLTIPS.referenceDrawing.description} position="right" />
              </h2>
              <div className="flex gap-4">
                <div className="flex-1">
                  <img
                    src={imageData}
                    alt="도면"
                    className="w-full max-h-[400px] object-contain rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => setShowImageModal(true)}
                    title="클릭하여 크게 보기"
                  />
                  <p className="text-xs text-gray-500 text-center mt-1">📌 클릭하여 크게 보기</p>
                </div>
                {imageSize && (
                  <div className="w-48 space-y-2 text-sm">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 flex items-center">
                      <span className="text-gray-500">크기:</span>
                      <span className="ml-2 font-medium">{imageSize.width} × {imageSize.height}</span>
                      <InfoTooltip content={FEATURE_TOOLTIPS.imageSize.description} position="left" iconSize={12} />
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 flex items-center">
                      <span className="text-gray-500">검출:</span>
                      <span className="ml-2 font-medium">{detections.length}개</span>
                      <InfoTooltip content={FEATURE_TOOLTIPS.detectionCount.description} position="left" iconSize={12} />
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 flex items-center">
                      <span className="text-gray-500">승인:</span>
                      <span className="ml-2 font-medium text-green-600">{stats.approved}개</span>
                      <InfoTooltip content={FEATURE_TOOLTIPS.approvedCount.description} position="left" iconSize={12} />
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* 도면 분류 정보 (빌더에서 설정한 경우 읽기 전용) */}
          {currentSession && currentSession.drawing_type && currentSession.drawing_type !== 'auto' && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1">
                📋 도면 정보
                <InfoTooltip content="빌더에서 설정한 도면 타입입니다. 분석 파이프라인이 이 타입에 맞게 최적화됩니다." position="right" />
              </h2>
              <div className="bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {/* 새로운 타입 (2025-12-22) */}
                    {currentSession.drawing_type === 'dimension' && '📏'}
                    {currentSession.drawing_type === 'electrical_panel' && '🔌'}
                    {currentSession.drawing_type === 'dimension_bom' && '📐'}
                    {/* 기존 타입 */}
                    {currentSession.drawing_type === 'pid' && '🔬'}
                    {currentSession.drawing_type === 'assembly' && '🔩'}
                    {/* 레거시 타입 */}
                    {currentSession.drawing_type === 'mechanical' && '⚙️'}
                    {currentSession.drawing_type === 'mechanical_part' && '⚙️'}
                    {currentSession.drawing_type === 'electrical' && '⚡'}
                    {currentSession.drawing_type === 'electrical_circuit' && '⚡'}
                    {currentSession.drawing_type === 'architectural' && '🏗️'}
                  </span>
                  <div>
                    <span className="font-medium text-indigo-800 dark:text-indigo-200">
                      {/* 새로운 타입 (2025-12-22) */}
                      {currentSession.drawing_type === 'dimension' && '치수 도면'}
                      {currentSession.drawing_type === 'electrical_panel' && '전기 제어판'}
                      {currentSession.drawing_type === 'dimension_bom' && '치수 + BOM'}
                      {/* 기존 타입 */}
                      {currentSession.drawing_type === 'pid' && 'P&ID (배관계장도)'}
                      {currentSession.drawing_type === 'assembly' && '조립도'}
                      {/* 레거시 타입 */}
                      {currentSession.drawing_type === 'mechanical' && '기계 부품도'}
                      {currentSession.drawing_type === 'mechanical_part' && '기계 부품도'}
                      {currentSession.drawing_type === 'electrical' && '전기 회로도'}
                      {currentSession.drawing_type === 'electrical_circuit' && '전기 회로도'}
                      {currentSession.drawing_type === 'architectural' && '건축 도면'}
                    </span>
                    <span className="ml-2 text-sm text-indigo-600 dark:text-indigo-400">
                      (빌더에서 설정됨)
                    </span>
                  </div>
                </div>
                {/* 도면 타입별 설명 */}
                <div className="text-xs text-indigo-600 dark:text-indigo-400 max-w-[200px] text-right">
                  {currentSession.drawing_type === 'dimension' && 'OCR 치수 인식 중심'}
                  {currentSession.drawing_type === 'electrical_panel' && 'YOLO 심볼 검출'}
                  {currentSession.drawing_type === 'dimension_bom' && 'OCR + 수동 라벨링'}
                  {currentSession.drawing_type === 'pid' && 'P&ID 심볼 + 라인'}
                  {currentSession.drawing_type === 'assembly' && 'YOLO + OCR'}
                </div>
              </div>
            </section>
          )}

          {/* 빌더에서 설정된 기능 (features가 있는 경우 표시) */}
          {currentSession && effectiveFeatures && effectiveFeatures.length > 0 && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                🔧 활성화된 기능
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                  (빌더에서 설정됨)
                </span>
              </h2>
              <div className="flex flex-wrap gap-2">
                {effectiveFeatures.includes('symbol_detection') && (
                  <span className="px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm flex items-center gap-1">
                    🎯 심볼 검출
                  </span>
                )}
                {effectiveFeatures.includes('symbol_verification') && (
                  <span className="px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm flex items-center gap-1">
                    ✅ 심볼 검증
                  </span>
                )}
                {effectiveFeatures.includes('dimension_ocr') && (
                  <span className="px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm flex items-center gap-1">
                    📏 치수 OCR
                  </span>
                )}
                {effectiveFeatures.includes('dimension_verification') && (
                  <span className="px-3 py-1.5 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 rounded-full text-sm flex items-center gap-1">
                    ✅ 치수 검증
                  </span>
                )}
                {effectiveFeatures.includes('gt_comparison') && (
                  <span className="px-3 py-1.5 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded-full text-sm flex items-center gap-1">
                    📊 GT 비교
                  </span>
                )}
                {effectiveFeatures.includes('bom_generation') && (
                  <span className="px-3 py-1.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-sm flex items-center gap-1">
                    📋 BOM 생성
                  </span>
                )}
                {effectiveFeatures.includes('gdt_parsing') && (
                  <span className="px-3 py-1.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm flex items-center gap-1">
                    📐 GD&T 파싱
                  </span>
                )}
                {/* 단기 로드맵 기능 (2025-12-24) */}
                {effectiveFeatures.includes('line_detection') && (
                  <span className="px-3 py-1.5 bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 rounded-full text-sm flex items-center gap-1">
                    📐 선 검출
                  </span>
                )}
                {effectiveFeatures.includes('pid_connectivity') && (
                  <span className="px-3 py-1.5 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded-full text-sm flex items-center gap-1">
                    🔗 P&ID 연결성
                  </span>
                )}
                {effectiveFeatures.includes('title_block_ocr') && (
                  <span className="px-3 py-1.5 bg-slate-100 dark:bg-slate-900/30 text-slate-700 dark:text-slate-300 rounded-full text-sm flex items-center gap-1">
                    📝 표제란 OCR
                  </span>
                )}
              </div>
              <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                💡 워크플로우 빌더에서 선택한 기능에 따라 아래 섹션이 동적으로 표시됩니다.
              </p>
            </section>
          )}

          {/* VLM 도면 분류 (Phase 4) - auto인 경우에만 표시, features가 있으면 건너뜀 */}
          {currentSession && imageData && showClassifier && (!currentSession.drawing_type || currentSession.drawing_type === 'auto') && !effectiveFeatures && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <DrawingClassifier
                sessionId={currentSession.session_id}
                imageBase64={imageData.replace(/^data:image\/[a-z]+;base64,/, '')}
                onClassificationComplete={(result) => {
                  setClassification({
                    drawing_type: result.drawing_type,
                    confidence: result.confidence,
                    suggested_preset: result.suggested_preset,
                    provider: result.provider
                  });
                  logger.log('Classification complete:', result);
                }}
                onPresetApply={(presetName) => {
                  logger.log('Preset applied:', presetName);
                  // 분석 옵션 패널 열기
                  setShowAnalysisOptions(true);
                }}
                apiBaseUrl={API_BASE_URL}
              />
              {classification && (
                <div className="px-4 pb-4 flex justify-end">
                  <button
                    onClick={() => setShowClassifier(false)}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    분류 패널 숨기기
                  </button>
                </div>
              )}
            </section>
          )}

          {/* 분류 결과 요약 (VLM 분류 완료 후 - auto인 경우에만, features 없을 때만) */}
          {classification && !showClassifier && (!currentSession?.drawing_type || currentSession.drawing_type === 'auto') && !effectiveFeatures && (
            <div className="bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">
                  {classification.drawing_type === 'mechanical_part' && '⚙️'}
                  {classification.drawing_type === 'pid' && '🔧'}
                  {classification.drawing_type === 'assembly' && '🔩'}
                  {classification.drawing_type === 'electrical' && '⚡'}
                  {classification.drawing_type === 'architectural' && '🏗️'}
                  {classification.drawing_type === 'unknown' && '❓'}
                </span>
                <div>
                  <span className="font-medium text-indigo-800 dark:text-indigo-200">
                    {classification.drawing_type === 'mechanical_part' && '기계 부품도'}
                    {classification.drawing_type === 'pid' && 'P&ID'}
                    {classification.drawing_type === 'assembly' && '조립도'}
                    {classification.drawing_type === 'electrical' && '전기 회로도'}
                    {classification.drawing_type === 'architectural' && '건축 도면'}
                    {classification.drawing_type === 'unknown' && '분류 불가'}
                  </span>
                  <span className="ml-2 text-sm text-indigo-600 dark:text-indigo-400">
                    ({(classification.confidence * 100).toFixed(0)}% via {classification.provider})
                  </span>
                </div>
              </div>
              <button
                onClick={() => setShowClassifier(true)}
                className="text-sm text-indigo-600 hover:text-indigo-800 dark:text-indigo-400"
              >
                다시 분류
              </button>
            </div>
          )}

          {/* Section 1: AI 검출 결과 */}
          {detections.length > 0 && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              {/* Title with inline metrics (Streamlit style) */}
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-1">
                🔍 AI 검출 결과
                <InfoTooltip content={FEATURE_TOOLTIPS.detectionResults.description} position="right" />
                {gtCompareResult && (
                  <span className="text-base font-normal ml-2 flex items-center gap-1">
                    📊 파나시아 YOLOv11N - {stats.total}개 검출
                    (<span className="inline-flex items-center">F1: {gtCompareResult.metrics.f1_score.toFixed(1)}%<InfoTooltip content={FEATURE_TOOLTIPS.f1Score.description} position="bottom" iconSize={12} /></span>,
                    <span className="inline-flex items-center ml-1">정밀도: {gtCompareResult.metrics.precision.toFixed(1)}%<InfoTooltip content={FEATURE_TOOLTIPS.precision.description} position="bottom" iconSize={12} /></span>,
                    <span className="inline-flex items-center ml-1">재현율: {gtCompareResult.metrics.recall.toFixed(1)}%<InfoTooltip content={FEATURE_TOOLTIPS.recall.description} position="bottom" iconSize={12} /></span>)
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
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-1">
                  ✅ 심볼 검증 및 수정
                  <InfoTooltip content={FEATURE_TOOLTIPS.symbolVerification.description} position="right" />
                </h2>
                <div className="flex items-center space-x-3">
                  <div className="flex items-center">
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
                    <InfoTooltip content={FEATURE_TOOLTIPS.approveAll.description} position="bottom" iconSize={12} />
                  </div>
                  <div className="flex items-center">
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
                    <InfoTooltip content={FEATURE_TOOLTIPS.rejectAll.description} position="bottom" iconSize={12} />
                  </div>
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
                  <InfoTooltip content={FEATURE_TOOLTIPS.showGT.description} position="bottom" iconSize={12} />
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showRefImages}
                    onChange={(e) => setShowRefImages(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">📚 참조 이미지 표시</span>
                  <InfoTooltip content={FEATURE_TOOLTIPS.showReference.description} position="bottom" iconSize={12} />
                </label>
                <div className="flex items-center">
                  <button
                    onClick={() => setShowManualLabel(!showManualLabel)}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    ✏️ 수작업 라벨 추가
                  </button>
                  <InfoTooltip content={FEATURE_TOOLTIPS.manualLabel.description} position="bottom" iconSize={12} />
                </div>
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
                      onBoxDrawn={async (box) => {
                        if (!manualLabel.class_name) {
                          alert('클래스를 먼저 선택해주세요!');
                          return;
                        }
                        if (!currentSession) return;

                        try {
                          logger.log('Adding manual detection:', manualLabel.class_name, box);
                          const result = await detectionApi.addManual(currentSession.session_id, {
                            class_name: manualLabel.class_name,
                            bbox: box,
                          });
                          logger.log('Manual detection added:', result);

                          // 세션 다시 로드하여 UI 업데이트
                          await loadSession(currentSession.session_id);
                          logger.log('Session reloaded, detections updated');
                        } catch (error) {
                          logger.error('Failed to add manual detection:', error);
                          alert('수작업 라벨 추가 실패: ' + (error instanceof Error ? error.message : '알 수 없는 오류'));
                        }
                      }}
                    />
                  </div>

                  {/* 추가된 수작업 라벨 목록 */}
                  {detections.filter(d => d.verification_status === 'manual').length > 0 && (
                    <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                      <h4 className="font-semibold text-purple-700 dark:text-purple-300 mb-2">
                        🎨 수작업 라벨 목록 ({detections.filter(d => d.verification_status === 'manual').length}개)
                      </h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {detections
                          .filter(d => d.verification_status === 'manual')
                          .map((d, idx) => (
                            <div
                              key={d.id}
                              className="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded border border-purple-100 dark:border-purple-700"
                            >
                              <div className="flex items-center space-x-3">
                                <span className="w-6 h-6 flex items-center justify-center bg-purple-500 text-white text-xs rounded-full">
                                  {idx + 1}
                                </span>
                                <div>
                                  <span className="font-medium text-gray-900 dark:text-white">
                                    {d.class_name}
                                  </span>
                                  <span className="ml-2 text-xs text-gray-500">
                                    ({Math.round(d.bbox.x1)}, {Math.round(d.bbox.y1)}) - ({Math.round(d.bbox.x2)}, {Math.round(d.bbox.y2)})
                                  </span>
                                  <span className="ml-2 text-xs text-gray-400">
                                    {Math.round(d.bbox.x2 - d.bbox.x1)}×{Math.round(d.bbox.y2 - d.bbox.y1)}px
                                  </span>
                                </div>
                              </div>
                              <button
                                onClick={() => {
                                  if (confirm(`"${d.class_name}" 수작업 라벨을 삭제하시겠습니까?`)) {
                                    deleteDetection(d.id);
                                  }
                                }}
                                className="p-1 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30 rounded"
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
                      className={`px-3 py-1 text-sm rounded ${page === currentPage
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

              {/* 검증 완료 버튼 */}
              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <p>현재 검증 현황:
                      승인 <span className="font-bold text-green-600">{stats.approved}</span>개 /
                      거부 <span className="font-bold text-red-600">{stats.rejected}</span>개 /
                      수작업 <span className="font-bold text-purple-600">{stats.manual}</span>개 /
                      대기 <span className="font-bold text-gray-500">{stats.pending}</span>개
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      BOM에 포함될 항목: <span className="font-bold text-primary-600">{stats.approved + stats.manual}</span>개
                      (승인 + 수작업)
                    </p>
                  </div>
                  <div className="flex items-center">
                    <button
                      onClick={() => {
                        const finalCount = stats.approved + stats.manual;
                        if (finalCount === 0) {
                          alert('BOM에 포함할 항목이 없습니다.\n검출 결과를 승인하거나 수작업 라벨을 추가해주세요.');
                          return;
                        }
                        setVerificationFinalized(true);
                      }}
                      className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-semibold transition-all ${verificationFinalized
                        ? 'bg-green-100 text-green-700 border-2 border-green-500'
                        : 'bg-green-600 text-white hover:bg-green-700'
                        }`}
                    >
                      {verificationFinalized ? (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          <span>검증 완료됨</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          <span>검증 완료</span>
                        </>
                      )}
                    </button>
                    <InfoTooltip content={FEATURE_TOOLTIPS.verificationComplete.description} position="left" iconSize={14} />
                  </div>
                </div>
                {verificationFinalized && (
                  <p className="mt-2 text-sm text-green-600 dark:text-green-400">
                    ✓ 검증이 완료되었습니다. 아래에서 최종 결과를 확인하고 BOM을 생성하세요.
                  </p>
                )}
              </div>
            </section>
          )}

          {/* Section 4.5: 치수 OCR 결과 - 타입별 조건부 렌더링 */}
          {dimensions.length > 0 && getSectionVisibility(effectiveDrawingType, effectiveFeatures).dimensionOCR && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  📏 치수 OCR 결과
                  <span className="text-base font-normal text-gray-500 ml-2">
                    ({dimensions.length}개 치수)
                  </span>
                </h2>
                {isRunningAnalysis && (
                  <div className="flex items-center text-primary-600">
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    <span className="text-sm">분석 중...</span>
                  </div>
                )}
              </div>

              {/* 뷰 모드 토글 */}
              <div className="flex gap-2 mb-3">
                <button
                  onClick={() => setShowVerificationQueue(false)}
                  className={`flex-1 px-3 py-2 text-sm rounded-lg transition-colors ${
                    !showVerificationQueue
                      ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  치수 목록
                </button>
                <button
                  onClick={() => setShowVerificationQueue(true)}
                  className={`flex-1 px-3 py-2 text-sm rounded-lg transition-colors ${
                    showVerificationQueue
                      ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Active Learning 큐
                </button>
              </div>

              {/* Dimension List 또는 Verification Queue */}
              {!showVerificationQueue ? (
                <DimensionList
                  dimensions={dimensions}
                  stats={dimensionStats || undefined}
                  onVerify={handleDimensionVerify}
                  onEdit={handleDimensionEdit}
                  onDelete={handleDimensionDelete}
                  onBulkApprove={handleBulkApproveDimensions}
                  onHover={(id) => setSelectedDimensionId(id)}
                  selectedId={selectedDimensionId}
                  imageData={imageData}
                  imageSize={imageSize}
                />
              ) : currentSession?.session_id ? (
                <VerificationQueue
                  sessionId={currentSession.session_id}
                  itemType="dimension"
                  onVerify={(itemId, action) => {
                    logger.log(`Verified ${itemId}: ${action}`);
                    // 치수 목록 새로고침
                    axios.get(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}`)
                      .then(({ data }) => {
                        setDimensions(data.dimensions || []);
                        setDimensionStats(data.stats || null);
                      });
                  }}
                  onAutoApprove={() => {
                    // 자동 승인 후 새로고침
                    axios.get(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}`)
                      .then(({ data }) => {
                        setDimensions(data.dimensions || []);
                        setDimensionStats(data.stats || null);
                      });
                  }}
                  onItemSelect={(itemId) => setSelectedDimensionId(itemId)}
                  apiBaseUrl={API_BASE_URL}
                />
              ) : (
                <div className="text-center text-gray-500 py-8">
                  세션을 선택해주세요
                </div>
              )}

              {/* 치수 요약 */}
              {dimensionStats && (
                <div className="mt-4 grid grid-cols-5 gap-2 text-sm">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 text-center">
                    <p className="text-lg font-bold text-gray-900 dark:text-white">{dimensions.length}</p>
                    <p className="text-xs text-gray-500">총 치수</p>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded p-2 text-center">
                    <p className="text-lg font-bold text-yellow-600">{dimensionStats.pending}</p>
                    <p className="text-xs text-gray-500">대기</p>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 rounded p-2 text-center">
                    <p className="text-lg font-bold text-green-600">{dimensionStats.approved}</p>
                    <p className="text-xs text-gray-500">승인</p>
                  </div>
                  <div className="bg-red-50 dark:bg-red-900/20 rounded p-2 text-center">
                    <p className="text-lg font-bold text-red-600">{dimensionStats.rejected}</p>
                    <p className="text-xs text-gray-500">거부</p>
                  </div>
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2 text-center">
                    <p className="text-lg font-bold text-blue-600">{dimensionStats.modified + dimensionStats.manual}</p>
                    <p className="text-xs text-gray-500">수정</p>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* Section 4.7: 선 검출 결과 - 타입별 조건부 렌더링 */}
          {currentSession && imageData && imageSize && getSectionVisibility(effectiveDrawingType, effectiveFeatures).lineDetection && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-1">
                  📐 선 검출
                  <InfoTooltip content={FEATURE_TOOLTIPS.lineDetection.description} position="right" />
                  {lines.length > 0 && (
                    <span className="text-base font-normal text-gray-500 ml-2">
                      ({lines.length}개 선, {intersections.length}개 교차점)
                    </span>
                  )}
                </h2>
                <div className="flex items-center gap-2">
                  {lines.length > 0 && (
                    <label className="flex items-center gap-2 text-sm text-gray-600">
                      <input
                        type="checkbox"
                        checked={showLines}
                        onChange={(e) => setShowLines(e.target.checked)}
                        className="rounded text-primary-600"
                      />
                      선 표시
                    </label>
                  )}
                  <button
                    onClick={handleRunLineDetection}
                    disabled={isRunningLineDetection}
                    className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors"
                  >
                    {isRunningLineDetection ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>검출 중...</span>
                      </>
                    ) : (
                      <>
                        <Ruler className="w-4 h-4" />
                        <span>선 검출</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 선 검출 결과 표시 */}
              {lines.length > 0 ? (
                <div className="space-y-4">
                  {/* 이미지 + 선 오버레이 */}
                  <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700" style={{ height: 400 }}>
                    <img
                      src={imageData}
                      alt="Blueprint with lines"
                      className="w-full h-full object-contain"
                    />
                    {showLines && (
                      <div className="absolute top-0 left-0 w-full h-full">
                        <IntegratedOverlay
                          imageData={imageData}
                          imageSize={imageSize}
                          detections={detections}
                          lines={lines}
                          dimensions={dimensions}
                          intersections={intersections}
                          links={links}
                          maxWidth="100%"
                          maxHeight={400}
                        />
                      </div>
                    )}
                  </div>

                  {/* 선 유형별 통계 */}
                  <div className="grid grid-cols-4 gap-2 text-sm">
                    {Object.entries(
                      lines.reduce((acc, line) => {
                        acc[line.line_type] = (acc[line.line_type] || 0) + 1;
                        return acc;
                      }, {} as Record<string, number>)
                    ).slice(0, 4).map(([type, count]) => (
                      <div key={type} className="bg-gray-50 dark:bg-gray-700 rounded p-2 text-center">
                        <p className="text-lg font-bold text-gray-900 dark:text-white">{count}</p>
                        <p className="text-xs text-gray-500">{type}</p>
                      </div>
                    ))}
                  </div>

                  {/* 치수-심볼 연결 버튼 */}
                  {dimensions.length > 0 && detections.length > 0 && (
                    <button
                      onClick={handleLinkDimensionsToSymbols}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      <Check className="w-4 h-4" />
                      <span>치수 → 심볼 자동 연결</span>
                    </button>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Ruler className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>선 검출을 실행하여 도면의 선을 분석하세요</p>
                  <p className="text-sm text-gray-400 mt-1">치수선, 배관, 신호선 등을 자동으로 분류합니다</p>
                </div>
              )}
            </section>
          )}

          {/* Section 4.5: Phase 2 - 치수-객체 관계 - 타입별 조건부 렌더링 */}
          {currentSession && dimensions.length > 0 && getSectionVisibility(effectiveDrawingType, effectiveFeatures).relationExtraction && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🔗 치수-객체 관계
                  <InfoTooltip content={FEATURE_TOOLTIPS.dimensionRelation.description} position="right" />
                  {relations.length > 0 && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded-full">
                      {relations.length}개
                    </span>
                  )}
                </h2>
                <div className="flex items-center gap-2">
                  {/* 토글 버튼 */}
                  <button
                    onClick={() => setShowRelations(!showRelations)}
                    className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                      showRelations
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                    }`}
                  >
                    {showRelations ? '관계선 표시' : '관계선 숨김'}
                  </button>
                  {/* 추출 버튼 */}
                  <button
                    onClick={handleExtractRelations}
                    disabled={isExtractingRelations}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {isExtractingRelations ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin" />
                        추출 중...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-3 h-3" />
                        관계 재추출
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 이미지 + 관계 오버레이 */}
              {imageData && imageSize && relations.length > 0 && showRelations && (
                <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 mb-4" style={{ height: 350 }}>
                  <img
                    src={imageData}
                    alt="Blueprint with relations"
                    className="w-full h-full object-contain"
                  />
                  <RelationOverlay
                    relations={relations}
                    dimensions={dimensions.map(d => ({ id: d.id, bbox: d.bbox, value: d.value }))}
                    detections={detections}
                    imageSize={imageSize}
                    containerSize={{ width: 600, height: 350 }}
                    selectedDimensionId={selectedDimensionId}
                    showLabels={true}
                    showConfidence={true}
                  />
                </div>
              )}

              {/* 관계 목록 */}
              <RelationList
                relations={relations}
                statistics={relationStats}
                dimensions={dimensions.map(d => ({ id: d.id, value: d.value, bbox: d.bbox }))}
                detections={detections}
                onManualLink={handleManualLink}
                onDeleteRelation={handleDeleteRelation}
                onSelectDimension={(id) => setSelectedDimensionId(id)}
                selectedDimensionId={selectedDimensionId}
                isLoading={isExtractingRelations}
              />
            </section>
          )}

          {/* Section 4.7.5: P&ID 연결성 분석 - features 기반 조건부 렌더링 (2025-12-24) */}
          {currentSession && imageData && imageSize && getSectionVisibility(effectiveDrawingType, effectiveFeatures).pidConnectivity && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🔗 P&ID 연결성
                  <InfoTooltip content="P&ID 도면에서 심볼 간 연결 관계를 분석합니다. 선 검출 결과를 기반으로 배관, 밸브, 기기 간의 연결을 추적합니다." position="right" />
                  {connectivityData && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300 rounded-full">
                      {connectivityData.statistics.total_connections}개 연결
                    </span>
                  )}
                </h2>
                <button
                  onClick={handleAnalyzeConnectivity}
                  disabled={isAnalyzingConnectivity || detections.length === 0}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isAnalyzingConnectivity ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      분석 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      연결성 분석
                    </>
                  )}
                </button>
              </div>

              {/* 연결성 다이어그램 */}
              {connectivityData ? (
                <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700" style={{ height: 400 }}>
                  <img
                    src={imageData}
                    alt="P&ID with connectivity"
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute inset-0">
                    <ConnectivityDiagram
                      data={connectivityData}
                      detections={detections}
                      imageSize={imageSize}
                      containerSize={{ width: 600, height: 400 }}
                      selectedSymbolId={selectedSymbolId}
                      highlightPath={highlightPath}
                      onSymbolClick={(id) => {
                        if (selectedSymbolId && selectedSymbolId !== id) {
                          // 두 심볼 선택 시 경로 찾기
                          handleFindPath(selectedSymbolId, id);
                        }
                        setSelectedSymbolId(id);
                      }}
                      onSymbolHover={() => {}}
                      showLabels={true}
                      showOrphans={true}
                    />
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="w-12 h-12 mx-auto mb-2 text-gray-300 flex items-center justify-center">
                    <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <p>연결성 분석을 실행하여 심볼 간 연결을 분석하세요</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {detections.length === 0
                      ? '먼저 심볼 검출을 실행하세요'
                      : `${detections.length}개 심볼 검출됨 - 분석 가능`}
                  </p>
                </div>
              )}

              {/* 연결 통계 요약 */}
              {connectivityData && (
                <div className="mt-4 grid grid-cols-4 gap-4 text-center">
                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {connectivityData.statistics.total_symbols}
                    </div>
                    <div className="text-xs text-gray-500">전체 심볼</div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-rose-600 dark:text-rose-400">
                      {connectivityData.statistics.total_connections}
                    </div>
                    <div className="text-xs text-gray-500">연결 수</div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {(connectivityData.statistics.connectivity_ratio * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">연결률</div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                      {connectivityData.statistics.orphan_count}
                    </div>
                    <div className="text-xs text-gray-500">고립 심볼</div>
                  </div>
                </div>
              )}

              {/* 선택된 심볼 정보 / 경로 찾기 안내 */}
              {selectedSymbolId && connectivityData && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
                  <span className="font-medium text-blue-700 dark:text-blue-300">
                    💡 다른 심볼을 클릭하면 두 심볼 간 연결 경로를 찾습니다.
                  </span>
                  {highlightPath && highlightPath.length > 1 && (
                    <div className="mt-2 text-blue-600 dark:text-blue-400">
                      경로: {highlightPath.map((id, i) => (
                        <span key={id}>
                          {connectivityData.nodes[id]?.class_name || id}
                          {i < highlightPath.length - 1 && ' → '}
                        </span>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={() => { setSelectedSymbolId(null); setHighlightPath(null); }}
                    className="mt-2 text-xs text-blue-500 hover:underline"
                  >
                    선택 해제
                  </button>
                </div>
              )}
            </section>
          )}

          {/* Section 4.7.6: 표제란 OCR - features 기반 조건부 렌더링 (2025-12-24) */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).titleBlockOcr && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  📝 표제란 OCR
                  <InfoTooltip content="도면 표제란에서 도면번호, 리비전, 날짜, 스케일 등 메타데이터를 자동으로 추출합니다." position="right" />
                  {titleBlockData?.drawing_number && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300 rounded-full">
                      {titleBlockData.drawing_number}
                    </span>
                  )}
                </h2>
                <div className="flex items-center gap-2">
                  {titleBlockData && !editingTitleBlock && (
                    <button
                      onClick={() => setEditingTitleBlock(titleBlockData)}
                      className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                    >
                      ✏️ 수정
                    </button>
                  )}
                  <button
                    onClick={handleExtractTitleBlock}
                    disabled={isExtractingTitleBlock}
                    className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-600 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isExtractingTitleBlock ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        추출 중...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-4 h-4" />
                        표제란 추출
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 표제란 정보 표시 */}
              {titleBlockData ? (
                <div className="space-y-4">
                  {/* 편집 모드 */}
                  {editingTitleBlock ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">도면번호</label>
                          <input
                            type="text"
                            value={editingTitleBlock.drawing_number || ''}
                            onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, drawing_number: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">리비전</label>
                          <input
                            type="text"
                            value={editingTitleBlock.revision || ''}
                            onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, revision: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">도면 제목</label>
                          <input
                            type="text"
                            value={editingTitleBlock.drawing_title || ''}
                            onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, drawing_title: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">날짜</label>
                          <input
                            type="text"
                            value={editingTitleBlock.date || ''}
                            onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, date: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">스케일</label>
                          <input
                            type="text"
                            value={editingTitleBlock.scale || ''}
                            onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, scale: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">회사</label>
                          <input
                            type="text"
                            value={editingTitleBlock.company || ''}
                            onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, company: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleUpdateTitleBlock}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                        >
                          ✓ 저장
                        </button>
                        <button
                          onClick={() => setEditingTitleBlock(null)}
                          className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-400 text-sm"
                        >
                          취소
                        </button>
                      </div>
                    </div>
                  ) : (
                    /* 읽기 모드 */
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {titleBlockData.drawing_number && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">도면번호</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.drawing_number}</div>
                        </div>
                      )}
                      {titleBlockData.revision && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">리비전</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.revision}</div>
                        </div>
                      )}
                      {titleBlockData.drawing_title && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3 col-span-2">
                          <div className="text-xs text-slate-500 mb-1">도면 제목</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.drawing_title}</div>
                        </div>
                      )}
                      {titleBlockData.date && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">날짜</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.date}</div>
                        </div>
                      )}
                      {titleBlockData.scale && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">스케일</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.scale}</div>
                        </div>
                      )}
                      {titleBlockData.material && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">재료</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.material}</div>
                        </div>
                      )}
                      {titleBlockData.company && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">회사</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.company}</div>
                        </div>
                      )}
                      {titleBlockData.drawn_by && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">작성자</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.drawn_by}</div>
                        </div>
                      )}
                      {titleBlockData.checked_by && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">검토자</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.checked_by}</div>
                        </div>
                      )}
                      {titleBlockData.approved_by && (
                        <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                          <div className="text-xs text-slate-500 mb-1">승인자</div>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.approved_by}</div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 원본 텍스트 표시 (디버깅용) */}
                  {titleBlockData.raw_text && (
                    <details className="mt-4">
                      <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                        📄 원본 텍스트 보기
                      </summary>
                      <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-900 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap">
                        {titleBlockData.raw_text}
                      </pre>
                    </details>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="w-12 h-12 mx-auto mb-2 text-gray-300 flex items-center justify-center text-4xl">
                    📝
                  </div>
                  <p>표제란 추출을 실행하여 도면 메타데이터를 가져오세요</p>
                  <p className="text-sm text-gray-400 mt-1">
                    도면번호, 리비전, 날짜, 스케일 등의 정보를 자동으로 인식합니다
                  </p>
                </div>
              )}
            </section>
          )}

          {/* Section 4.8: Phase 7 - GD&T 기하공차 - 타입별 조건부 렌더링 */}
          {currentSession && imageData && imageSize && getSectionVisibility(effectiveDrawingType, effectiveFeatures).gdtParsing && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  &#128208; GD&T 기하공차
                  <InfoTooltip content="기하 공차 (Geometric Dimensioning and Tolerancing): 직진도, 평면도, 위치도 등 14가지 기하 특성을 파싱합니다." position="right" />
                  {fcfList.length > 0 && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 rounded-full">
                      FCF {fcfList.length}개
                    </span>
                  )}
                  {gdtDatums.length > 0 && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 rounded-full">
                      데이텀 {gdtDatums.length}개
                    </span>
                  )}
                </h2>
                <div className="flex items-center gap-2">
                  {/* 토글 버튼 */}
                  <button
                    onClick={() => setShowGDT(!showGDT)}
                    className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                      showGDT
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                    }`}
                  >
                    {showGDT ? 'GD&T 표시' : 'GD&T 숨김'}
                  </button>
                  {/* 파싱 버튼 */}
                  <button
                    onClick={handleParseGDT}
                    disabled={isParsingGDT}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                  >
                    {isParsingGDT ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin" />
                        파싱 중...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-3 h-3" />
                        GD&T 파싱
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* GD&T 요약 통계 */}
              {gdtSummary && (fcfList.length > 0 || gdtDatums.length > 0) && (
                <div className="grid grid-cols-4 gap-3 mb-4">
                  <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-purple-600">{gdtSummary.total_fcf}</p>
                    <p className="text-xs text-gray-500">FCF</p>
                  </div>
                  <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-amber-600">{gdtSummary.total_datums}</p>
                    <p className="text-xs text-gray-500">데이텀</p>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-green-600">{gdtSummary.verified_fcf}</p>
                    <p className="text-xs text-gray-500">검증됨</p>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-yellow-600">{gdtSummary.pending_fcf}</p>
                    <p className="text-xs text-gray-500">대기중</p>
                  </div>
                </div>
              )}

              {/* GD&T 에디터 */}
              {showGDT && (fcfList.length > 0 || gdtDatums.length > 0) && (
                <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700" style={{ height: 400 }}>
                  <img
                    src={imageData}
                    alt="Blueprint with GD&T"
                    className="w-full h-full object-contain"
                  />
                  <GDTEditor
                    sessionId={currentSession.session_id}
                    fcfList={fcfList}
                    datums={gdtDatums}
                    imageSize={imageSize}
                    containerSize={{ width: 600, height: 400 }}
                    selectedFCFId={selectedFCFId}
                    selectedDatumId={selectedDatumId}
                    onFCFSelect={setSelectedFCFId}
                    onDatumSelect={setSelectedDatumId}
                    onFCFUpdate={handleFCFUpdate}
                    onFCFDelete={handleFCFDelete}
                    onDatumDelete={handleDatumDelete}
                    onParse={handleParseGDT}
                    isProcessing={isParsingGDT}
                    showLabels={true}
                  />
                </div>
              )}

              {/* 빈 상태 */}
              {fcfList.length === 0 && gdtDatums.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">&#128208;</div>
                  <p>GD&T 파싱을 실행하여 기하공차를 분석하세요</p>
                  <p className="text-sm text-gray-400 mt-1">직진도, 평면도, 위치도 등 14가지 기하 특성을 검출합니다</p>
                </div>
              )}
            </section>
          )}

          {/* ==================== 중기 로드맵 기능 섹션 (2025-12-24) ==================== */}

          {/* Section 4.9: 용접 기호 파싱 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).weldingSymbolParsing && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🔩 용접 기호 파싱
                  <InfoTooltip content="용접 기호를 검출하고 파싱합니다. 필렛, 그루브, 점 용접 등의 타입과 크기, 깊이, 피치 정보를 추출합니다." position="right" />
                  {weldingResult && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 rounded-full">
                      {weldingResult.total_count}개
                    </span>
                  )}
                </h2>
                <button
                  onClick={handleParseWelding}
                  disabled={isParsingWelding}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isParsingWelding ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      파싱 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      용접 기호 파싱
                    </>
                  )}
                </button>
              </div>

              {weldingResult && weldingResult.welding_symbols.length > 0 ? (
                <div className="space-y-4">
                  {/* 타입별 통계 */}
                  <div className="grid grid-cols-4 gap-3">
                    {Object.entries(weldingResult.by_type).map(([type, count]) => (
                      <div key={type} className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3 text-center">
                        <p className="text-lg font-bold text-amber-600">{count}</p>
                        <p className="text-xs text-gray-500">{type}</p>
                      </div>
                    ))}
                  </div>

                  {/* 용접 기호 목록 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {weldingResult.welding_symbols.map((symbol) => (
                      <div
                        key={symbol.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedWeldingId === symbol.id
                            ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-300'
                            : 'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700 hover:bg-gray-100'
                        }`}
                        onClick={() => setSelectedWeldingId(symbol.id === selectedWeldingId ? null : symbol.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-medium text-gray-900 dark:text-white">
                              {symbol.welding_type.toUpperCase()}
                            </span>
                            <span className="ml-2 text-sm text-gray-500">
                              ({symbol.location.replace('_', ' ')})
                            </span>
                          </div>
                          <span className="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded">
                            {(symbol.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="mt-1 text-sm text-gray-600 dark:text-gray-400 flex flex-wrap gap-2">
                          {symbol.size && <span>크기: {symbol.size}</span>}
                          {symbol.length && <span>길이: {symbol.length}</span>}
                          {symbol.pitch && <span>피치: {symbol.pitch}</span>}
                          {symbol.depth && <span>깊이: {symbol.depth}</span>}
                          {symbol.field_weld && <span className="text-blue-600">현장용접</span>}
                          {symbol.all_around && <span className="text-purple-600">전둘레</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🔩</div>
                  <p>용접 기호 파싱을 실행하여 용접 정보를 추출하세요</p>
                  <p className="text-sm text-gray-400 mt-1">필렛, 그루브, 점 용접 등 다양한 용접 타입을 인식합니다</p>
                </div>
              )}
            </section>
          )}

          {/* Section 4.10: 표면 거칠기 파싱 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).surfaceRoughnessParsing && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🪨 표면 거칠기 파싱
                  <InfoTooltip content="표면 거칠기 기호를 검출하고 파싱합니다. Ra, Rz, Rmax 값과 가공 방법, 방향 정보를 추출합니다." position="right" />
                  {roughnessResult && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-stone-100 text-stone-700 dark:bg-stone-900/30 dark:text-stone-300 rounded-full">
                      {roughnessResult.total_count}개
                    </span>
                  )}
                </h2>
                <button
                  onClick={handleParseRoughness}
                  disabled={isParsingRoughness}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-stone-600 text-white rounded-lg hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isParsingRoughness ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      파싱 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      거칠기 파싱
                    </>
                  )}
                </button>
              </div>

              {roughnessResult && roughnessResult.roughness_symbols.length > 0 ? (
                <div className="space-y-4">
                  {/* 타입별 통계 */}
                  <div className="grid grid-cols-4 gap-3">
                    {Object.entries(roughnessResult.by_type).map(([type, count]) => (
                      <div key={type} className="bg-stone-50 dark:bg-stone-900/20 rounded-lg p-3 text-center">
                        <p className="text-lg font-bold text-stone-600">{count}</p>
                        <p className="text-xs text-gray-500">{type}</p>
                      </div>
                    ))}
                  </div>

                  {/* 표면 거칠기 목록 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {roughnessResult.roughness_symbols.map((symbol) => (
                      <div
                        key={symbol.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedRoughnessId === symbol.id
                            ? 'bg-stone-50 dark:bg-stone-900/20 border-stone-300'
                            : 'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700 hover:bg-gray-100'
                        }`}
                        onClick={() => setSelectedRoughnessId(symbol.id === selectedRoughnessId ? null : symbol.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-medium text-gray-900 dark:text-white">
                              {symbol.roughness_type}
                            </span>
                            {symbol.value && (
                              <span className="ml-2 text-lg font-bold text-stone-600">
                                {symbol.value} {symbol.unit}
                              </span>
                            )}
                          </div>
                          <span className="text-xs px-2 py-1 bg-stone-100 text-stone-700 rounded">
                            {(symbol.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="mt-1 text-sm text-gray-600 dark:text-gray-400 flex flex-wrap gap-2">
                          {symbol.machining_method !== 'unknown' && <span>가공: {symbol.machining_method}</span>}
                          {symbol.lay_direction !== 'unknown' && <span>방향: {symbol.lay_direction}</span>}
                          {symbol.upper_limit && <span>상한: {symbol.upper_limit}</span>}
                          {symbol.lower_limit && <span>하한: {symbol.lower_limit}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🪨</div>
                  <p>표면 거칠기 파싱을 실행하여 거칠기 정보를 추출하세요</p>
                  <p className="text-sm text-gray-400 mt-1">Ra, Rz, Rmax 값과 가공 방법을 인식합니다</p>
                </div>
              )}
            </section>
          )}

          {/* Section 4.11: 수량 추출 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).quantityExtraction && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🔢 수량 추출
                  <InfoTooltip content="도면에서 부품 수량 정보를 추출합니다. QTY, 수량, EA 등의 패턴을 인식하여 자동으로 수량을 파악합니다." position="right" />
                  {quantityResult && (
                    <>
                      <span className="px-2 py-0.5 text-xs font-normal bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300 rounded-full">
                        {quantityResult.total_items}개 항목
                      </span>
                      <span className="px-2 py-0.5 text-xs font-normal bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded-full">
                        총 {quantityResult.total_quantity}개
                      </span>
                    </>
                  )}
                </h2>
                <button
                  onClick={handleExtractQuantity}
                  disabled={isExtractingQuantity}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isExtractingQuantity ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      추출 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      수량 추출
                    </>
                  )}
                </button>
              </div>

              {quantityResult && quantityResult.quantities.length > 0 ? (
                <div className="space-y-4">
                  {/* 출처별 통계 */}
                  <div className="grid grid-cols-4 gap-3">
                    {Object.entries(quantityResult.by_source).map(([source, count]) => (
                      <div key={source} className="bg-cyan-50 dark:bg-cyan-900/20 rounded-lg p-3 text-center">
                        <p className="text-lg font-bold text-cyan-600">{count}</p>
                        <p className="text-xs text-gray-500">{source}</p>
                      </div>
                    ))}
                  </div>

                  {/* 수량 목록 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {quantityResult.quantities.map((item) => (
                      <div
                        key={item.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedQuantityId === item.id
                            ? 'bg-cyan-50 dark:bg-cyan-900/20 border-cyan-300'
                            : 'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700 hover:bg-gray-100'
                        }`}
                        onClick={() => setSelectedQuantityId(item.id === selectedQuantityId ? null : item.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl font-bold text-cyan-600">{item.quantity}</span>
                            {item.unit && <span className="text-sm text-gray-500">{item.unit}</span>}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">{item.source}</span>
                            <span className="text-xs px-2 py-1 bg-cyan-100 text-cyan-700 rounded">
                              {(item.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                          {item.part_number && <span className="mr-2">부품번호: {item.part_number}</span>}
                          {item.balloon_number && <span className="mr-2">벌룬: {item.balloon_number}</span>}
                          {item.pattern_matched && <span className="text-gray-400">({item.pattern_matched})</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🔢</div>
                  <p>수량 추출을 실행하여 부품 수량을 파악하세요</p>
                  <p className="text-sm text-gray-400 mt-1">QTY, 수량, EA 등의 패턴을 자동 인식합니다</p>
                </div>
              )}
            </section>
          )}

          {/* Section 4.12: 벌룬 매칭 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).balloonMatching && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🎈 벌룬 매칭
                  <InfoTooltip content="벌룬 번호를 검출하고 해당 심볼과 자동으로 매칭합니다. 지시선을 분석하여 벌룬과 부품을 연결합니다." position="right" />
                  {balloonResult && (
                    <>
                      <span className="px-2 py-0.5 text-xs font-normal bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300 rounded-full">
                        {balloonResult.total_balloons}개
                      </span>
                      <span className="px-2 py-0.5 text-xs font-normal bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 rounded-full">
                        {balloonResult.match_rate.toFixed(0)}% 매칭
                      </span>
                    </>
                  )}
                </h2>
                <button
                  onClick={handleMatchBalloons}
                  disabled={isMatchingBalloons || detections.length === 0}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-pink-600 text-white rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isMatchingBalloons ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      매칭 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      벌룬 매칭
                    </>
                  )}
                </button>
              </div>

              {balloonResult && balloonResult.balloons.length > 0 ? (
                <div className="space-y-4">
                  {/* 매칭 통계 */}
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-pink-50 dark:bg-pink-900/20 rounded-lg p-3 text-center">
                      <p className="text-lg font-bold text-pink-600">{balloonResult.total_balloons}</p>
                      <p className="text-xs text-gray-500">전체</p>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                      <p className="text-lg font-bold text-green-600">{balloonResult.matched_count}</p>
                      <p className="text-xs text-gray-500">매칭됨</p>
                    </div>
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
                      <p className="text-lg font-bold text-yellow-600">{balloonResult.unmatched_count}</p>
                      <p className="text-xs text-gray-500">미매칭</p>
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                      <p className="text-lg font-bold text-blue-600">{balloonResult.match_rate.toFixed(0)}%</p>
                      <p className="text-xs text-gray-500">매칭률</p>
                    </div>
                  </div>

                  {/* 벌룬 목록 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {balloonResult.balloons.map((balloon) => (
                      <div
                        key={balloon.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedBalloonId === balloon.id
                            ? 'bg-pink-50 dark:bg-pink-900/20 border-pink-300'
                            : 'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700 hover:bg-gray-100'
                        }`}
                        onClick={() => setSelectedBalloonId(balloon.id === selectedBalloonId ? null : balloon.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="w-8 h-8 rounded-full bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center text-lg font-bold text-pink-600">
                              {balloon.number}
                            </span>
                            <div>
                              {balloon.matched_symbol_id ? (
                                <span className="text-green-600 font-medium flex items-center gap-1">
                                  <Check className="w-4 h-4" />
                                  {balloon.matched_symbol_class || balloon.matched_symbol_id}
                                </span>
                              ) : (
                                <span className="text-yellow-600 font-medium flex items-center gap-1">
                                  <AlertCircle className="w-4 h-4" />
                                  미매칭
                                </span>
                              )}
                            </div>
                          </div>
                          <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                            {balloon.shape}
                          </span>
                        </div>

                        {/* 수동 연결 UI (미매칭 벌룬 선택 시) */}
                        {selectedBalloonId === balloon.id && !balloon.matched_symbol_id && detections.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                            <p className="text-sm text-gray-600 mb-2">수동 연결:</p>
                            <div className="flex flex-wrap gap-1">
                              {detections.slice(0, 10).map((d) => (
                                <button
                                  key={d.id}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleLinkBalloon(balloon.id, d.id);
                                  }}
                                  className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                                >
                                  {d.class_name}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🎈</div>
                  <p>벌룬 매칭을 실행하여 부품 번호를 연결하세요</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {detections.length === 0
                      ? '먼저 심볼 검출을 실행하세요'
                      : `${detections.length}개 심볼 검출됨 - 매칭 가능`}
                  </p>
                </div>
              )}
            </section>
          )}

          {/* 장기 로드맵 섹션 (2025-12-24) */}

          {/* 1. 도면 영역 세분화 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).drawingRegionSegmentation && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🗺️ 도면 영역 세분화
                  <InfoTooltip content="SAM/U-Net 모델을 사용하여 도면의 뷰 영역(정면도, 측면도, 단면도, 상세도, 표제란 등)을 자동으로 구분합니다." position="right" />
                  {drawingRegions.length > 0 && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded-full">
                      {drawingRegions.length}개 영역
                    </span>
                  )}
                </h2>
                <button
                  onClick={handleSegmentRegions}
                  disabled={isSegmentingRegions}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSegmentingRegions ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      분석 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      영역 분석
                    </>
                  )}
                </button>
              </div>

              {drawingRegions.length > 0 ? (
                <div className="space-y-4">
                  {/* 영역 타입별 통계 */}
                  <div className="grid grid-cols-5 gap-3">
                    {['front', 'side', 'section', 'detail', 'title_block'].map((type) => {
                      const count = drawingRegions.filter(r => r.view_type === type).length;
                      return (
                        <div key={type} className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-3 text-center">
                          <p className="text-lg font-bold text-indigo-600">{count}</p>
                          <p className="text-xs text-gray-500 capitalize">{type.replace('_', ' ')}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* 영역 목록 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {drawingRegions.map((region) => (
                      <div
                        key={region.id}
                        onClick={() => setSelectedRegionId(selectedRegionId === region.id ? null : region.id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedRegionId === region.id
                            ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-300'
                            : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-indigo-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium capitalize">{region.view_type.replace('_', ' ')}</span>
                          <span className="text-xs text-gray-500">{(region.confidence * 100).toFixed(0)}%</span>
                        </div>
                        {region.label && (
                          <p className="text-sm text-gray-500 mt-1">{region.label}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🗺️</div>
                  <p>영역 분석을 실행하여 도면 뷰를 자동 구분하세요</p>
                  <p className="text-sm text-gray-400 mt-1">정면도, 측면도, 단면도, 상세도 등을 자동 검출</p>
                </div>
              )}
            </section>
          )}

          {/* 2. 주석/노트 추출 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).notesExtraction && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  📋 주석/노트 추출
                  <InfoTooltip content="OCR과 LLM을 활용하여 도면의 주석, 노트, 재료 정보, 열처리 조건 등을 자동으로 추출하고 분류합니다." position="right" />
                  {extractedNotes.length > 0 && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300 rounded-full">
                      {extractedNotes.length}개 노트
                    </span>
                  )}
                </h2>
                <button
                  onClick={handleExtractNotes}
                  disabled={isExtractingNotes}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isExtractingNotes ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      추출 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      노트 추출
                    </>
                  )}
                </button>
              </div>

              {extractedNotes.length > 0 ? (
                <div className="space-y-4">
                  {/* 카테고리별 통계 */}
                  <div className="grid grid-cols-4 gap-3">
                    {['material', 'tolerance', 'surface_finish', 'general'].map((cat) => {
                      const count = extractedNotes.filter(n => n.category === cat).length;
                      const colors: Record<string, string> = {
                        material: 'bg-blue-50 text-blue-600',
                        tolerance: 'bg-green-50 text-green-600',
                        surface_finish: 'bg-orange-50 text-orange-600',
                        general: 'bg-gray-50 text-gray-600',
                      };
                      return (
                        <div key={cat} className={`${colors[cat] || 'bg-gray-50 text-gray-600'} dark:bg-opacity-20 rounded-lg p-3 text-center`}>
                          <p className="text-lg font-bold">{count}</p>
                          <p className="text-xs capitalize">{cat.replace('_', ' ')}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* 노트 목록 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {extractedNotes.map((note) => (
                      <div
                        key={note.id}
                        onClick={() => setSelectedNoteId(selectedNoteId === note.id ? null : note.id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedNoteId === note.id
                            ? 'bg-teal-50 dark:bg-teal-900/20 border-teal-300'
                            : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-teal-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className={`px-2 py-0.5 text-xs rounded-full ${
                            note.category === 'material' ? 'bg-blue-100 text-blue-700' :
                            note.category === 'tolerance' ? 'bg-green-100 text-green-700' :
                            note.category === 'surface_finish' ? 'bg-orange-100 text-orange-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {note.category.replace('_', ' ')}
                          </span>
                          <span className="text-xs text-gray-500">{(note.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <p className="text-sm">{note.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">📋</div>
                  <p>노트 추출을 실행하여 주석 정보를 추출하세요</p>
                  <p className="text-sm text-gray-400 mt-1">재료, 공차, 가공 방법, 일반 주석 자동 분류</p>
                </div>
              )}
            </section>
          )}

          {/* 3. 리비전 비교 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).revisionComparison && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🔄 리비전 비교
                  <InfoTooltip content="SIFT/ORB 특징점 매칭을 사용하여 두 도면 버전 간의 변경점을 감지합니다. 추가, 수정, 삭제된 요소를 자동으로 하이라이트합니다." position="right" />
                  {revisionChanges.length > 0 && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300 rounded-full">
                      {revisionChanges.length}개 변경
                    </span>
                  )}
                </h2>
                <div className="flex items-center gap-2">
                  <select
                    value={comparisonSessionId}
                    onChange={(e) => setComparisonSessionId(e.target.value)}
                    className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                  >
                    <option value="">비교할 세션 선택...</option>
                    {sessions.filter(s => s.session_id !== currentSession.session_id).map(s => (
                      <option key={s.session_id} value={s.session_id}>
                        {s.filename || s.session_id.slice(0, 8)}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleCompareRevisions}
                    disabled={isComparingRevisions || !comparisonSessionId}
                    className="flex items-center gap-2 px-4 py-2 text-sm bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isComparingRevisions ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        비교 중...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-4 h-4" />
                        비교 실행
                      </>
                    )}
                  </button>
                </div>
              </div>

              {revisionChanges.length > 0 ? (
                <div className="space-y-4">
                  {/* 변경 유형별 통계 */}
                  <div className="grid grid-cols-3 gap-3">
                    {['added', 'modified', 'deleted'].map((type) => {
                      const count = revisionChanges.filter(c => c.change_type === type).length;
                      const colors: Record<string, string> = {
                        added: 'bg-green-50 text-green-600',
                        modified: 'bg-yellow-50 text-yellow-600',
                        deleted: 'bg-red-50 text-red-600',
                      };
                      const icons: Record<string, string> = {
                        added: '+',
                        modified: '~',
                        deleted: '-',
                      };
                      return (
                        <div key={type} className={`${colors[type]} dark:bg-opacity-20 rounded-lg p-3 text-center`}>
                          <p className="text-lg font-bold">{icons[type]}{count}</p>
                          <p className="text-xs capitalize">{type}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* 변경 목록 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {revisionChanges.map((change, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border ${
                          change.change_type === 'added' ? 'bg-green-50 dark:bg-green-900/20 border-green-200' :
                          change.change_type === 'modified' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200' :
                          'bg-red-50 dark:bg-red-900/20 border-red-200'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 text-xs rounded-full ${
                            change.change_type === 'added' ? 'bg-green-200 text-green-800' :
                            change.change_type === 'modified' ? 'bg-yellow-200 text-yellow-800' :
                            'bg-red-200 text-red-800'
                          }`}>
                            {change.change_type}
                          </span>
                          <span className="text-xs text-gray-500">{change.category}</span>
                        </div>
                        <p className="text-sm">{change.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🔄</div>
                  <p>비교할 세션을 선택하고 리비전 비교를 실행하세요</p>
                  <p className="text-sm text-gray-400 mt-1">추가, 수정, 삭제된 요소를 자동으로 감지</p>
                </div>
              )}
            </section>
          )}

          {/* 4. VLM 자동 분류 */}
          {currentSession && imageData && getSectionVisibility(effectiveDrawingType, effectiveFeatures).vlmAutoClassification && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  🤖 VLM 자동 분류
                  <InfoTooltip content="Vision-Language Model을 사용하여 도면의 타입, 산업 분야, 복잡도를 자동으로 분류하고 적합한 분석 기능을 추천합니다." position="right" />
                  {vlmClassification && (
                    <span className="px-2 py-0.5 text-xs font-normal bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-300 rounded-full">
                      {vlmClassification.drawing_type}
                    </span>
                  )}
                </h2>
                <button
                  onClick={handleVlmClassify}
                  disabled={isVlmClassifying}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-fuchsia-600 text-white rounded-lg hover:bg-fuchsia-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isVlmClassifying ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      분류 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      AI 분류
                    </>
                  )}
                </button>
              </div>

              {vlmClassification ? (
                <div className="space-y-4">
                  {/* 분류 결과 */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-fuchsia-50 dark:bg-fuchsia-900/20 rounded-lg p-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">도면 타입</p>
                      <p className="text-lg font-bold text-fuchsia-600 capitalize">
                        {vlmClassification.drawing_type.replace('_', ' ')}
                      </p>
                      <p className="text-xs text-gray-400">
                        {(vlmClassification.drawing_type_confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">산업 분야</p>
                      <p className="text-lg font-bold text-purple-600 capitalize">
                        {vlmClassification.industry_domain.replace('_', ' ')}
                      </p>
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">복잡도</p>
                      <p className="text-lg font-bold text-blue-600 capitalize">
                        {vlmClassification.complexity}
                      </p>
                    </div>
                  </div>

                  {/* 추천 기능 */}
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">🔧 추천 분석 기능:</p>
                    <div className="flex flex-wrap gap-2">
                      {vlmClassification.recommended_features.map((feature: string) => (
                        <span
                          key={feature}
                          className="px-3 py-1 text-sm bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-300 rounded-full"
                        >
                          {feature.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* VLM 분석 */}
                  {vlmClassification.analysis_summary && (
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">📝 AI 분석:</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {vlmClassification.analysis_summary}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🤖</div>
                  <p>AI 분류를 실행하여 도면 타입을 자동 분석하세요</p>
                  <p className="text-sm text-gray-400 mt-1">VLM이 도면 타입, 산업 분야, 적합한 기능을 추천</p>
                </div>
              )}
            </section>
          )}

          {/* Section 5: 최종 검증 결과 이미지 (검증 완료 후에만 표시) */}
          {verificationFinalized && imageData && imageSize && (stats.approved + stats.manual) > 0 && (
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

              {/* 2-Column Layout: Image + BOM List */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Final Image with Bounding Boxes */}
                <div className="lg:col-span-2">
                  <div
                    className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 cursor-pointer hover:ring-2 hover:ring-primary-500 transition-all"
                    onClick={() => setShowImageModal(true)}
                    title="클릭하여 확대"
                  >
                    <canvas
                      ref={(canvas) => {
                        if (!canvas || !imageData || !imageSize) return;
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return;

                        const img = new Image();
                        img.onload = () => {
                          // Scale to fit container (max 600px width for side-by-side layout)
                          const maxWidth = 600;
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
                    <div className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
                      🔍 클릭하여 확대
                    </div>
                  </div>
                  <p className="text-center text-sm text-gray-500 mt-2">
                    최종 선정된 부품: 총 {detections.filter(d =>
                      d.verification_status === 'approved' ||
                      d.verification_status === 'modified' ||
                      d.verification_status === 'manual'
                    ).length}개
                  </p>
                </div>

                {/* Right: BOM List */}
                <div className="lg:col-span-1">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 h-full">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3">📋 BOM 심볼 리스트</h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {(() => {
                        const finalDetections = detections.filter(d =>
                          d.verification_status === 'approved' ||
                          d.verification_status === 'modified' ||
                          d.verification_status === 'manual'
                        );

                        // Group by class name
                        const grouped = finalDetections.reduce((acc, d) => {
                          const className = d.modified_class_name || d.class_name;
                          if (!acc[className]) {
                            acc[className] = { count: 0, items: [] };
                          }
                          acc[className].count++;
                          acc[className].items.push(d);
                          return acc;
                        }, {} as Record<string, { count: number; items: typeof finalDetections }>);

                        const sortedClasses = Object.entries(grouped).sort((a, b) => b[1].count - a[1].count);

                        return sortedClasses.map(([className, data], idx) => (
                          <div
                            key={className}
                            className="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600"
                          >
                            <div className="flex items-center space-x-2">
                              <span className="w-6 h-6 flex items-center justify-center bg-primary-500 text-white text-xs rounded-full font-bold">
                                {idx + 1}
                              </span>
                              <span className="font-medium text-gray-900 dark:text-white text-sm">{className}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-lg font-bold text-primary-600">{data.count}</span>
                              <span className="text-xs text-gray-500">개</span>
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                    <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-700 dark:text-gray-300">총 품목 수</span>
                        <span className="text-xl font-bold text-primary-600">
                          {(() => {
                            const finalDetections = detections.filter(d =>
                              d.verification_status === 'approved' ||
                              d.verification_status === 'modified' ||
                              d.verification_status === 'manual'
                            );
                            const grouped = new Set(finalDetections.map(d => d.modified_class_name || d.class_name));
                            return grouped.size;
                          })()}종
                        </span>
                      </div>
                      <div className="flex justify-between items-center mt-1">
                        <span className="font-semibold text-gray-700 dark:text-gray-300">총 수량</span>
                        <span className="text-xl font-bold text-green-600">
                          {detections.filter(d =>
                            d.verification_status === 'approved' ||
                            d.verification_status === 'modified' ||
                            d.verification_status === 'manual'
                          ).length}개
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Image Modal */}
          {showImageModal && imageData && imageSize && (
            <div
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
              onClick={() => setShowImageModal(false)}
            >
              <div className="relative max-w-[95vw] max-h-[95vh]" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => setShowImageModal(false)}
                  className="absolute -top-10 right-0 text-white hover:text-gray-300 text-xl"
                >
                  ✕ 닫기
                </button>
                <canvas
                  ref={(canvas) => {
                    if (!canvas || !imageData || !imageSize) return;
                    const ctx = canvas.getContext('2d');
                    if (!ctx) return;

                    const img = new Image();
                    img.onload = () => {
                      // Full size with max viewport constraints
                      const maxWidth = window.innerWidth * 0.9;
                      const maxHeight = window.innerHeight * 0.85;
                      const scaleW = maxWidth / imageSize.width;
                      const scaleH = maxHeight / imageSize.height;
                      const scale = Math.min(1, scaleW, scaleH);

                      canvas.width = imageSize.width * scale;
                      canvas.height = imageSize.height * scale;

                      // Draw image
                      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                      // Draw bounding boxes
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

                        let color = '#22c55e';
                        if (detection.modified_class_name && detection.modified_class_name !== detection.class_name) {
                          color = '#f97316';
                        } else if (detection.verification_status === 'manual') {
                          color = '#a855f7';
                        }

                        ctx.strokeStyle = color;
                        ctx.lineWidth = 3;
                        ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

                        // Label with class name
                        const className = detection.modified_class_name || detection.class_name;
                        const label = `${idx + 1}. ${className}`;
                        ctx.font = 'bold 14px sans-serif';
                        const textWidth = ctx.measureText(label).width;
                        ctx.fillStyle = color;
                        ctx.fillRect(sx1, sy1 - 22, textWidth + 10, 22);
                        ctx.fillStyle = 'white';
                        ctx.fillText(label, sx1 + 5, sy1 - 6);
                      });
                    };
                    img.src = imageData;
                  }}
                  className="rounded-lg shadow-2xl"
                />
              </div>
            </div>
          )}

          {/* Section 6: BOM 생성 (검증 완료 후에만 표시) */}
          {verificationFinalized && detections.length > 0 && (
            <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-1">
                  📊 BOM 생성 및 내보내기
                  <InfoTooltip content={FEATURE_TOOLTIPS.bomGeneration.description} position="right" />
                </h2>
                <div className="flex items-center space-x-3">
                  <div className="flex items-center">
                    <select
                      value={exportFormat}
                      onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                    >
                      <option value="excel">Excel (.xlsx)</option>
                      <option value="csv">CSV</option>
                      <option value="json">JSON</option>
                    </select>
                    <InfoTooltip content={FEATURE_TOOLTIPS.exportFormat.description} position="bottom" iconSize={12} />
                  </div>
                  <div className="flex items-center">
                    <button
                      onClick={handleGenerateBOM}
                      disabled={isLoading || stats.approved === 0}
                      className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                    >
                      <FileSpreadsheet className="w-5 h-5" />
                      <span>BOM 생성</span>
                    </button>
                    <InfoTooltip content={FEATURE_TOOLTIPS.generateBOM.description} position="bottom" iconSize={12} />
                  </div>
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
                          <th className="px-4 py-2 text-left">치수 (규격)</th>
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
                            <td className="px-4 py-2">
                              {item.dimensions && item.dimensions.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {item.dimensions.map((dim, i) => (
                                    <span key={i} className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-600 rounded text-xs whitespace-nowrap">
                                      {dim}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <span className="text-gray-400 text-xs">-</span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-center">{item.quantity}</td>
                            <td className="px-4 py-2 text-right">{item.unit_price?.toLocaleString() || '-'}</td>
                            <td className="px-4 py-2 text-right">{item.total_price?.toLocaleString() || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-gray-50 dark:bg-gray-700 font-bold">
                        <tr>
                          <td colSpan={3} className="px-4 py-2">합계</td>
                          <td className="px-4 py-2 text-center">{bomData.summary.total_quantity}</td>
                          <td className="px-4 py-2"></td>
                          <td className="px-4 py-2 text-right">{bomData.summary.total?.toLocaleString() || '-'}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>

                  <div className="mt-4 flex justify-end">
                    <a
                      href={`${API_BASE_URL}/bom/${currentSession?.session_id}/download?format=${exportFormat}`}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      download
                    >
                      <Download className="w-4 h-4" />
                      <span>다운로드</span>
                    </a>
                  </div>
                </div>
              ) : (
                <div>
                  {/* BOM 생성 전 미리보기 */}
                  <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      💡 아래 승인된 검출 결과를 기반으로 BOM이 생성됩니다. "BOM 생성" 버튼을 클릭하세요.
                    </p>
                  </div>

                  {/* 미리보기 테이블 - 승인된 검출 결과를 클래스별로 그룹화 */}
                  {(() => {
                    const approvedDetections = detections.filter(d =>
                      d.verification_status === 'approved' ||
                      d.verification_status === 'modified' ||
                      d.verification_status === 'manual'
                    );

                    // 클래스별로 그룹화
                    const grouped = approvedDetections.reduce((acc, d) => {
                      const className = d.modified_class_name || d.class_name;
                      if (!acc[className]) {
                        acc[className] = { count: 0, items: [] };
                      }
                      acc[className].count++;
                      acc[className].items.push(d);
                      return acc;
                    }, {} as Record<string, { count: number; items: typeof approvedDetections }>);

                    const sortedClasses = Object.entries(grouped).sort((a, b) => b[1].count - a[1].count);

                    return (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                              <th className="px-4 py-2 text-left">#</th>
                              <th className="px-4 py-2 text-left">품목명 (클래스)</th>
                              <th className="px-4 py-2 text-center">수량</th>
                              <th className="px-4 py-2 text-center">상태</th>
                              <th className="px-4 py-2 text-left">검출 ID</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sortedClasses.map(([className, data], idx) => (
                              <tr key={className} className="border-b border-gray-200 dark:border-gray-700">
                                <td className="px-4 py-2">{idx + 1}</td>
                                <td className="px-4 py-2 font-medium">{className}</td>
                                <td className="px-4 py-2 text-center font-bold text-primary-600">{data.count}</td>
                                <td className="px-4 py-2 text-center">
                                  <div className="flex justify-center space-x-1">
                                    {data.items.some(i => i.verification_status === 'approved') && (
                                      <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">승인</span>
                                    )}
                                    {data.items.some(i => i.verification_status === 'modified') && (
                                      <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">수정</span>
                                    )}
                                    {data.items.some(i => i.verification_status === 'manual') && (
                                      <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">수작업</span>
                                    )}
                                  </div>
                                </td>
                                <td className="px-4 py-2 text-xs text-gray-500">
                                  {data.items.map(i => i.id.slice(0, 6)).join(', ')}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot className="bg-gray-50 dark:bg-gray-700 font-bold">
                            <tr>
                              <td colSpan={2} className="px-4 py-2">합계</td>
                              <td className="px-4 py-2 text-center">{approvedDetections.length}</td>
                              <td colSpan={2} className="px-4 py-2"></td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    );
                  })()}
                </div>
              )}
            </section>
          )}

        </div>
      </main>

      {/* 📚 심볼 참조 패널 (오른쪽 고정) */}
      <ReferencePanel onClose={() => { }} />
    </div>
  );
}

export default WorkflowPage;
