/**
 * Table Extraction Section
 * 테이블 추출 결과 + 텍스트 영역 OCR 결과 표시
 */

import { useState, useEffect, useCallback } from 'react';
import { Loader2, Table2, FileText } from 'lucide-react';
import logger from '../../../lib/logger';

interface TableCell {
  text: string;
  row: number;
  col: number;
  rowSpan?: number;
  colSpan?: number;
}

interface ExtractedTable {
  table_id?: string;
  rows: number;
  cols: number;
  cells: TableCell[];
  confidence?: number;
  source_region?: string;
  headers?: string[];
  data?: string[][];
}

interface TextDetection {
  text: string;
  confidence: number;
  bbox?: number[][];
}

interface TextRegion {
  region: string;
  full_text: string;
  text_count: number;
  detections: TextDetection[];
}

interface TableExtractionSectionProps {
  sessionId: string;
  apiBaseUrl: string;
}

const REGION_LABELS: Record<string, string> = {
  title_block: '표제란 (Title Block)',
  notes_area: 'NOTES 영역',
  revision_table: '리비전 테이블',
  parts_list_right: '부품표 (Parts List)',
};

export function TableExtractionSection({ sessionId, apiBaseUrl }: TableExtractionSectionProps) {
  const [tables, setTables] = useState<ExtractedTable[]>([]);
  const [textRegions, setTextRegions] = useState<TextRegion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const loadTables = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/sessions/${sessionId}`);
      if (!res.ok) throw new Error(`Failed to load session: ${res.status}`);
      const session = await res.json();

      // table_results 필드가 세션에 있으면 사용
      if (session.table_results && Array.isArray(session.table_results)) {
        setTables(session.table_results);
      } else if (session.analysis_results?.tables) {
        setTables(session.analysis_results.tables);
      } else {
        setTables([]);
      }

      // text_regions 필드 로드
      if (session.text_regions && Array.isArray(session.text_regions)) {
        setTextRegions(session.text_regions);
      } else {
        setTextRegions([]);
      }

      setLoaded(true);
    } catch (err) {
      logger.error('Failed to load table results:', err);
      setError(err instanceof Error ? err.message : 'Failed to load tables');
      setLoaded(true);
    } finally {
      setLoading(false);
    }
  }, [sessionId, apiBaseUrl]);

  useEffect(() => {
    loadTables();
  }, [loadTables]);

  const renderTable = (table: ExtractedTable, index: number) => {
    // data 배열이 있으면 그것을 사용 (Table Detector extract 결과)
    if (table.data && table.data.length > 0) {
      return (
        <div key={table.table_id || index} className="mb-4">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            테이블 {index + 1} ({table.rows} x {table.cols})
            {table.source_region && (
              <span className="text-xs font-normal text-blue-500 ml-2 px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 rounded">
                {REGION_LABELS[table.source_region] || table.source_region}
              </span>
            )}
          </h3>
          <div className="overflow-x-auto border border-gray-200 dark:border-gray-600 rounded-lg">
            <table className="w-full text-sm">
              {table.headers && table.headers.length > 0 && (
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    {table.headers.map((h, i) => (
                      <th key={i} className="px-3 py-2 text-left font-medium text-gray-700 dark:text-gray-300">
                        {h || '-'}
                      </th>
                    ))}
                  </tr>
                </thead>
              )}
              <tbody>
                {table.data.map((row, rIdx) => (
                  <tr key={rIdx} className="border-t border-gray-200 dark:border-gray-600">
                    {row.map((cellText, cIdx) => (
                      <td key={cIdx} className="px-3 py-2 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                        {cellText || <span className="text-gray-300">-</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // cells 배열 기반 (기존 방식)
    const grid: string[][] = Array.from({ length: table.rows }, () =>
      Array.from({ length: table.cols }, () => '')
    );
    for (const cell of (table.cells || [])) {
      if (cell.row < table.rows && cell.col < table.cols) {
        grid[cell.row][cell.col] = cell.text;
      }
    }

    return (
      <div key={table.table_id || index} className="mb-4">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
          테이블 {index + 1} ({table.rows} x {table.cols})
          {table.confidence != null && (
            <span className="text-sm font-normal text-gray-500 ml-2">
              신뢰도: {Math.round(table.confidence * 100)}%
            </span>
          )}
        </h3>
        <div className="overflow-x-auto border border-gray-200 dark:border-gray-600 rounded-lg">
          <table className="w-full text-sm">
            <tbody>
              {grid.map((row, rIdx) => (
                <tr key={rIdx} className={rIdx === 0 ? 'bg-gray-50 dark:bg-gray-700 font-medium' : 'border-t border-gray-200 dark:border-gray-600'}>
                  {row.map((cellText, cIdx) => (
                    <td key={cIdx} className="px-3 py-2 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {cellText || <span className="text-gray-300">-</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderTextRegion = (region: TextRegion, index: number) => (
    <div key={index} className="mb-4 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="w-4 h-4 text-indigo-500" />
        <h3 className="font-semibold text-gray-900 dark:text-white">
          {REGION_LABELS[region.region] || region.region}
        </h3>
        <span className="text-xs text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
          {region.text_count}개 텍스트
        </span>
      </div>
      <div className="space-y-1">
        {region.detections.map((det, i) => (
          <div key={i} className="flex items-start gap-2 text-sm">
            <span className={`shrink-0 w-1.5 h-1.5 rounded-full mt-1.5 ${
              det.confidence >= 0.8 ? 'bg-green-400' : det.confidence >= 0.5 ? 'bg-yellow-400' : 'bg-red-400'
            }`} />
            <span className="text-gray-800 dark:text-gray-200">{det.text}</span>
            <span className="text-xs text-gray-400 shrink-0">
              {Math.round(det.confidence * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  const hasContent = tables.length > 0 || textRegions.length > 0;

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Table2 className="w-5 h-5" />
          테이블 및 텍스트 추출 결과
        </h2>
        {loading && (
          <div className="flex items-center text-primary-600">
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            <span className="text-sm">로드 중...</span>
          </div>
        )}
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg p-3 mb-4">
          {error}
        </div>
      )}

      {loaded && !hasContent && !error ? (
        <div className="text-center py-8">
          <Table2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">추출 결과가 없습니다.</p>
          <p className="text-sm text-gray-400 mt-1">
            사이드바에서 "분석 실행"을 눌러 테이블/텍스트 추출을 포함해 주세요.
          </p>
        </div>
      ) : (
        <>
          {tables.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                테이블 ({tables.length}개)
              </h3>
              {tables.map((table, i) => renderTable(table, i))}
            </div>
          )}
          {textRegions.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                텍스트 영역 ({textRegions.length}개)
              </h3>
              {textRegions.map((region, i) => renderTextRegion(region, i))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
