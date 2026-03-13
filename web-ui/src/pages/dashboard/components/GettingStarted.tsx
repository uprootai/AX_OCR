import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

export function GettingStarted() {
  return (
    <Card id="section-getting-started" className="scroll-mt-4">
      <CardHeader>
        <CardTitle>Getting Started</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
              1
            </div>
            <div>
              <h4 className="font-semibold">API 상태 확인</h4>
              <p className="text-sm text-muted-foreground">
                위의 API Health Status에서 모든 서비스가 정상 작동하는지 확인하세요.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
              2
            </div>
            <div>
              <h4 className="font-semibold">BlueprintFlow 워크플로우</h4>
              <p className="text-sm text-muted-foreground">
                비주얼 워크플로우에서 각 API를 노드로 추가하고 테스트하세요.
              </p>
              <Link to="/blueprintflow/builder">
                <Button variant="outline" size="sm" className="mt-2">
                  워크플로우 시작하기
                </Button>
              </Link>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
              3
            </div>
            <div>
              <h4 className="font-semibold">통합 분석 실행</h4>
              <p className="text-sm text-muted-foreground">
                템플릿을 선택하여 OCR, 세그멘테이션, 공차 예측을 한 번에 실행하세요.
              </p>
              <Link to="/blueprintflow/templates">
                <Button variant="outline" size="sm" className="mt-2">
                  템플릿 선택하기
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
