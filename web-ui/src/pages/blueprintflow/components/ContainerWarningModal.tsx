/**
 * ContainerWarningModal Component
 * 컨테이너 상태 경고 모달
 */

import { useTranslation } from 'react-i18next';
import { AlertTriangle } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import type { ContainerWarningModalState } from '../types';

interface ContainerWarningModalProps {
  modalState: ContainerWarningModalState;
  onClose: () => void;
  onStartContainers: (containerNames: string[]) => void;
}

export function ContainerWarningModal({
  modalState,
  onClose,
  onStartContainers,
}: ContainerWarningModalProps) {
  const { t } = useTranslation();

  if (!modalState.isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-amber-50 dark:bg-amber-900/30 px-6 py-4 border-b border-amber-200 dark:border-amber-800">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
            <h3 className="text-lg font-semibold text-amber-900 dark:text-amber-100">
              {t('blueprintflow.containersNotRunning') || '컨테이너가 실행 중이 아닙니다'}
            </h3>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {t('blueprintflow.containersNotRunningDesc') || '다음 서비스가 중지되어 있어 워크플로우를 실행할 수 없습니다:'}
          </p>
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 mb-4 max-h-40 overflow-y-auto">
            {modalState.stoppedContainers.map((name, idx) => (
              <div key={idx} className="flex items-center gap-2 py-1">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-sm font-mono text-gray-700 dark:text-gray-300">{name}</span>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            {t('blueprintflow.containersStartHint') || 'Dashboard에서 서비스를 시작하거나, 아래 버튼을 클릭하여 자동으로 시작할 수 있습니다.'}
          </p>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={modalState.isStarting}
          >
            {t('common.cancel') || '취소'}
          </Button>
          <Button
            onClick={() => onStartContainers(modalState.stoppedContainers)}
            disabled={modalState.isStarting}
            className="bg-amber-600 hover:bg-amber-700"
          >
            {modalState.isStarting
              ? (t('blueprintflow.startingContainers') || '시작 중...')
              : (t('blueprintflow.startAndExecute') || '시작 후 실행')}
          </Button>
        </div>
      </div>
    </div>
  );
}
