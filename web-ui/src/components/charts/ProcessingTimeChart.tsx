import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface ProcessingTimeChartProps {
  yoloTime?: number;
  ocrTime?: number;
  segmentationTime?: number;
  toleranceTime?: number;
  totalTime?: number;
  title?: string;
}

const COLORS = {
  yolo: '#3b82f6',      // blue
  ocr: '#10b981',       // green
  segmentation: '#f59e0b', // orange
  tolerance: '#8b5cf6', // purple
  other: '#6b7280'      // gray
};

export function ProcessingTimeChart({
  yoloTime = 0,
  ocrTime = 0,
  segmentationTime = 0,
  toleranceTime = 0,
  totalTime = 0,
  title = "처리 시간 분석"
}: ProcessingTimeChartProps) {
  const data = [
    { name: 'YOLO 검출', value: yoloTime, color: COLORS.yolo },
    { name: 'OCR 분석', value: ocrTime, color: COLORS.ocr },
    { name: '세그멘테이션', value: segmentationTime, color: COLORS.segmentation },
    { name: '공차 예측', value: toleranceTime, color: COLORS.tolerance },
  ].filter(item => item.value > 0);

  const otherTime = Math.max(0, totalTime - (yoloTime + ocrTime + segmentationTime + toleranceTime));
  if (otherTime > 0.1) {
    data.push({ name: '기타', value: otherTime, color: COLORS.other });
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            처리 시간 데이터가 없습니다
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatTime = (seconds: number) => {
    if (seconds < 1) {
      return `${Math.round(seconds * 1000)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} (${((percent || 0) * 100).toFixed(1)}%)`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-gray-800 p-3 border rounded shadow-lg">
                      <p className="font-semibold">{data.name}</p>
                      <p className="text-sm">시간: {formatTime(data.value)}</p>
                      <p className="text-sm">
                        비율: {((data.value / totalTime) * 100).toFixed(1)}%
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>

        {/* 상세 통계 */}
        <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
          {data.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between p-2 bg-muted rounded">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span>{item.name}</span>
              </div>
              <span className="font-semibold">{formatTime(item.value)}</span>
            </div>
          ))}
          {totalTime > 0 && (
            <div className="col-span-2 flex items-center justify-between p-2 bg-primary/10 rounded font-semibold">
              <span>총 처리 시간</span>
              <span>{formatTime(totalTime)}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
