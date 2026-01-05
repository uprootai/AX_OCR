/**
 * GTComparisonSection - Ground Truth 비교 섹션
 * GT 파일 업로드 및 검출 결과와의 비교 메트릭 표시
 */

import { useState, useRef } from 'react';
import { Upload, BarChart3, CheckCircle, XCircle, AlertCircle, FileJson } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';

interface GTMatch {
  detection_idx: number;
  gt_bbox: { x1: number; y1: number; x2: number; y2: number };
  gt_class: string;
  iou: number;
  class_match: boolean;
}

interface FNLabel {
  bbox: { x1: number; y1: number; x2: number; y2: number };
  class_name: string;
}

interface GTCompareResult {
  gt_count: number;
  tp_matches: GTMatch[];
  fn_labels: FNLabel[];
  metrics: {
    f1_score: number;
    precision: number;
    recall: number;
    tp: number;
    fp: number;
    fn: number;
  };
}

interface GTComparisonSectionProps {
  sessionId: string;
  gtCompareResult: GTCompareResult | null;
  detectionCount: number;
  onUploadGT: (file: File) => Promise<void>;
  onCompare: () => Promise<void>;
  isLoading: boolean;
  apiBaseUrl: string;
}

export function GTComparisonSection({
  sessionId: _sessionId,
  gtCompareResult,
  detectionCount,
  onUploadGT,
  onCompare,
  isLoading,
}: GTComparisonSectionProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.json') || file.name.endsWith('.xml') || file.name.endsWith('.txt'))) {
      setUploadedFileName(file.name);
      await onUploadGT(file);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFileName(file.name);
      await onUploadGT(file);
    }
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-orange-500" />
        GT 비교
        <InfoTooltip
          content="Ground Truth(정답 데이터)와 검출 결과를 비교하여 정밀도, 재현율, F1 스코어를 계산합니다."
          position="right"
        />
      </h2>

      {/* GT 파일 업로드 영역 */}
      <div
        className={`border-2 border-dashed rounded-lg p-4 mb-4 transition-colors ${
          isDragging
            ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
            : 'border-gray-300 dark:border-gray-600'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,.xml,.txt"
          className="hidden"
          onChange={handleFileSelect}
        />
        <div className="text-center">
          {uploadedFileName ? (
            <div className="flex items-center justify-center gap-2 text-green-600 dark:text-green-400">
              <FileJson className="w-5 h-5" />
              <span className="font-medium">{uploadedFileName}</span>
            </div>
          ) : (
            <>
              <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                GT 파일을 드래그하거나{' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-orange-600 hover:text-orange-700 font-medium"
                >
                  클릭하여 선택
                </button>
              </p>
              <p className="text-xs text-gray-500 mt-1">JSON, XML, TXT (YOLO) 형식</p>
            </>
          )}
        </div>
      </div>

      {/* 비교 버튼 */}
      <button
        onClick={onCompare}
        disabled={!uploadedFileName || isLoading || detectionCount === 0}
        className={`w-full py-2 px-4 rounded-lg font-medium transition-colors mb-4 ${
          !uploadedFileName || isLoading || detectionCount === 0
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700'
            : 'bg-orange-500 text-white hover:bg-orange-600'
        }`}
      >
        {isLoading ? '비교 중...' : 'GT 비교 실행'}
      </button>

      {/* 비교 결과 */}
      {gtCompareResult && (
        <div className="space-y-4">
          {/* 메트릭 카드 */}
          <div className="grid grid-cols-3 gap-3">
            <MetricCard
              label="정밀도"
              value={formatPercent(gtCompareResult.metrics.precision)}
              description="검출 중 정답 비율"
              color="blue"
            />
            <MetricCard
              label="재현율"
              value={formatPercent(gtCompareResult.metrics.recall)}
              description="정답 중 검출 비율"
              color="green"
            />
            <MetricCard
              label="F1 스코어"
              value={formatPercent(gtCompareResult.metrics.f1_score)}
              description="정밀도와 재현율의 조화평균"
              color="orange"
            />
          </div>

          {/* TP/FP/FN 카운트 */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              상세 통계
            </h3>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="flex flex-col items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mb-1" />
                <span className="text-lg font-bold text-green-600 dark:text-green-400">
                  {gtCompareResult.metrics.tp}
                </span>
                <span className="text-xs text-gray-500">True Positive</span>
              </div>
              <div className="flex flex-col items-center">
                <XCircle className="w-5 h-5 text-red-500 mb-1" />
                <span className="text-lg font-bold text-red-600 dark:text-red-400">
                  {gtCompareResult.metrics.fp}
                </span>
                <span className="text-xs text-gray-500">False Positive</span>
              </div>
              <div className="flex flex-col items-center">
                <AlertCircle className="w-5 h-5 text-yellow-500 mb-1" />
                <span className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                  {gtCompareResult.metrics.fn}
                </span>
                <span className="text-xs text-gray-500">False Negative</span>
              </div>
            </div>
          </div>

          {/* GT 총 개수 */}
          <div className="text-sm text-gray-600 dark:text-gray-400 text-center">
            GT 라벨: <span className="font-medium">{gtCompareResult.gt_count}개</span> |
            검출 결과: <span className="font-medium">{detectionCount}개</span>
          </div>
        </div>
      )}

      {/* 결과 없음 */}
      {!gtCompareResult && uploadedFileName && !isLoading && (
        <div className="text-center text-gray-500 dark:text-gray-400 py-4">
          <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">GT 비교를 실행하면 결과가 여기에 표시됩니다.</p>
        </div>
      )}
    </section>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  description: string;
  color: 'blue' | 'green' | 'orange';
}

function MetricCard({ label, value, description, color }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    orange: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400',
  };

  return (
    <div className={`rounded-lg p-3 ${colorClasses[color]}`}>
      <div className="text-xs font-medium opacity-80">{label}</div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs opacity-60">{description}</div>
    </div>
  );
}
