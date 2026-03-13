/**
 * CategoryCard — 카테고리별 API 그룹 카드
 */

import {
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Square,
  Play,
} from 'lucide-react';
import { Button } from '../../ui/Button';
import type { APIInfo, ContainerStats, APIResourceSpec } from '../types';
import { CATEGORY_LABELS } from '../types';
import { APICard } from './APICard';

interface CategoryCardProps {
  category: string;
  apis: APIInfo[];
  isExpanded: boolean;
  onToggle: () => void;
  onCategoryAction: (category: string, action: 'stop' | 'start') => void;
  categoryActionLoading: string | null;
  containerStats: Record<string, ContainerStats>;
  apiResources: Record<string, APIResourceSpec>;
  getSpecId: (apiId: string) => string;
  onDeleteApi: (apiId: string) => void;
  onSingleApiAction: (api: APIInfo, action: 'stop' | 'start') => void;
  singleApiActionLoading: string | null;
  isGlobalLoading: boolean;
}

export function CategoryCard({
  category,
  apis,
  isExpanded,
  onToggle,
  onCategoryAction,
  categoryActionLoading,
  containerStats,
  apiResources,
  getSpecId,
  onDeleteApi,
  onSingleApiAction,
  singleApiActionLoading,
  isGlobalLoading,
}: CategoryCardProps) {
  const categoryHealthy = apis.filter(api => api.status === 'healthy').length;

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Category Header */}
      <div className="flex items-center justify-between p-3 bg-muted/30">
        <button onClick={onToggle} className="flex items-center gap-2 hover:opacity-70 transition-opacity">
          <span className="font-semibold">{CATEGORY_LABELS[category] || category}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            categoryHealthy === apis.length
              ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
              : categoryHealthy > 0
              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
              : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
          }`}>
            {categoryHealthy}/{apis.length}
          </span>
          {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </button>

        {/* Category Actions */}
        <div className="flex items-center gap-1">
          {categoryHealthy > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => { e.stopPropagation(); onCategoryAction(category, 'stop'); }}
              disabled={categoryActionLoading === category}
              className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              {categoryActionLoading === category ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Square className="h-3.5 w-3.5" />}
              <span className="ml-1 text-xs">Stop All</span>
            </Button>
          )}
          {categoryHealthy < apis.length && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => { e.stopPropagation(); onCategoryAction(category, 'start'); }}
              disabled={categoryActionLoading === category}
              className="h-7 px-2 text-green-600 hover:text-green-700 hover:bg-green-50"
            >
              {categoryActionLoading === category ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              <span className="ml-1 text-xs">Start All</span>
            </Button>
          )}
        </div>
      </div>

      {/* Category Content */}
      {isExpanded && (
        <div className="p-3 grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          {apis.map(api => (
            <APICard
              key={api.id}
              api={api}
              containerStats={containerStats[api.id]}
              resourceSpec={apiResources[getSpecId(api.id)]}
              onDelete={() => onDeleteApi(api.id)}
              onAction={onSingleApiAction}
              isActionLoading={singleApiActionLoading === api.id}
              isGlobalLoading={isGlobalLoading}
            />
          ))}
        </div>
      )}
    </div>
  );
}
