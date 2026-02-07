/**
 * ProjectCreateModal - 프로젝트 생성 모달
 */

import { useState, useEffect } from 'react';
import {
  X,
  FolderPlus,
  Building,
  FileText,
  LayoutTemplate,
  Loader2,
} from 'lucide-react';
import { projectApi, type ProjectCreate } from '../../../lib/api';

interface Template {
  template_id: string;
  name: string;
  description?: string;
}

interface ProjectCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (projectId: string) => void;
  templates?: Template[];
}

export function ProjectCreateModal({
  isOpen,
  onClose,
  onCreated,
  templates = [],
}: ProjectCreateModalProps) {
  const [formData, setFormData] = useState<ProjectCreate>({
    name: '',
    customer: '',
    description: '',
    project_type: 'bom_quotation' as const,
    default_template_id: '',
    default_features: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 모달 열릴 때 폼 초기화
  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        customer: '',
        description: '',
        project_type: 'bom_quotation' as const,
        default_template_id: '',
        default_features: [],
      });
      setError(null);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.customer.trim()) {
      setError('프로젝트명과 고객사명은 필수입니다.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await projectApi.create({
        ...formData,
        default_template_id: formData.default_template_id || undefined,
      });
      onCreated(result.project_id);
      onClose();
    } catch (err) {
      console.error('Failed to create project:', err);
      setError('프로젝트 생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 배경 */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* 모달 */}
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-5 border-b">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FolderPlus className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">새 프로젝트</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* 프로젝트 타입 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프로젝트 타입 <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, project_type: 'bom_quotation' })}
                className={`p-3 rounded-lg border-2 text-left transition-colors ${
                  formData.project_type === 'bom_quotation'
                    ? 'border-pink-500 bg-pink-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-sm">BOM 견적</div>
                <div className="text-xs text-gray-500 mt-0.5">BOM 기반 부품 분석 · 견적</div>
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, project_type: 'pid_detection' })}
                className={`p-3 rounded-lg border-2 text-left transition-colors ${
                  formData.project_type === 'pid_detection'
                    ? 'border-cyan-500 bg-cyan-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-sm">P&ID 검출</div>
                <div className="text-xs text-gray-500 mt-0.5">심볼 검출 · GT 비교</div>
              </button>
            </div>
          </div>

          {/* 프로젝트명 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              프로젝트명 <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="예: BWMS 2025 신규"
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          {/* 고객사 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              고객사 <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={formData.customer}
                onChange={(e) =>
                  setFormData({ ...formData, customer: e.target.value })
                }
                placeholder="예: 파나시아"
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          {/* 설명 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              설명
            </label>
            <textarea
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="프로젝트에 대한 설명을 입력하세요"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
            />
          </div>

          {/* 기본 템플릿 */}
          {templates.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                기본 템플릿
              </label>
              <div className="relative">
                <LayoutTemplate className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <select
                  value={formData.default_template_id}
                  onChange={(e) =>
                    setFormData({ ...formData, default_template_id: e.target.value })
                  }
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
                >
                  <option value="">템플릿 선택 (선택사항)</option>
                  {templates.map((template) => (
                    <option key={template.template_id} value={template.template_id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* 에러 메시지 */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {error}
            </div>
          )}

          {/* 버튼 */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  생성 중...
                </>
              ) : (
                '프로젝트 생성'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ProjectCreateModal;
