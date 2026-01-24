/**
 * DeployTemplateModal - 템플릿 배포 모달
 * BlueprintFlow 템플릿을 고객용 세션으로 배포
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Rocket, Copy, Check, ExternalLink, Lock, Unlock, Calendar } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { workflowSessionApi, type WorkflowSessionResponse, type WorkflowDefinition } from '../../../lib/api';

// Blueprint AI BOM 프론트엔드 URL (CustomerSessionPage가 있는 곳)
const BLUEPRINT_AI_BOM_FRONTEND_URL = import.meta.env.VITE_BLUEPRINT_AI_BOM_URL || 'http://localhost:3000';

interface DeployTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  template: {
    nameKey: string;
    descKey: string;
    workflow: WorkflowDefinition;
  };
}

type LockLevel = 'full' | 'parameters' | 'none';

export function DeployTemplateModal({ isOpen, onClose, template }: DeployTemplateModalProps) {
  const { t } = useTranslation();
  const [customerName, setCustomerName] = useState('');
  const [lockLevel, setLockLevel] = useState<LockLevel>('full');
  const [expiresInDays, setExpiresInDays] = useState(30);
  const [isDeploying, setIsDeploying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WorkflowSessionResponse | null>(null);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleDeploy = async () => {
    if (!customerName.trim()) {
      setError('고객명을 입력해주세요');
      return;
    }

    setIsDeploying(true);
    setError(null);

    try {
      const response = await workflowSessionApi.createFromWorkflow({
        name: template.workflow.name,
        description: template.workflow.description,
        nodes: template.workflow.nodes,
        edges: template.workflow.edges,
        lock_level: lockLevel,
        customer_name: customerName,
        expires_in_days: expiresInDays,
      });

      setResult(response);
    } catch (err) {
      console.error('Failed to deploy template:', err);
      setError('템플릿 배포에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsDeploying(false);
    }
  };

  const getShareUrl = () => {
    if (!result) return '';
    return `${BLUEPRINT_AI_BOM_FRONTEND_URL}${result.share_url}?token=${result.access_token}`;
  };

  const handleCopyUrl = () => {
    if (!result) return;
    navigator.clipboard.writeText(getShareUrl());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenInNewTab = () => {
    if (!result) return;
    window.open(getShareUrl(), '_blank');
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    setCustomerName('');
    setLockLevel('full');
    setExpiresInDays(30);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Rocket className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              템플릿 배포
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 컨텐츠 */}
        <div className="p-4">
          {!result ? (
            <>
              {/* 템플릿 정보 */}
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mb-4">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  {t(`blueprintflow.${template.nameKey}`)}
                </p>
                <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                  {template.workflow.nodes.length} 노드 | {template.workflow.edges.length} 연결
                </p>
              </div>

              {/* 고객명 */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  고객명 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="예: PANASIA, TECHCROSS, DSE Bearing"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              {/* 잠금 수준 */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  권한 설정
                </label>
                <div className="space-y-2">
                  <label className="flex items-start gap-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                    <input
                      type="radio"
                      name="lockLevel"
                      value="full"
                      checked={lockLevel === 'full'}
                      onChange={() => setLockLevel('full')}
                      className="mt-0.5"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Lock className="w-4 h-4 text-red-500" />
                        <span className="font-medium text-gray-900 dark:text-white">완전 잠금</span>
                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">권장</span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        고객은 이미지 업로드와 실행만 가능합니다. 워크플로우 수정 불가.
                      </p>
                    </div>
                  </label>

                  <label className="flex items-start gap-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                    <input
                      type="radio"
                      name="lockLevel"
                      value="parameters"
                      checked={lockLevel === 'parameters'}
                      onChange={() => setLockLevel('parameters')}
                      className="mt-0.5"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Unlock className="w-4 h-4 text-yellow-500" />
                        <span className="font-medium text-gray-900 dark:text-white">파라미터 수정 허용</span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        고객이 일부 파라미터(confidence 등)를 조정할 수 있습니다.
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              {/* 만료 기간 */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  만료 기간
                </label>
                <select
                  value={expiresInDays}
                  onChange={(e) => setExpiresInDays(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value={7}>7일</option>
                  <option value={14}>14일</option>
                  <option value={30}>30일</option>
                  <option value={60}>60일</option>
                  <option value={90}>90일</option>
                  <option value={365}>1년</option>
                </select>
              </div>

              {/* 에러 메시지 */}
              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400 mb-4">
                  {error}
                </div>
              )}

              {/* 버튼 */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleClose}
                  className="flex-1"
                >
                  취소
                </Button>
                <Button
                  onClick={handleDeploy}
                  disabled={isDeploying}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                >
                  {isDeploying ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      배포 중...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Rocket className="w-4 h-4" />
                      배포 링크 생성
                    </span>
                  )}
                </Button>
              </div>
            </>
          ) : (
            /* 배포 성공 결과 */
            <div className="text-center py-4">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-green-500" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                배포 완료!
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                고객용 링크가 생성되었습니다.
              </p>

              {/* 공유 URL */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-4">
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 text-left">
                  공유 URL
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={getShareUrl()}
                    className="flex-1 px-3 py-2 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-lg text-sm"
                  />
                  <button
                    onClick={handleCopyUrl}
                    className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* 접근 토큰 */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 mb-4 text-left">
                <label className="block text-xs font-medium text-yellow-700 dark:text-yellow-400 mb-1">
                  접근 토큰 (안전하게 보관하세요)
                </label>
                <code className="text-xs text-yellow-800 dark:text-yellow-300 break-all">
                  {result.access_token}
                </code>
              </div>

              {/* 만료 정보 */}
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                <Calendar className="w-3 h-3 inline mr-1" />
                만료: {new Date(result.expires_at).toLocaleDateString('ko-KR')}
              </p>

              {/* 버튼 */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleClose}
                  className="flex-1"
                >
                  닫기
                </Button>
                <Button
                  onClick={handleOpenInNewTab}
                  className="flex-1"
                >
                  <ExternalLink className="w-4 h-4 mr-1" />
                  새 탭에서 열기
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DeployTemplateModal;
