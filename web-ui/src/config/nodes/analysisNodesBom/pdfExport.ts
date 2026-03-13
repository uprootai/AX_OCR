/**
 * PDF Export Node
 * P&ID 분석 결과를 PDF 리포트로 내보내기
 */

import type { NodeDefinition } from '../types';

export const pdfExportNode: Record<string, NodeDefinition> = {
  pdfexport: {
    type: 'pdfexport',
    label: 'PDF Export',
    category: 'analysis',
    color: '#dc2626',
    icon: 'FileText',
    description:
      'P&ID 분석 결과를 전문적인 PDF 리포트로 내보냅니다. Equipment, Valve, Checklist, Deviation 목록과 요약 통계를 포함합니다.',
    inputs: [
      {
        name: 'session_data',
        type: 'SessionData',
        description: '📊 워크플로우 분석 결과 (Equipment, Valve, Checklist 등)',
      },
      {
        name: 'image',
        type: 'Image',
        description: '📄 원본 이미지 (도면 번호 참조용)',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'pdf_url',
        type: 'string',
        description: '📁 생성된 PDF 파일 다운로드 URL',
      },
      {
        name: 'filename',
        type: 'string',
        description: '📝 PDF 파일명',
      },
      {
        name: 'summary',
        type: 'ExportSummary',
        description: '📊 내보내기 요약 (포함된 항목 수, 검증 상태 등)',
      },
    ],
    parameters: [
      {
        name: 'export_type',
        type: 'select',
        default: 'all',
        options: [
          { value: 'all', label: '전체', description: 'Equipment + Valve + Checklist + Deviation 모두 포함' },
          { value: 'valve', label: 'Valve List', description: '밸브 신호 목록만' },
          { value: 'equipment', label: 'Equipment List', description: '장비 목록만' },
          { value: 'checklist', label: 'Checklist', description: '설계 체크리스트만' },
          { value: 'deviation', label: 'Deviation', description: '편차 목록만' },
        ],
        description: '내보내기 범위 선택',
      },
      {
        name: 'project_name',
        type: 'string',
        default: '',
        description: 'PDF 표지에 표시될 프로젝트명',
        placeholder: '예: BWMS Project Alpha',
      },
      {
        name: 'drawing_no',
        type: 'string',
        default: '',
        description: '도면 번호',
        placeholder: '예: PID-001-A',
      },
      {
        name: 'include_rejected',
        type: 'boolean',
        default: false,
        description: '거부된 항목도 포함할지 여부',
      },
    ],
    examples: [
      'PID Analyzer → PDF Export → 전체 분석 리포트',
      'Design Checker → PDF Export → 체크리스트 리포트',
      'Equipment/Valve 검출 → PDF Export → 목록 리포트',
    ],
    usageTips: [
      '⭐ PID Analyzer 또는 Blueprint AI BOM 노드 출력을 연결하세요',
      '📋 export_type="all"로 전체 리포트를 한 번에 생성 가능',
      '🏢 project_name과 drawing_no를 입력하면 표지에 표시됩니다',
      '❌ include_rejected=false로 거부된 항목을 제외하면 최종 리포트에 적합',
      '📊 Executive Summary 섹션에서 검증 진행률과 Pass/Fail 현황 확인',
    ],
    recommendedInputs: [
      {
        from: 'pidanalyzer',
        field: 'session_data',
        reason: '⭐ P&ID 분석 결과 (Equipment, Valve, Connection 등) 포함',
      },
      {
        from: 'designchecker',
        field: 'checklist',
        reason: '설계 검증 체크리스트 결과 포함',
      },
      {
        from: 'blueprint-ai-bom',
        field: 'session',
        reason: 'Human-in-the-Loop 검증 결과 포함',
      },
    ],
  },
};
