/**
 * ProjectCard - 프로젝트 카드 컴포넌트
 */

import { Link } from 'react-router-dom';
import {
  FolderOpen,
  FileText,
  CheckCircle,
  Clock,
  Building,
  LayoutTemplate,
  ChevronRight,
} from 'lucide-react';
import type { Project } from '../../../lib/api';

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const progressPercent =
    project.session_count > 0
      ? Math.round((project.completed_count / project.session_count) * 100)
      : 0;

  return (
    <Link
      to={`/projects/${project.project_id}`}
      className="block bg-white rounded-xl border shadow-sm hover:shadow-md transition-all group"
    >
      <div className="p-5">
        {/* 헤더 */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FolderOpen className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                {project.name}
              </h3>
              <div className="flex items-center gap-1 text-sm text-gray-500 mt-0.5">
                <Building className="w-3.5 h-3.5" />
                <span>{project.customer}</span>
              </div>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" />
        </div>

        {/* 설명 */}
        {project.description && (
          <p className="text-sm text-gray-600 mt-3 line-clamp-2">
            {project.description}
          </p>
        )}

        {/* 통계 */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-gray-600">
              <FileText className="w-4 h-4" />
              <span className="text-lg font-bold">{project.session_count}</span>
            </div>
            <span className="text-xs text-gray-500">세션</span>
          </div>
          <div className="text-center p-2 bg-green-50 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-green-600">
              <CheckCircle className="w-4 h-4" />
              <span className="text-lg font-bold">{project.completed_count}</span>
            </div>
            <span className="text-xs text-gray-500">완료</span>
          </div>
          <div className="text-center p-2 bg-yellow-50 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-yellow-600">
              <Clock className="w-4 h-4" />
              <span className="text-lg font-bold">{project.pending_count}</span>
            </div>
            <span className="text-xs text-gray-500">대기</span>
          </div>
        </div>

        {/* 진행률 */}
        {project.session_count > 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">진행률</span>
              <span className="font-medium text-gray-900">{progressPercent}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        )}

        {/* 템플릿 정보 */}
        {project.default_template_name && (
          <div className="flex items-center gap-2 mt-4 text-sm text-gray-500">
            <LayoutTemplate className="w-4 h-4" />
            <span>템플릿: {project.default_template_name}</span>
          </div>
        )}
      </div>

      {/* 푸터 */}
      <div className="px-5 py-3 border-t bg-gray-50 rounded-b-xl">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>생성: {new Date(project.created_at).toLocaleDateString('ko-KR')}</span>
          <span>수정: {new Date(project.updated_at).toLocaleDateString('ko-KR')}</span>
        </div>
      </div>
    </Link>
  );
}

export default ProjectCard;
