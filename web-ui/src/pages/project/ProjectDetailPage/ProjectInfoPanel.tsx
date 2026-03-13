/**
 * ProjectInfoPanel - 프로젝트 정보 카드 + 진행 현황 카드
 */

import { FileText, CheckCircle, Clock, LayoutTemplate } from 'lucide-react';
import { Tooltip } from '../../../components/ui/Tooltip';
import type { ProjectDetail } from '../../../lib/blueprintBomApi';
import { FEATURE_DESCRIPTIONS } from './constants';

interface ProjectInfoPanelProps {
  project: ProjectDetail;
  doneCount: number;
  progressPercent: number;
}

export function ProjectInfoPanel({ project, doneCount, progressPercent }: ProjectInfoPanelProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      {/* 프로젝트 정보 */}
      <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">프로젝트 정보</h2>
        {project.description && (
          <p className="text-gray-600 dark:text-gray-400 mb-4">{project.description}</p>
        )}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Tooltip content="프로젝트가 처음 생성된 날짜입니다" position="right">
              <p className="text-sm text-gray-500 dark:text-gray-400">생성일</p>
            </Tooltip>
            <p className="font-medium text-gray-900 dark:text-white">
              {new Date(project.created_at).toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>
          <div>
            <Tooltip content="프로젝트 데이터가 마지막으로 변경된 시점입니다" position="right">
              <p className="text-sm text-gray-500 dark:text-gray-400">최근 수정</p>
            </Tooltip>
            <p className="font-medium text-gray-900 dark:text-white">
              {new Date(project.updated_at).toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>
          {project.bom_source && (
            <div>
              <Tooltip
                content="업로드된 BOM(부품 목록) PDF 파일명입니다. BOM 견적 워크플로우에서 사용됩니다."
                position="bottom"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400">BOM 소스</p>
              </Tooltip>
              <p
                className="font-medium text-gray-900 dark:text-white truncate"
                title={project.bom_source}
              >
                {project.bom_source}
              </p>
            </div>
          )}
          {project.drawing_folder && (
            <div>
              <Tooltip
                content="도면 파일이 저장된 서버 경로입니다. BOM 항목과 도면 자동 매칭에 사용됩니다."
                position="bottom"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400">도면 폴더</p>
              </Tooltip>
              <p
                className="font-medium text-gray-900 dark:text-white truncate"
                title={project.drawing_folder}
              >
                {project.drawing_folder}
              </p>
            </div>
          )}
          {project.bom_item_count > 0 && (
            <div>
              <Tooltip
                content="BOM PDF에서 파싱된 부품 총 수입니다. 괄호 안은 견적이 완료된 항목 수입니다."
                position="bottom"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400">BOM 아이템</p>
              </Tooltip>
              <p className="font-medium text-gray-900 dark:text-white">
                {project.bom_item_count}개
                {project.quoted_count > 0 && (
                  <span className="text-sm text-gray-500 dark:text-gray-400 ml-1">
                    (견적 {project.quoted_count}개)
                  </span>
                )}
              </p>
            </div>
          )}
          {project.total_quotation > 0 && (
            <div>
              <Tooltip
                content="모든 부품의 견적 합계 금액입니다 (재료비 + 가공비 + 부가세 포함)"
                position="bottom"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400">총 견적액</p>
              </Tooltip>
              <p className="font-medium text-gray-900 dark:text-white">
                ₩{project.total_quotation.toLocaleString('ko-KR')}
              </p>
            </div>
          )}
          {project.default_template_name && (
            <div className="col-span-2">
              <Tooltip
                content="새 세션 생성 시 자동 적용되는 BlueprintFlow 워크플로우 템플릿입니다. 검출·분석 파이프라인을 정의합니다."
                position="bottom"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400">기본 템플릿</p>
              </Tooltip>
              <div className="flex items-center gap-2 font-medium text-blue-600 dark:text-blue-400">
                <LayoutTemplate className="w-4 h-4" />
                {project.default_template_name}
              </div>
            </div>
          )}
          {project.default_features.length > 0 && (
            <div className="col-span-2">
              <Tooltip
                content="세션에서 자동으로 활성화되는 분석 기능 목록입니다. 각 뱃지 위에 마우스를 올리면 상세 설명을 볼 수 있습니다."
                position="bottom"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1.5">활성 기능</p>
              </Tooltip>
              <div className="flex flex-wrap gap-1.5">
                {project.default_features.map((feature) => (
                  <Tooltip
                    key={feature}
                    content={FEATURE_DESCRIPTIONS[feature] || feature}
                    position="bottom"
                  >
                    <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-md cursor-help">
                      {feature}
                    </span>
                  </Tooltip>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 진행 현황 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">진행 현황</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Tooltip
              content="프로젝트에 연결된 도면 분석 세션의 총 수입니다. 각 세션은 하나의 도면 이미지에 대한 분석 단위입니다."
              position="bottom"
            >
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                <FileText className="w-4 h-4" />
                <span>전체 세션</span>
              </div>
            </Tooltip>
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              {project.session_count}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <Tooltip
              content="검출 및 검증이 모두 완료된 세션 수입니다. completed와 verified 상태를 포함합니다."
              position="bottom"
            >
              <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span>완료</span>
              </div>
            </Tooltip>
            <span className="text-xl font-bold text-green-600 dark:text-green-400">
              {doneCount}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <Tooltip
              content="아직 분석이 시작되지 않았거나 검증이 진행 중인 세션 수입니다."
              position="bottom"
            >
              <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
                <Clock className="w-4 h-4" />
                <span>대기</span>
              </div>
            </Tooltip>
            <span className="text-xl font-bold text-yellow-600 dark:text-yellow-400">
              {project.pending_count}
            </span>
          </div>
          <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between text-sm mb-1">
              <Tooltip
                content="완료된 세션의 비율입니다. 100%가 되면 모든 도면 분석이 완료된 것입니다."
                position="bottom"
              >
                <span className="text-gray-600 dark:text-gray-400">진행률</span>
              </Tooltip>
              <span className="font-medium text-gray-900 dark:text-white">{progressPercent}%</span>
            </div>
            <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 dark:bg-blue-400 transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
