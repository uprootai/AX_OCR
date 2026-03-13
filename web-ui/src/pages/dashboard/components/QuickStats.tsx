import { Card, CardContent } from '../../../components/ui/Card';
import { TrendingUp, Activity } from 'lucide-react';

export function QuickStats() {
  return (
    <div id="section-stats" className="scroll-mt-4 grid md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">오늘 분석</p>
              <p className="text-2xl font-bold">0</p>
            </div>
            <TrendingUp className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">성공률</p>
              <p className="text-2xl font-bold">100%</p>
            </div>
            <Activity className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">평균 응답</p>
              <p className="text-2xl font-bold">4.5s</p>
            </div>
            <Activity className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">에러</p>
              <p className="text-2xl font-bold">0</p>
            </div>
            <Activity className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
