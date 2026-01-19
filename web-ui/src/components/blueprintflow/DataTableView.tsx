import { useState, useMemo, useCallback } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import {
  ChevronUp,
  ChevronDown,
  Download,
  FileSpreadsheet,
  Search,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check
} from 'lucide-react';

// 한글 레이블 매핑
const LABEL_MAP: Record<string, string> = {
  // 공통
  'confidence': '신뢰도',
  'class_name': '클래스',
  'class_id': '클래스ID',
  'bbox': '바운딩박스',
  'text': '텍스트',
  'value': '값',

  // OCR 관련
  'dimension_text': '치수',
  'tolerance': '공차',
  'unit': '단위',
  'source': '출처',
  'gdt_symbol': 'GD&T 기호',
  'datum': '데이텀',

  // P&ID 관련
  'color_type': '색상타입',
  'color_type_korean': '색상',
  'line_style': '라인스타일',
  'line_style_korean': '스타일',
  'signal_type': '신호타입',
  'pipe_type': '배관타입',
  'source_symbol': '소스심볼',
  'target_symbol': '타겟심볼',
  'source_class': '소스클래스',
  'target_class': '타겟클래스',

  // BOM 관련
  'tag': '태그',
  'type': '타입',
  'quantity': '수량',
  'description': '설명',
  'count': '개수',

  // Line Detector
  'start_point': '시작점',
  'end_point': '끝점',
  'length': '길이',
  'angle': '각도',

  // 기타
  'id': 'ID',
  'name': '이름',
  'index': '번호',
  'x': 'X',
  'y': 'Y',
  'width': '너비',
  'height': '높이',
};

interface ColumnDef {
  key: string;
  label: string;
  type?: 'string' | 'number' | 'percentage' | 'badge' | 'array' | 'object';
  width?: string;
  sortable?: boolean;
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}

interface DataTableViewProps {
  data: unknown[];
  columns?: ColumnDef[];
  title?: string;
  nodeType?: string;
  exportFilename?: string;
  searchable?: boolean;
  sortable?: boolean;
  pageSize?: number;
  compact?: boolean;
}

// 값 타입 추론
function inferType(value: unknown): ColumnDef['type'] {
  if (value === null || value === undefined) return 'string';
  if (typeof value === 'number') {
    if (value >= 0 && value <= 1) return 'percentage';
    return 'number';
  }
  if (Array.isArray(value)) return 'array';
  if (typeof value === 'object') return 'object';
  return 'string';
}

// 컬럼 자동 추론
function inferColumns(data: unknown[]): ColumnDef[] {
  if (!data || data.length === 0) return [];

  const sample = data[0] as Record<string, unknown>;
  const keys = Object.keys(sample);

  // 숨길 필드들
  const hiddenFields = ['raw_data', 'metadata', '__typename'];

  return keys
    .filter(key => !hiddenFields.includes(key))
    .map(key => ({
      key,
      label: LABEL_MAP[key] || formatLabel(key),
      type: inferType(sample[key]),
      sortable: true,
    }));
}

// snake_case -> 한글/영문 변환
function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

// 값 포맷팅
function formatValue(value: unknown, type?: ColumnDef['type']): React.ReactNode {
  if (value === null || value === undefined) return '-';

  if (type === 'percentage' && typeof value === 'number') {
    return `${(value * 100).toFixed(1)}%`;
  }

  if (type === 'number' && typeof value === 'number') {
    return value.toFixed(2);
  }

  if (type === 'array' && Array.isArray(value)) {
    if (value.length === 0) return '-';
    if (value.length <= 4 && value.every(v => typeof v === 'number')) {
      return `[${value.map(v => typeof v === 'number' ? v.toFixed(0) : v).join(', ')}]`;
    }
    return `[${value.length}개]`;
  }

  if (type === 'object' && typeof value === 'object') {
    return JSON.stringify(value).slice(0, 50) + '...';
  }

  return String(value);
}

