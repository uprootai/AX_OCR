/**
 * Confidence Distribution Chart
 *
 * 검출 결과의 신뢰도 분포를 히스토그램으로 시각화합니다.
 * YOLO, OCR 등 다양한 검출 결과에 사용할 수 있습니다.
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import { useMemo } from 'react';

export interface Detection {
  confidence: number;
  class_name?: string;
  [key: string]: unknown;
}

interface ConfidenceDistributionChartProps {
  detections: Detection[];
  title?: string;
  buckets?: number;
  showStatistics?: boolean;
  compact?: boolean;
}

interface BucketData {
  range: string;
  count: number;
  percentage: number;
  minConf: number;
  maxConf: number;
}

interface Statistics {
  mean: number;
  median: number;
  stdDev: number;
  min: number;
  max: number;
  total: number;
}

const getConfidenceColor = (minConf: number): string => {
  if (minConf >= 0.8) return '#22c55e'; // green-500
  if (minConf >= 0.6) return '#84cc16'; // lime-500
  if (minConf >= 0.4) return '#eab308'; // yellow-500
  if (minConf >= 0.2) return '#f97316'; // orange-500
  return '#ef4444'; // red-500
};

const calculateStatistics = (confidences: number[]): Statistics => {
  if (confidences.length === 0) {
    return { mean: 0, median: 0, stdDev: 0, min: 0, max: 0, total: 0 };
  }

  const sorted = [...confidences].sort((a, b) => a - b);
  const sum = sorted.reduce((acc, val) => acc + val, 0);
  const mean = sum / sorted.length;

  const median = sorted.length % 2 === 0
    ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
    : sorted[Math.floor(sorted.length / 2)];

  const squaredDiffs = sorted.map(val => Math.pow(val - mean, 2));
  const variance = squaredDiffs.reduce((acc, val) => acc + val, 0) / sorted.length;
  const stdDev = Math.sqrt(variance);

  return {
    mean,
    median,
    stdDev,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    total: sorted.length,
  };
};

export function ConfidenceDistributionChart({
  detections,
  title = "신뢰도 분포",
  buckets = 5,
  showStatistics = true,
  compact = false,
}: ConfidenceDistributionChartProps) {
  const { bucketData, statistics } = useMemo(() => {
    const confidences = detections
      .map(d => d.confidence)
      .filter(c => typeof c === 'number' && !isNaN(c));

    const stats = calculateStatistics(confidences);

    // Create buckets (0-20%, 20-40%, etc.)
    const bucketSize = 1 / buckets;
    const bucketCounts: BucketData[] = Array.from({ length: buckets }, (_, i) => {
      const minConf = i * bucketSize;
      const maxConf = (i + 1) * bucketSize;
      const count = confidences.filter(c => c >= minConf && (i === buckets - 1 ? c <= maxConf : c < maxConf)).length;
      const percentage = confidences.length > 0 ? (count / confidences.length) * 100 : 0;

      return {
        range: `${Math.round(minConf * 100)}-${Math.round(maxConf * 100)}%`,
        count,
        percentage,
        minConf,
        maxConf,
      };
    });

    return { bucketData: bucketCounts, statistics: stats };
  }, [detections, buckets]);

  if (detections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            검출 데이터가 없습니다
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className={compact ? "py-3" : undefined}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          <span className="text-sm text-muted-foreground">
            총 {statistics.total}개 검출
          </span>
        </div>
      </CardHeader>
      <CardContent className={compact ? "py-2" : undefined}>
        <ResponsiveContainer width="100%" height={compact ? 200 : 280}>
          <BarChart
            data={bucketData}
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              dataKey="range"
              tick={{ fontSize: 11 }}
              tickLine={false}
            />
            <YAxis
              label={compact ? undefined : { value: '검출 수', angle: -90, position: 'insideLeft', fontSize: 12 }}
              tick={{ fontSize: 11 }}
              allowDecimals={false}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload as BucketData;
                  return (
                    <div className="bg-white dark:bg-gray-800 p-3 border rounded shadow-lg text-sm">
                      <p className="font-semibold">신뢰도: {data.range}</p>
                      <p>검출 수: <span className="font-bold">{data.count}</span>개</p>
                      <p>비율: {data.percentage.toFixed(1)}%</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              formatter={() => '검출 수'}
              wrapperStyle={{ fontSize: 12 }}
            />
            <Bar
              dataKey="count"
              name="검출 수"
              radius={[4, 4, 0, 0]}
            >
              {bucketData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getConfidenceColor(entry.minConf)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {showStatistics && (
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-5 gap-2 text-center">
            <StatBox label="평균" value={`${(statistics.mean * 100).toFixed(1)}%`} />
            <StatBox label="중앙값" value={`${(statistics.median * 100).toFixed(1)}%`} />
            <StatBox label="표준편차" value={`${(statistics.stdDev * 100).toFixed(1)}%`} />
            <StatBox label="최소" value={`${(statistics.min * 100).toFixed(1)}%`} />
            <StatBox label="최대" value={`${(statistics.max * 100).toFixed(1)}%`} />
          </div>
        )}

        {!compact && (
          <div className="mt-4 flex items-center justify-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#ef4444' }} />
              <span>낮음 (&lt;20%)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#f97316' }} />
              <span>보통 (20-40%)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#eab308' }} />
              <span>양호 (40-60%)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#84cc16' }} />
              <span>우수 (60-80%)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#22c55e' }} />
              <span>최상 (&gt;80%)</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-muted/50 rounded-lg p-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-sm font-semibold">{value}</div>
    </div>
  );
}

export default ConfidenceDistributionChart;
