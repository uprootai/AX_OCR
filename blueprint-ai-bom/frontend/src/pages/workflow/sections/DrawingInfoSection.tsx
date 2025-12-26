/**
 * DrawingInfoSection - 도면 정보 섹션
 * 빌더에서 설정한 도면 타입 정보를 표시
 */

import { InfoTooltip } from '../../../components/Tooltip';

interface DrawingInfoSectionProps {
  drawingType: string;
}

const DRAWING_TYPE_CONFIG: Record<string, { icon: string; label: string; description: string }> = {
  // 새로운 타입 (2025-12-22)
  dimension: { icon: '📏', label: '치수 도면', description: 'OCR 치수 인식 중심' },
  electrical_panel: { icon: '🔌', label: '전기 제어판', description: 'YOLO 심볼 검출' },
  dimension_bom: { icon: '📐', label: '치수 + BOM', description: 'OCR + 수동 라벨링' },
  // 기존 타입
  pid: { icon: '🔬', label: 'P&ID (배관계장도)', description: 'P&ID 심볼 + 라인' },
  assembly: { icon: '🔩', label: '조립도', description: 'YOLO + OCR' },
  // 레거시 타입
  mechanical: { icon: '⚙️', label: '기계 부품도', description: '기계 부품 분석' },
  mechanical_part: { icon: '⚙️', label: '기계 부품도', description: '기계 부품 분석' },
  electrical: { icon: '⚡', label: '전기 회로도', description: '전기 회로 분석' },
  electrical_circuit: { icon: '⚡', label: '전기 회로도', description: '전기 회로 분석' },
  architectural: { icon: '🏗️', label: '건축 도면', description: '건축 도면 분석' },
};

export function DrawingInfoSection({ drawingType }: DrawingInfoSectionProps) {
  const config = DRAWING_TYPE_CONFIG[drawingType];
  if (!config) return null;

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1">
        📋 도면 정보
        <InfoTooltip content="빌더에서 설정한 도면 타입입니다. 분석 파이프라인이 이 타입에 맞게 최적화됩니다." position="right" />
      </h2>
      <div className="bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <span className="font-medium text-indigo-800 dark:text-indigo-200">
              {config.label}
            </span>
            <span className="ml-2 text-sm text-indigo-600 dark:text-indigo-400">
              (빌더에서 설정됨)
            </span>
          </div>
        </div>
        <div className="text-xs text-indigo-600 dark:text-indigo-400 max-w-[200px] text-right">
          {config.description}
        </div>
      </div>
    </section>
  );
}
