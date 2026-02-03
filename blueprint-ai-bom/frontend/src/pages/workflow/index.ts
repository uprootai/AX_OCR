/**
 * Workflow Module Exports
 * 워크플로우 페이지 관련 모듈 내보내기
 */

// Types (타입 재export)
export type {
  Dimension,
  DimensionStats,
  SectionVisibility,
  AnalysisOptionsData,
  DetectionStats,
} from './types/workflow';

// Config
export {
  DRAWING_TYPE_SECTIONS,
  getSectionVisibility,
  ITEMS_PER_PAGE,
  // Feature 의존성 검증
  FEATURE_DEPENDENCIES,
  validateFeatureDependencies,
  ALL_FEATURES_DISABLED,
} from './config/sectionConfig';
export type { DependencyValidationResult } from './config/sectionConfig';

// Hooks
export {
  // 상태 관리
  useWorkflowState,
  useWorkflowEffects,
  // 로드맵 기능
  useLongTermFeatures,
  useMidTermFeatures,
  // 분석 핸들러
  useAnalysisHandlers,
  useGDTHandlers,
  useDimensionHandlers,
  useRelationHandlers,
  useTitleBlockHandlers,
  // P&ID 분석 핸들러
  usePIDFeaturesHandlers,
  useBWMSHandlers,  // 하위 호환성
} from './hooks';
export type { WorkflowState, ClassExample, ClassificationData, LineData, IntersectionData, ManualLabelState } from './hooks';
export type { UIValveItem, UIEquipmentItem, UIChecklistItem } from './hooks';

// Components
export { WorkflowSidebar } from './components/WorkflowSidebar';
export { DetectionRow } from './components/DetectionRow';
export { ImageModal } from './components/ImageModal';

// Sections
export { LongTermSection } from './sections/LongTermSection';
export { MidTermSection } from './sections/MidTermSection';
export { TitleBlockSection } from './sections/TitleBlockSection';
export { ConnectivitySection } from './sections/ConnectivitySection';
export { GDTSection } from './sections/GDTSection';
export { DimensionSection } from './sections/DimensionSection';
export { LineDetectionSection } from './sections/LineDetectionSection';
export { RelationSection } from './sections/RelationSection';
export { SymbolVerificationSection } from './sections/SymbolVerificationSection';
export { DetectionResultsSection } from './sections/DetectionResultsSection';
export { FinalResultsSection } from './sections/FinalResultsSection';
export { BOMSection } from './sections/BOMSection';
export { ReferenceDrawingSection } from './sections/ReferenceDrawingSection';
export { DrawingInfoSection } from './sections/DrawingInfoSection';
export { ActiveFeaturesSection } from './sections/ActiveFeaturesSection';
export { VLMClassificationSection } from './sections/VLMClassificationSection';
export { PIDFeaturesSection, BWMSSection } from './sections/PIDFeaturesSection';
export { GTComparisonSection } from './sections/GTComparisonSection';
export { ImageReviewSection } from './sections/ImageReviewSection';
export { TableExtractionSection } from './sections/TableExtractionSection';
