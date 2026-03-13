/**
 * UnlinkedSessionsPanel - 미연결 세션 목록 및 연결 UI
 */

import { FileText, Loader2, Link2, Plus } from 'lucide-react';
import { Tooltip } from '../../../components/ui/Tooltip';
import type { SessionListItem } from '../../../lib/blueprintBomApi';

interface UnlinkedSessionsPanelProps {
  unlinkedSessions: SessionListItem[];
  isLoadingUnlinked: boolean;
  linkingSessionId: string | null;
  onLinkSession: (sessionId: string) => void;
}

export function UnlinkedSessionsPanel({
  unlinkedSessions,
  isLoadingUnlinked,
  linkingSessionId,
  onLinkSession,
}: UnlinkedSessionsPanelProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
      <div className="px-5 pt-4 pb-2 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-1">
          <Link2 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <Tooltip
            content="프로젝트에 포함되지 않은 기존 세션을 이 프로젝트에 연결할 수 있습니다. 연결된 세션은 위의 워크플로우에서 관리됩니다."
            position="bottom"
          >
            <h2 className="font-semibold text-gray-900 dark:text-white">기존 세션 연결</h2>
          </Tooltip>
          {!isLoadingUnlinked && unlinkedSessions.length > 0 && (
            <span className="px-1.5 py-0.5 rounded-full text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400">
              {unlinkedSessions.length}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          프로젝트에 포함되지 않은 기존 세션을 연결합니다.
        </p>
      </div>

      {isLoadingUnlinked ? (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
        </div>
      ) : unlinkedSessions.length === 0 ? (
        <div className="px-5 py-3 text-sm text-gray-400 dark:text-gray-500">
          미연결 세션이 없습니다.
        </div>
      ) : (
        <div className="divide-y divide-gray-100 dark:divide-gray-700">
          {unlinkedSessions.map((session) => (
            <div
              key={session.session_id}
              className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group"
            >
              <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5 text-gray-400 dark:text-gray-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                  {session.filename}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {session.created_at
                    ? new Date(session.created_at).toLocaleDateString('ko-KR')
                    : '날짜 없음'}
                  {' · '}검출: {session.detection_count}개
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
                    session.status === 'completed'
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                      : session.status === 'error'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  }`}
                >
                  {session.status}
                </span>
                <button
                  onClick={() => onLinkSession(session.session_id)}
                  disabled={linkingSessionId === session.session_id}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
                >
                  {linkingSessionId === session.session_id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Plus className="w-3.5 h-3.5" />
                  )}
                  연결
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
