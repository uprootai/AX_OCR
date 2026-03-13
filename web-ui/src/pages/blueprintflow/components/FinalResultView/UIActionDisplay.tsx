/**
 * FinalResultView — UIActionDisplay sub-component
 * Interactive Action UI with session management
 */

import { useState, useCallback } from 'react';
import Toast from '../../../../components/ui/Toast';
import { BLUEPRINT_AI_BOM_BASE } from '../../../../lib/api';
import type { ToastState } from './types';

interface UIActionDisplayProps {
  uiAction: { url?: string; label?: string };
  sessionId?: string;
  message?: string;
}

export function UIActionDisplay({
  uiAction,
  sessionId,
  message,
}: UIActionDisplayProps) {
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  const showToast = useCallback((toastMessage: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message: toastMessage, type });
  }, []);

  const handleDeleteSession = async () => {
    try {
      await fetch(`${BLUEPRINT_AI_BOM_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
      showToast('✓ 세션이 삭제되었습니다', 'success');
    } catch {
      showToast('✗ 세션 삭제 실패', 'error');
    }
  };

  return (
    <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
            🔗 {message || '액션이 필요합니다'}
          </div>
          <a
            href={uiAction.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
          >
            <span>🚀</span>
            {uiAction.label || '열기'}
            <span className="text-blue-200">↗</span>
          </a>
        </div>
        {sessionId && (
          <button
            onClick={handleDeleteSession}
            className="ml-3 px-2 py-1 text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
            title="세션 삭제"
          >
            🗑️ 세션 닫기
          </button>
        )}
      </div>
      {sessionId && (
        <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
          Session: {sessionId}
        </div>
      )}

      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.type === 'error' ? 15000 : 10000}
          onClose={() => setToast(prev => ({ ...prev, show: false }))}
        />
      )}
    </div>
  );
}
