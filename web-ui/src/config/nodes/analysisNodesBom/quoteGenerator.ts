/**
 * Quote Generator Node
 * BOM 기반 자동 견적 생성
 */

import type { NodeDefinition } from '../types';

export const quoteGeneratorNode: Record<string, NodeDefinition> = {
  quotegenerator: {
    type: 'quotegenerator',
    label: 'Quote Generator',
    category: 'analysis',
    color: '#dc2626',
    icon: 'Calculator',
    description:
      'BOM 기반 자동 견적 생성. 재료비, 가공비, 마진율을 적용하여 견적서를 생성합니다.',
    profiles: {
      default: 'bearing',
      available: [
        {
          name: 'bearing',
          label: '베어링 견적',
          description: 'DSE Bearing 견적 최적화',
          params: {
            currency: 'KRW',
            material_markup: 15,
            labor_markup: 20,
            tax_rate: 10,
            include_tax: true,
            quantity_discount: true,
          },
        },
        {
          name: 'standard',
          label: '표준 견적',
          description: '일반 기계 부품 견적',
          params: {
            currency: 'KRW',
            material_markup: 10,
            labor_markup: 15,
            tax_rate: 10,
            include_tax: true,
            quantity_discount: false,
          },
        },
        {
          name: 'export',
          label: '수출용 견적',
          description: '해외 수출용 (USD)',
          params: {
            currency: 'USD',
            material_markup: 20,
            labor_markup: 25,
            tax_rate: 0,
            include_tax: false,
            quantity_discount: true,
          },
        },
      ],
    },
    inputs: [
      {
        name: 'bom',
        type: 'BOMEntry[]',
        description: '📋 BOM Matcher 출력 (부품 목록)',
      },
      {
        name: 'drawing_info',
        type: 'DrawingInfo',
        description: '📄 도면 메타 정보 (도면번호, 품명)',
        optional: true,
      },
      {
        name: 'pricing_table',
        type: 'PricingTable',
        description: '💰 커스텀 단가 테이블 (미입력 시 기본값)',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'quote',
        type: 'QuoteDocument',
        description: '📜 견적서 문서',
      },
      {
        name: 'line_items',
        type: 'QuoteLineItem[]',
        description: '📝 견적 항목 목록',
      },
      {
        name: 'summary',
        type: 'QuoteSummary',
        description: '📊 견적 요약 (총액, 세금 등)',
      },
      {
        name: 'total_cost',
        type: 'number',
        description: '💵 총 견적 금액',
      },
      {
        name: 'quote_number',
        type: 'string',
        description: '🔢 견적 번호',
      },
    ],
    parameters: [
      {
        name: 'currency',
        type: 'select',
        default: 'KRW',
        options: [
          { value: 'KRW', label: '원화 (₩)', description: '한국 원' },
          { value: 'USD', label: '달러 ($)', description: '미국 달러' },
          { value: 'EUR', label: '유로 (€)', description: '유럽 유로' },
          { value: 'JPY', label: '엔화 (¥)', description: '일본 엔' },
        ],
        description: '통화 단위',
      },
      {
        name: 'material_markup',
        type: 'number',
        default: 15,
        min: 0,
        max: 100,
        step: 1,
        description: '재료비 마진율 (%)',
      },
      {
        name: 'labor_markup',
        type: 'number',
        default: 20,
        min: 0,
        max: 100,
        step: 1,
        description: '가공비 마진율 (%)',
      },
      {
        name: 'tax_rate',
        type: 'number',
        default: 10,
        min: 0,
        max: 30,
        step: 0.5,
        description: '부가세율 (%)',
      },
      {
        name: 'include_tax',
        type: 'boolean',
        default: true,
        description: '부가세 포함 여부',
      },
      {
        name: 'quantity_discount',
        type: 'boolean',
        default: true,
        description: '수량 할인 적용 (10개↑ 5%, 50개↑ 10%)',
      },
      {
        name: 'validity_days',
        type: 'number',
        default: 30,
        min: 7,
        max: 90,
        step: 1,
        description: '견적 유효 기간 (일)',
      },
      {
        name: 'output_format',
        type: 'select',
        default: 'json',
        options: [
          { value: 'json', label: 'JSON', description: '구조화된 데이터' },
          { value: 'pdf', label: 'PDF', description: '견적서 PDF' },
          { value: 'excel', label: 'Excel', description: '견적서 Excel' },
        ],
        description: '출력 형식',
      },
    ],
    examples: [
      'BOM Matcher → Quote Generator → 견적서 JSON',
      '도면 분석 → BOM → 견적서 PDF 생성',
      '부품 10개, 재료비 500만원 → 견적 700만원 (마진 포함)',
    ],
    usageTips: [
      '⭐ BOM Matcher 출력을 입력으로 연결',
      '💰 material_markup/labor_markup으로 마진율 조정',
      '📊 수량 할인: 10개↑ 5%, 20개↑ 7%, 50개↑ 10%, 100개↑ 15%',
      '📄 PDF/Excel 출력으로 고객 제출용 견적서 생성',
      '🔧 pricing_table로 커스텀 단가 적용 가능',
    ],
    recommendedInputs: [
      {
        from: 'bommatcher',
        field: 'bom',
        reason: '⭐ BOM Matcher 출력 (부품 목록)',
      },
      {
        from: 'bommatcher',
        field: 'drawing_info',
        reason: '도면 메타 정보 (도면번호)',
      },
    ],
  },
};
