import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Dimension {
  dimension_text: string;
  value?: number;
  tolerance?: string;
}

interface DimensionChartProps {
  dimensions: Dimension[];
  title?: string;
}

export function DimensionChart({ dimensions, title = "치수 분포" }: DimensionChartProps) {
  // 치수 값이 있는 항목만 필터링하고 상위 10개만 표시
  const chartData = dimensions
    .filter(d => d.value !== undefined && d.value > 0)
    .slice(0, 10)
    .map((d, index) => ({
      name: `#${index + 1}`,
      dimension: d.dimension_text,
      value: d.value,
      tolerance: d.tolerance || 'N/A'
    }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            치수 데이터가 없습니다
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis label={{ value: '치수 값 (mm)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-gray-800 p-3 border rounded shadow-lg">
                      <p className="font-semibold">{data.dimension}</p>
                      <p className="text-sm">값: {data.value} mm</p>
                      <p className="text-sm">공차: {data.tolerance}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Bar dataKey="value" fill="#3b82f6" name="치수 값 (mm)" />
          </BarChart>
        </ResponsiveContainer>

        {/* 상세 테이블 */}
        <div className="mt-4 max-h-40 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="bg-muted sticky top-0">
              <tr>
                <th className="p-2 text-left">#</th>
                <th className="p-2 text-left">치수</th>
                <th className="p-2 text-right">값 (mm)</th>
                <th className="p-2 text-center">공차</th>
              </tr>
            </thead>
            <tbody>
              {chartData.map((d, idx) => (
                <tr key={idx} className="border-t">
                  <td className="p-2">{d.name}</td>
                  <td className="p-2 font-mono">{d.dimension}</td>
                  <td className="p-2 text-right font-semibold">{d.value}</td>
                  <td className="p-2 text-center">{d.tolerance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
