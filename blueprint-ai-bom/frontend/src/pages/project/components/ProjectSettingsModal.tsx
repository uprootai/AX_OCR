/**
 * ProjectSettingsModal - 프로젝트 설정 편집 모달
 */

import { useState, useEffect } from 'react';
import { X, Settings, Loader2 } from 'lucide-react';
import { projectApi, type ProjectDetail, type ProjectUpdate } from '../../../lib/api';

const AVAILABLE_FEATURES = [
  { key: 'verification', label: '검증 (Verification)' },
  { key: 'gt_comparison', label: 'GT 비교 (GT Comparison)' },
  { key: 'bom_generation', label: 'BOM 생성 (BOM Generation)' },
  { key: 'dimension_extraction', label: '치수 추출 (Dimension Extraction)' },
] as const;

interface ProjectSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  project: ProjectDetail;
  onUpdated: () => void;
}

export function ProjectSettingsModal({
  isOpen,
  onClose,
  project,
  onUpdated,
}: ProjectSettingsModalProps) {
  const [formData, setFormData] = useState<ProjectUpdate>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 모달 열릴 때 project 데이터로 폼 초기화
  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: project.name,
        customer: project.customer,
        description: project.description || '',
        project_type: project.project_type,
        default_features: [...project.default_features],
      });
      setError(null);
    }
  }, [isOpen, project]);

  const handleFeatureToggle = (feature: string) => {
    const current = formData.default_features || [];
    const next = current.includes(feature)
      ? current.filter((f) => f !== feature)
      : [...current, feature];
    setFormData({ ...formData, default_features: next });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name?.trim() || !formData.customer?.trim()) {
      setError('프로젝트명과 고객사명은 필수입니다.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await projectApi.update(project.project_id, formData);
      onUpdated();
      onClose();
    } catch (err) {
      console.error('Failed to update project:', err);
      setError('프로젝트 설정 저장에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <Settings className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">프로젝트 설정</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* 프로젝트 타입 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              프로젝트 타입
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, project_type: 'bom_quotation' })}
                className={`p-3 rounded-lg border-2 text-left transition-colors ${
                  formData.project_type === 'bom_quotation'
                    ? 'border-pink-500 bg-pink-50 dark:bg-pink-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <div className="font-medium text-sm text-gray-900 dark:text-white">BOM 견적</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">BOM 기반 부품 분석 · 견적</div>
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, project_type: 'pid_detection' })}
                className={`p-3 rounded-lg border-2 text-left transition-colors ${
                  formData.project_type === 'pid_detection'
                    ? 'border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <div className="font-medium text-sm text-gray-900 dark:text-white">P&ID 검출</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">심볼 검출 · GT 비교</div>
              </button>
            </div>
          </div>

          {/* 프로젝트명 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              프로젝트명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* 고객사 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              고객사 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.customer || ''}
              onChange={(e) => setFormData({ ...formData, customer: e.target.value })}
              className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* 설명 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              설명
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
            />
          </div>

          {/* 기본 기능 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              기본 기능
            </label>
            <div className="space-y-2">
              {AVAILABLE_FEATURES.map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={(formData.default_features || []).includes(key)}
                    onChange={() => handleFeatureToggle(key)}
                    className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-blue-500 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 에러 */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {/* 버튼 */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
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
                  저장 중...
                </>
              ) : (
                '저장'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
