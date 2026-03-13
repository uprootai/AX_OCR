/**
 * ProjectDetailPage 상수 및 유틸리티
 */

import type { ProjectDetail } from '../../../lib/blueprintBomApi';

/** 활성 기능(feature) 이름 → 설명 */
export const FEATURE_DESCRIPTIONS: Record<string, string> = {
  symbol_verification: 'YOLO 검출 결과를 사람이 확인하고 승인/반려하는 Human-in-the-Loop 검증 기능',
  gt_comparison: 'Ground Truth 데이터와 검출 결과를 비교하여 정확도(mAP, IoU)를 측정',
  bom_generation: '승인된 검출 결과를 기반으로 부품 목록(BOM)과 견적서를 자동 생성',
  dimension_extraction: '도면에서 치수 정보를 OCR로 추출하여 부품 크기·공차 분석',
  verification: '검출 결과에 대한 사람의 검증(승인/반려) 워크플로우',
};

/** project_type → 설명 */
export const TYPE_DESCRIPTIONS: Record<string, string> = {
  pid_detection: 'P&ID(배관계장도) 도면의 심볼을 자동 검출·분석하는 프로젝트',
  bom_quotation: 'BOM(부품 목록) PDF를 파싱하고 도면 매칭 후 견적을 산출하는 프로젝트',
  general: '범용 도면 분석 프로젝트',
};

export interface TypeColors {
  bg: string;
  icon: string;
  badge: string;
  label: string;
}

/** project_type에 따른 색상 반환 */
export function getTypeColors(project: ProjectDetail | null): TypeColors {
  if (project?.project_type === 'pid_detection') {
    return {
      bg: 'bg-cyan-100 dark:bg-cyan-900/30',
      icon: 'text-cyan-600 dark:text-cyan-400',
      badge: 'bg-cyan-100 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300',
      label: 'P&ID',
    };
  }
  if (project?.project_type === 'bom_quotation') {
    return {
      bg: 'bg-pink-100 dark:bg-pink-900/30',
      icon: 'text-pink-600 dark:text-pink-400',
      badge: 'bg-pink-100 dark:bg-pink-900/50 text-pink-700 dark:text-pink-300',
      label: 'BOM',
    };
  }
  return {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    icon: 'text-blue-600 dark:text-blue-400',
    badge: 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300',
    label: '일반',
  };
}
