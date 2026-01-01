import { Button } from '../ui/Button';
import { Copy, FileJson, FileSpreadsheet } from 'lucide-react';
import { useState, useCallback } from 'react';
import Toast from '../ui/Toast';

// Toast 상태 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

interface DimensionData {
  dimension_text?: string;
  value?: string | number;
  tolerance?: string;
  confidence?: number;
  source?: string;
}

interface ResultData {
  [key: string]: unknown;
  ensemble?: { dimensions?: DimensionData[] };
  edocr_v2?: { dimensions?: DimensionData[] };
}

interface ResultActionsProps {
  data: ResultData;
  filename?: string;
}

export function ResultActions({ data, filename = 'drawing_analysis' }: ResultActionsProps) {
  const [copied, setCopied] = useState(false);

  // Toast 알림 상태
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  // Toast 표시 헬퍼 함수
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  const downloadJSON = () => {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadCSV = () => {
    // Extract dimensions from ensemble or edocr_v2 results
    const dimensions = data?.ensemble?.dimensions || data?.edocr_v2?.dimensions || [];

    if (dimensions.length === 0) {
      showToast('⚠️ CSV로 변환할 치수 데이터가 없습니다', 'warning');
      return;
    }

    // Create CSV header
    const headers = ['번호', '치수', '값', '공차', '신뢰도', '출처'];
    const rows = [headers.join(',')];

    // Add data rows
    dimensions.forEach((dim, index: number) => {
      const row = [
        index + 1,
        `"${dim.dimension_text || ''}"`,
        dim.value || '',
        `"${dim.tolerance || ''}"`,
        dim.confidence || '',
        `"${dim.source || ''}"`,
      ];
      rows.push(row.join(','));
    });

    const csv = rows.join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' }); // UTF-8 BOM for Excel
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async () => {
    try {
      const json = JSON.stringify(data, null, 2);
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
      showToast('✗ 클립보드 복사에 실패했습니다', 'error');
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        onClick={downloadJSON}
        variant="outline"
        size="sm"
        className="flex items-center gap-2"
      >
        <FileJson className="w-4 h-4" />
        JSON 다운로드
      </Button>

      <Button
        onClick={downloadCSV}
        variant="outline"
        size="sm"
        className="flex items-center gap-2"
      >
        <FileSpreadsheet className="w-4 h-4" />
        CSV 다운로드
      </Button>

      <Button
        onClick={copyToClipboard}
        variant="outline"
        size="sm"
        className="flex items-center gap-2"
      >
        {copied ? (
          <>
            <Copy className="w-4 h-4" />
            복사됨!
          </>
        ) : (
          <>
            <Copy className="w-4 h-4" />
            클립보드 복사
          </>
        )}
      </Button>

      {/* Toast 알림 */}
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
