/**
 * Section Configuration
 * features 배열 기반 섹션 가시성 설정
 *
 * 2025-12-26: drawing_type 기반 로직 제거, features만 사용
 */

import type { SectionVisibility } from '../types/workflow';

// 기본 기능 (features가 비어있을 때 사용)
const DEFAULT_FEATURES = ['symbol_detection', 'title_block_ocr', 'vlm_auto_classification'];

// 모든 기능 비활성화 기본값 (외부에서 사용 가능)
export const ALL_FEATURES_DISABLED: SectionVisibility = {
  symbolDetection: false,
  dimensionOCR: false,
  lineDetection: false,
  gdtParsing: false,
  relationExtraction: false,
  pidConnectivity: false,
  titleBlockOcr: false,
  weldingSymbolParsing: false,
  surfaceRoughnessParsing: false,
  quantityExtraction: false,
  balloonMatching: false,
  drawingRegionSegmentation: false,
  notesExtraction: false,
  revisionComparison: false,
  vlmAutoClassification: false,
};

/**
 * features 배열을 SectionVisibility 객체로 변환
 */
const featuresToVisibility = (features: string[]): SectionVisibility => ({
  symbolDetection: features.includes('symbol_detection'),
  dimensionOCR: features.includes('dimension_ocr'),
  lineDetection: features.includes('line_detection'),
  gdtParsing: features.includes('gdt_parsing'),
  relationExtraction: features.includes('relation_extraction'),
  pidConnectivity: features.includes('pid_connectivity'),
  titleBlockOcr: features.includes('title_block_ocr'),
  weldingSymbolParsing: features.includes('welding_symbol_parsing'),
  surfaceRoughnessParsing: features.includes('surface_roughness_parsing'),
  quantityExtraction: features.includes('quantity_extraction'),
  balloonMatching: features.includes('balloon_matching'),
  drawingRegionSegmentation: features.includes('drawing_region_segmentation'),
  notesExtraction: features.includes('notes_extraction'),
  revisionComparison: features.includes('revision_comparison'),
  vlmAutoClassification: features.includes('vlm_auto_classification'),
});

/**
 * 섹션 가시성 헬퍼 함수
 * features 배열 기반으로 가시성 결정 (drawing_type 미사용)
 *
 * @param _drawingType - 더 이상 사용하지 않음 (하위 호환성 유지)
 * @param features - 활성화된 기능 목록
 */
export const getSectionVisibility = (
  _drawingType?: string,
  features?: string[]
): SectionVisibility => {
  // features가 제공된 경우 features 기반 가시성 사용
  if (features && features.length > 0) {
    return featuresToVisibility(features);
  }

  // features가 비어있으면 기본 기능만 활성화
  return featuresToVisibility(DEFAULT_FEATURES);
};

/**
 * 모든 기능 목록 (UI에서 기능 선택 시 사용)
 */
export const ALL_AVAILABLE_FEATURES = [
  // 기본 검출
  { id: 'symbol_detection', label: '🎯 심볼 검출', group: '기본 검출' },
  { id: 'dimension_ocr', label: '📏 치수 OCR', group: '기본 검출' },
  { id: 'line_detection', label: '📐 선 검출', group: '기본 검출' },
  // GD&T / 기계
  { id: 'gdt_parsing', label: '🔧 GD&T 파싱', group: 'GD&T / 기계' },
  { id: 'relation_extraction', label: '🔗 심볼-치수 관계', group: 'GD&T / 기계' },
  { id: 'welding_symbol_parsing', label: '⚡ 용접 기호 파싱', group: 'GD&T / 기계' },
  { id: 'surface_roughness_parsing', label: '🔲 표면 거칠기 파싱', group: 'GD&T / 기계' },
  // P&ID
  { id: 'pid_connectivity', label: '🔀 P&ID 연결성', group: 'P&ID' },
  // BOM 생성
  { id: 'title_block_ocr', label: '📝 표제란 OCR', group: 'BOM 생성' },
  { id: 'quantity_extraction', label: '🔢 수량 추출', group: 'BOM 생성' },
  { id: 'balloon_matching', label: '🎈 벌룬 매칭', group: 'BOM 생성' },
  // 장기 로드맵
  { id: 'drawing_region_segmentation', label: '🗺️ 영역 세분화', group: '장기 로드맵' },
  { id: 'notes_extraction', label: '📋 노트 추출', group: '장기 로드맵' },
  { id: 'revision_comparison', label: '🔄 리비전 비교', group: '장기 로드맵' },
  { id: 'vlm_auto_classification', label: '🤖 VLM 자동 분류', group: '장기 로드맵' },
] as const;

// 하위 호환성을 위해 빈 객체 export (더 이상 사용하지 않음)
export const DRAWING_TYPE_SECTIONS: Record<string, SectionVisibility> = {};

// 페이지당 아이템 수
export const ITEMS_PER_PAGE = 7;
