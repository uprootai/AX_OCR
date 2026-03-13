import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { GatewayGuideContent } from './GatewayGuideContent';

export default function GatewayGuide() {
  const [isOpen, setIsOpen] = useState(true);
  const [selectedPipeline, setSelectedPipeline] = useState<'hybrid' | 'speed'>('hybrid');

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Gateway API 사용 가이드
              <Badge variant="default">통합 오케스트레이터</Badge>
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              모든 API를 통합하여 완전한 도면 분석 및 견적 생성 워크플로우를 제공합니다
            </p>
          </div>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="text-muted-foreground hover:text-foreground"
          >
            {isOpen ? <ChevronUp /> : <ChevronDown />}
          </button>
        </div>
      </CardHeader>

      {isOpen && (
        <CardContent className="space-y-6">
          <GatewayGuideContent
            selectedPipeline={selectedPipeline}
            onSelectPipeline={setSelectedPipeline}
          />
        </CardContent>
      )}
    </Card>
  );
}