export default function DataTableView({
  data,
  columns: propColumns,
  title,
  nodeType,
  exportFilename = 'data',
  searchable = true,
  sortable = true,
  pageSize = 10,
  compact = false,
}: DataTableViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [copied, setCopied] = useState(false);

  // 컬럼 정의 (props 또는 자동 추론)
  const columns = useMemo(() => {
    if (propColumns && propColumns.length > 0) return propColumns;
    return inferColumns(data);
  }, [data, propColumns]);

  // 필터링된 데이터
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return data as Record<string, unknown>[];

    const query = searchQuery.toLowerCase();
    return (data as Record<string, unknown>[]).filter(row =>
      columns.some(col => {
        const value = row[col.key];
        if (value === null || value === undefined) return false;
        return String(value).toLowerCase().includes(query);
      })
    );
  }, [data, searchQuery, columns]);

  // 정렬된 데이터
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      let comparison = 0;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal;
      } else {
        comparison = String(aVal).localeCompare(String(bVal));
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortKey, sortDirection]);

  // 페이지네이션
  const totalPages = Math.ceil(sortedData.length / pageSize);
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  // 정렬 핸들러
  const handleSort = useCallback((key: string) => {
    if (!sortable) return;
    if (sortKey === key) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  }, [sortKey, sortable]);

  // CSV 다운로드
  const downloadCSV = useCallback(() => {
    const headers = columns.map(col => col.label);
    const rows = [headers.join(',')];

    (data as Record<string, unknown>[]).forEach((row, index) => {
      const values = columns.map(col => {
        const value = row[col.key];
        if (value === null || value === undefined) return '';
        if (typeof value === 'object') return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
        return `"${String(value).replace(/"/g, '""')}"`;
      });
      rows.push([index + 1, ...values.slice(1)].join(','));
    });

    const csv = rows.join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${exportFilename}_${nodeType || 'data'}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [data, columns, exportFilename, nodeType]);

  // JSON 다운로드
  const downloadJSON = useCallback(() => {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${exportFilename}_${nodeType || 'data'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [data, exportFilename, nodeType]);

  // 클립보드 복사
  const copyToClipboard = useCallback(async () => {
    try {
      const json = JSON.stringify(data, null, 2);
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // 클립보드 복사 실패 시 조용히 처리
    }
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <div className="text-sm text-muted-foreground p-4 text-center">
        데이터가 없습니다
      </div>
    );
  }

  return (
    <Card className={compact ? 'p-2' : 'p-4'}>
      {/* 헤더 */}
      <div className={`flex items-center justify-between ${compact ? 'mb-2' : 'mb-4'}`}>
        <div className="flex items-center gap-2">
          {title && (
            <h4 className={`font-semibold ${compact ? 'text-xs' : 'text-sm'}`}>
              {title}
            </h4>
          )}
          <span className={`text-muted-foreground ${compact ? 'text-xs' : 'text-sm'}`}>
            ({sortedData.length}개)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* 검색 */}
          {searchable && !compact && (
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
              <input
                type="text"
                placeholder="검색..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-7 pr-2 py-1 text-xs border rounded w-32 bg-background"
              />
            </div>
          )}

          {/* 내보내기 버튼 */}
          <Button
            variant="outline"
            size="sm"
            onClick={downloadCSV}
            className={compact ? 'h-6 px-2 text-xs' : 'h-7 px-2 text-xs'}
          >
            <FileSpreadsheet className="w-3 h-3 mr-1" />
            CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={downloadJSON}
            className={compact ? 'h-6 px-2 text-xs' : 'h-7 px-2 text-xs'}
          >
            <Download className="w-3 h-3 mr-1" />
            JSON
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={copyToClipboard}
            className={compact ? 'h-6 px-2 text-xs' : 'h-7 px-2 text-xs'}
          >
            {copied ? (
              <Check className="w-3 h-3 text-green-500" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
          </Button>
        </div>
      </div>

      {/* 테이블 */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-2 py-1.5 text-left font-medium text-muted-foreground w-10">
                #
              </th>
              {columns.map(col => (
                <th
                  key={col.key}
                  className={`px-2 py-1.5 text-left font-medium text-muted-foreground ${
                    sortable ? 'cursor-pointer hover:bg-muted/80 select-none' : ''
                  }`}
                  style={{ width: col.width }}
                  onClick={() => handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sortable && sortKey === col.key && (
                      sortDirection === 'asc'
                        ? <ChevronUp className="w-3 h-3" />
                        : <ChevronDown className="w-3 h-3" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-b hover:bg-muted/30 transition-colors"
              >
                <td className="px-2 py-1.5 text-muted-foreground">
                  {(currentPage - 1) * pageSize + rowIndex + 1}
                </td>
                {columns.map(col => (
                  <td key={col.key} className="px-2 py-1.5">
                    {col.render
                      ? col.render(row[col.key], row)
                      : formatValue(row[col.key], col.type)
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3 pt-3 border-t">
          <span className="text-xs text-muted-foreground">
            {(currentPage - 1) * pageSize + 1}-{Math.min(currentPage * pageSize, sortedData.length)} / {sortedData.length}
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="h-6 w-6 p-0"
            >
              <ChevronLeft className="w-3 h-3" />
            </Button>
            <span className="text-xs px-2">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="h-6 w-6 p-0"
            >
              <ChevronRight className="w-3 h-3" />
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}

