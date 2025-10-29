import { Link } from 'react-router-dom';
import { ArrowRight, Zap, Eye, Bug } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20">
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold mb-4">
            AX 도면 분석 시스템
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            AI 기반 공학 도면 분석 및 디버깅 콘솔
          </p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-semibold hover:bg-primary/90 transition-colors"
          >
            시작하기
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>

        <div className="grid md:grid-3 gap-8 max-w-4xl mx-auto">
          <div className="bg-card p-6 rounded-lg border">
            <Zap className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">빠른 분석</h3>
            <p className="text-sm text-muted-foreground">
              도면 업로드 후 5초 내 OCR, 세그멘테이션, 공차 예측 완료
            </p>
          </div>

          <div className="bg-card p-6 rounded-lg border">
            <Eye className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">실시간 모니터링</h3>
            <p className="text-sm text-muted-foreground">
              각 API의 성능을 실시간으로 확인하고 병목 구간 파악
            </p>
          </div>

          <div className="bg-card p-6 rounded-lg border">
            <Bug className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">강력한 디버깅</h3>
            <p className="text-sm text-muted-foreground">
              Request/Response 인스펙터로 모든 데이터 추적 및 분석
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
