/**
 * TemplateVersionHistory - 템플릿 버전 히스토리 컴포넌트
 *
 * 템플릿의 버전 히스토리를 표시하고 롤백 기능을 제공합니다.
 *
 * Features:
 * - 버전 목록 표시 (최신순)
 * - 버전 비교
 * - 롤백 기능
 * - 버전 상세 보기
 */

import { useState, useEffect, useCallback } from 'react';
import { History, RotateCcw, GitCompare, Eye, Clock, User, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

// ============ Types ============

export interface TemplateVersion {
  version: number;
  change_summary: string;
  node_count: number;
  edge_count: number;
  created_at: string;
  created_by?: string | null;
}

export interface TemplateVersionHistoryProps {
  templateId: string;
  templateName?: string;
  apiBaseUrl?: string;
  onRollback?: (version: number) => void;
  onCompare?: (versionA: number, versionB: number) => void;
  className?: string;
}

// ============ Component ============

export function TemplateVersionHistory({
  templateId,
  templateName,
  apiBaseUrl = 'http://localhost:5020',
  onRollback,
  onCompare,
  className = '',
}: TemplateVersionHistoryProps) {
  // State
  const [versions, setVersions] = useState<TemplateVersion[]>([]);
  const [currentVersion, setCurrentVersion] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedVersion, setExpandedVersion] = useState<number | null>(null);
  const [selectedVersions, setSelectedVersions] = useState<number[]>([]);
  const [isRollingBack, setIsRollingBack] = useState(false);

  // Fetch version history
  const fetchVersions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/templates/${templateId}/versions`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setVersions(data.versions || []);
      setCurrentVersion(data.current_version || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : '버전 목록 로드 실패');
    } finally {
      setIsLoading(false);
    }
  }, [templateId, apiBaseUrl]);

  useEffect(() => {
    if (templateId) {
      fetchVersions();
    }
  }, [templateId, fetchVersions]);

  // Handle rollback
  const handleRollback = useCallback(async (version: number) => {
    if (!confirm(`버전 ${version}으로 롤백하시겠습니까?\n현재 상태는 자동으로 백업됩니다.`)) {
      return;
    }

    setIsRollingBack(true);
    try {
      const response = await fetch(`${apiBaseUrl}/templates/${templateId}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_version: version }),
      });

      if (!response.ok) {
        throw new Error(`롤백 실패: HTTP ${response.status}`);
      }

      // Refresh versions
      await fetchVersions();
      onRollback?.(version);
    } catch (err) {
      setError(err instanceof Error ? err.message : '롤백 실패');
    } finally {
      setIsRollingBack(false);
    }
  }, [templateId, apiBaseUrl, fetchVersions, onRollback]);

  // Handle version selection for comparison
  const toggleVersionSelection = useCallback((version: number) => {
    setSelectedVersions(prev => {
      if (prev.includes(version)) {
        return prev.filter(v => v !== version);
      }
      // Max 2 selections
      if (prev.length >= 2) {
        return [prev[1], version];
      }
      return [...prev, version];
    });
  }, []);

  // Handle compare
  const handleCompare = useCallback(() => {
    if (selectedVersions.length === 2) {
      onCompare?.(selectedVersions[0], selectedVersions[1]);
    }
  }, [selectedVersions, onCompare]);

  // Format date
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  if (isLoading) {
    return (
      <Card className={`w-full ${className}`}>
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-500">버전 히스토리 로딩...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`w-full ${className}`}>
        <div className="flex items-center justify-center h-32 text-red-500">
          {error}
        </div>
      </Card>
    );
  }

  return (
    <Card className={`w-full ${className}`}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-blue-500" />
            <h3 className="text-sm font-semibold">버전 히스토리</h3>
            {templateName && (
              <Badge variant="outline" className="text-xs">
                {templateName}
              </Badge>
            )}
            <Badge variant="secondary" className="text-xs">
              현재 v{currentVersion}
            </Badge>
          </div>
          <div className="flex items-center gap-1">
            {selectedVersions.length === 2 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCompare}
                className="text-xs"
              >
                <GitCompare className="w-3 h-3 mr-1" />
                비교 (v{selectedVersions[0]} ↔ v{selectedVersions[1]})
              </Button>
            )}
            <Badge variant="outline" className="text-xs">
              {versions.length}개 버전
            </Badge>
          </div>
        </div>
      </div>

      {/* Version list */}
      <div className="max-h-96 overflow-auto">
        {versions.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            버전 히스토리가 없습니다
          </div>
        ) : (
          versions.map((version, index) => {
            const isLatest = index === 0;
            const isExpanded = expandedVersion === version.version;
            const isSelected = selectedVersions.includes(version.version);

            return (
              <div
                key={version.version}
                className={`border-b border-gray-100 dark:border-gray-800 ${
                  isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                }`}
              >
                {/* Version header */}
                <div
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                  onClick={() => setExpandedVersion(isExpanded ? null : version.version)}
                >
                  <div className="flex items-center gap-3">
                    {/* Checkbox for comparison */}
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => {
                        e.stopPropagation();
                        toggleVersionSelection(version.version);
                      }}
                      className="w-4 h-4 text-blue-600 rounded"
                    />

                    {/* Version badge */}
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={isLatest ? 'default' : 'outline'}
                        className="text-xs"
                      >
                        v{version.version}
                      </Badge>
                      {isLatest && (
                        <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                          최신
                        </Badge>
                      )}
                    </div>

                    {/* Change summary */}
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {version.change_summary || '변경 내용 없음'}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    {/* Stats */}
                    <span className="text-xs text-gray-400">
                      노드 {version.node_count} · 엣지 {version.edge_count}
                    </span>

                    {/* Date */}
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(version.created_at)}
                    </span>

                    {/* Expand icon */}
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-1 bg-gray-50 dark:bg-gray-800/50">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-500">
                        {version.created_by && (
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {version.created_by}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            // View version details (could open modal)
                            window.open(
                              `${apiBaseUrl}/templates/${templateId}/versions/${version.version}`,
                              '_blank'
                            );
                          }}
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          상세
                        </Button>

                        {!isLatest && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs text-orange-600 border-orange-300 hover:bg-orange-50"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRollback(version.version);
                            }}
                            disabled={isRollingBack}
                          >
                            {isRollingBack ? (
                              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            ) : (
                              <RotateCcw className="w-3 h-3 mr-1" />
                            )}
                            롤백
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer - Compare hint */}
      {versions.length >= 2 && selectedVersions.length < 2 && (
        <div className="p-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <p className="text-xs text-gray-500 text-center">
            두 버전을 선택하여 비교할 수 있습니다
          </p>
        </div>
      )}
    </Card>
  );
}

export default TemplateVersionHistory;
