/**
 * ActiveFeaturesSection - 활성화된 기능 섹션
 * 빌더에서 설정한 기능 목록을 표시
 *
 * 2025-12-26: SSOT 리팩토링 - features 정의를 config/features에서 import
 */

import { FEATURE_BADGE_CONFIG } from '../../../config/features';

interface ActiveFeaturesSectionProps {
  features: string[];
}

export function ActiveFeaturesSection({ features }: ActiveFeaturesSectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        🔧 활성화된 기능
        <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
          (빌더에서 설정됨)
        </span>
      </h2>
      <div className="flex flex-wrap gap-2">
        {features.map(feature => {
          const config = FEATURE_BADGE_CONFIG[feature];
          if (!config) return null;
          return (
            <span
              key={feature}
              className={`px-3 py-1.5 ${config.bgClass} ${config.textClass} rounded-full text-sm flex items-center gap-1`}
            >
              {config.icon} {config.label}
            </span>
          );
        })}
      </div>
      <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
        💡 워크플로우 빌더에서 선택한 기능에 따라 아래 섹션이 동적으로 표시됩니다.
      </p>
    </section>
  );
}
