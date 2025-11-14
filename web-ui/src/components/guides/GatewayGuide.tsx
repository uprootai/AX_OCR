import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import Mermaid from '../ui/Mermaid';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

export default function GatewayGuide() {
  const [isOpen, setIsOpen] = useState(true);
  const [selectedPipeline, setSelectedPipeline] = useState<'hybrid' | 'speed'>('hybrid');

  const systemDiagram = `
flowchart LR
    A[Web UI / Client] --> B[Gateway API<br/>포트 8000]
    B --> C{오케스트레이터}
    C --> D[eDOCr v1/v2<br/>5001/5002]
    C --> E[EDGNet<br/>5002]
    C --> F[Skin Model<br/>5003]
    C --> G[YOLO<br/>5005]
    C -.-> V[VLM<br/>GPT-4V/Claude Vision<br/>추후 확장]
    D --> H[병렬 처리]
    E --> H
    F --> H
    G --> H
    V -.-> H
    H --> I[결과 통합]
    I --> J[견적서 생성]
    J --> K[PDF 다운로드]

    style B fill:#1e40af,stroke:#60a5fa,stroke-width:3px,color:#fff
    style C fill:#ea580c,stroke:#fb923c,stroke-width:3px,color:#fff
    style V fill:#be185d,stroke:#f9a8d4,stroke-width:3px,color:#fff,stroke-dasharray:5 5
    style H fill:#065f46,stroke:#34d399,stroke-width:3px,color:#fff
    style K fill:#7e22ce,stroke:#c084fc,stroke-width:3px,color:#fff
  `;

  // 제안 1: 하이브리드 파이프라인 (정확도 + 속도 균형)
  const hybridPipelineDiagram = `
sequenceDiagram
    participant User as 사용자
    participant UI as Web UI
    participant GW as Gateway
    participant YOLO as YOLOv11
    participant UP as Upscaler
    participant OCR as eDOCr v2
    participant SEG as EDGNet
    participant SKIN as Skin Model

    User->>UI: 1. 도면 업로드
    UI->>GW: 2. POST /api/v1/process<br/>(mode=hybrid)

    Note over GW: Step 1: 객체 검출
    GW->>YOLO: 3. 치수 영역 검출 요청
    YOLO-->>GW: 4. Bounding Boxes<br/>(mAP50 80.4%)

    par Step 2: 병렬 정밀 분석
        Note over GW,OCR: 2a. 검출된 영역 정밀 OCR
        GW->>UP: 5a. bbox 영역 4x Upscale
        UP-->>GW: 6a. 고해상도 이미지
        GW->>OCR: 7a. 정밀 OCR 요청
        OCR-->>GW: 8a. 치수 값 (92% 정확도)
        and
        Note over GW,SEG: 2b. 전체 구조 분석
        GW->>SEG: 5b. 세그멘테이션 요청
        SEG-->>GW: 6b. 레이어 분리<br/>(90.82% 정확도)
    end

    Note over GW: Step 3: 결과 앙상블
    GW->>GW: 9. YOLO bbox +<br/>eDOCr 값 +<br/>EDGNet 레이어 병합

    Note over GW: Step 4: 공차 예측
    GW->>SKIN: 10. 공차 예측 요청
    SKIN-->>GW: 11. 제조 가능성 분석

    GW->>GW: 12. 견적서 생성
    GW-->>UI: 13. 통합 결과 반환
    UI-->>User: 14. 결과 표시<br/>(예상 정확도 ~95%)

    Note over User,SKIN: 전체 처리 시간: 40-50초
  `;

  // 제안 2: 속도 우선 파이프라인
  const speedPipelineDiagram = `
sequenceDiagram
    participant User as 사용자
    participant UI as Web UI
    participant GW as Gateway
    participant YOLO as YOLOv11
    participant OCR as eDOCr v2
    participant SEG as EDGNet
    participant SKIN as Skin Model

    User->>UI: 1. 도면 업로드
    UI->>GW: 2. POST /api/v1/process<br/>(mode=speed)

    Note over GW: Step 1: 3-way 병렬 처리
    par 동시 실행 (최대 속도)
        GW->>YOLO: 3a. 객체 검출
        and
        GW->>OCR: 3b. OCR 분석
        and
        GW->>SEG: 3c. 세그멘테이션
    end

    par 결과 수신
        YOLO-->>GW: 4a. Bounding Boxes<br/>+ 클래스 (mAP50 80.4%)
        and
        OCR-->>GW: 4b. 치수 텍스트<br/>(92% 정확도)
        and
        SEG-->>GW: 4c. 레이어 정보<br/>(90.82% 정확도)
    end

    Note over GW: Step 2: 스마트 병합
    GW->>GW: 5. Confidence 기반 앙상블<br/>- YOLO bbox 우선<br/>- eDOCr 값 우선<br/>- EDGNet 레이어 보조

    Note over GW: Step 3: 공차 예측
    GW->>SKIN: 6. 공차 예측 요청
    SKIN-->>GW: 7. 제조 가능성 분석

    GW->>GW: 8. 견적서 생성
    GW-->>UI: 9. 통합 결과 반환
    UI-->>User: 10. 결과 표시<br/>(예상 정확도 ~93%)

    Note over User,SKIN: 전체 처리 시간: 35-45초
  `;

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
          {/* 📊 시스템 아키텍처 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">📊 시스템 아키텍처</h3>
            <Mermaid chart={systemDiagram} />
          </div>

          {/* 🚀 치수 추출 최적화 파이프라인 */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 p-6 rounded-lg border-2 border-blue-200 dark:border-blue-800">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              🚀 치수 추출 최적화 파이프라인
              <Badge variant="default">NEW</Badge>
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              목적에 맞게 최적화된 두 가지 처리 전략을 선택할 수 있습니다
            </p>

            {/* 파이프라인 선택 버튼 */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => setSelectedPipeline('hybrid')}
                className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                  selectedPipeline === 'hybrid'
                    ? 'border-blue-500 bg-blue-500 text-white shadow-lg'
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                }`}
              >
                <div className="font-semibold mb-1">⚖️ 하이브리드 파이프라인</div>
                <div className="text-xs opacity-90">
                  정확도 ~95% | 처리시간 40-50초
                </div>
              </button>
              <button
                onClick={() => setSelectedPipeline('speed')}
                className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                  selectedPipeline === 'speed'
                    ? 'border-green-500 bg-green-500 text-white shadow-lg'
                    : 'border-gray-300 dark:border-gray-600 hover:border-green-400'
                }`}
              >
                <div className="font-semibold mb-1">⚡ 속도 우선 파이프라인</div>
                <div className="text-xs opacity-90">
                  정확도 ~93% | 처리시간 35-45초
                </div>
              </button>
            </div>

            {/* 선택된 파이프라인의 다이어그램 */}
            <div className="bg-white dark:bg-gray-900 p-4 rounded-lg">
              <Mermaid
                chart={selectedPipeline === 'hybrid' ? hybridPipelineDiagram : speedPipelineDiagram}
              />
            </div>

            {/* 파이프라인별 상세 설명 */}
            {selectedPipeline === 'hybrid' ? (
              <div className="mt-4 grid md:grid-cols-2 gap-3">
                <div className="bg-blue-50 dark:bg-blue-900/30 p-3 rounded-lg">
                  <h5 className="font-semibold text-sm mb-2">✅ 장점</h5>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li>• YOLO로 정확한 위치 검출 (mAP50 80.4%)</li>
                    <li>• Upscaling으로 작은 텍스트도 인식</li>
                    <li>• eDOCr v2 정밀 OCR (92% 정확도)</li>
                    <li>• EDGNet으로 구조적 검증</li>
                    <li>• 앙상블로 최고 정확도 달성</li>
                  </ul>
                </div>
                <div className="bg-orange-50 dark:bg-orange-900/30 p-3 rounded-lg">
                  <h5 className="font-semibold text-sm mb-2">💡 추천 상황</h5>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li>• 고정밀도가 필요한 중요 도면</li>
                    <li>• 복잡한 치수 정보가 많은 도면</li>
                    <li>• 작은 폰트 크기의 치수 표기</li>
                    <li>• 최종 견적서 생성 시</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="mt-4 grid md:grid-cols-2 gap-3">
                <div className="bg-green-50 dark:bg-green-900/30 p-3 rounded-lg">
                  <h5 className="font-semibold text-sm mb-2">✅ 장점</h5>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li>• 3-way 병렬 처리로 최고 속도</li>
                    <li>• Confidence 기반 스마트 병합</li>
                    <li>• YOLO + eDOCr + EDGNet 동시 활용</li>
                    <li>• 리소스 효율적</li>
                    <li>• 실시간 피드백 가능</li>
                  </ul>
                </div>
                <div className="bg-orange-50 dark:bg-orange-900/30 p-3 rounded-lg">
                  <h5 className="font-semibold text-sm mb-2">💡 추천 상황</h5>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li>• 대량의 도면을 빠르게 처리</li>
                    <li>• 실시간 프리뷰가 필요한 경우</li>
                    <li>• 표준화된 도면 형식</li>
                    <li>• 초기 검토 및 분석 단계</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* 🎯 주요 기능 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">🎯 주요 기능</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">🔗 API 오케스트레이션</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 5개 API 통합 관리</li>
                  <li>• 병렬 처리로 속도 최적화</li>
                  <li>• 자동 에러 핸들링</li>
                  <li>• 결과 데이터 검증</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">📄 견적서 생성</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 자동 비용 산정</li>
                  <li>• PDF 견적서 생성</li>
                  <li>• QC 체크리스트 포함</li>
                  <li>• 가공 공정 명세</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">⚡ 성능 최적화</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 비동기 병렬 처리</li>
                  <li>• 캐싱 메커니즘</li>
                  <li>• 로드 밸런싱</li>
                  <li>• 타임아웃 관리</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">📊 모니터링</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 실시간 헬스체크</li>
                  <li>• 성능 메트릭 수집</li>
                  <li>• 에러 로깅</li>
                  <li>• API 상태 추적</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 📝 엔드포인트 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">📝 주요 엔드포인트</h3>
            <div className="space-y-3">
              <div className="bg-muted p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="default">POST</Badge>
                  <code className="text-sm">/api/v1/process</code>
                </div>
                <p className="text-sm text-muted-foreground">
                  전체 파이프라인 실행 (OCR + 세그멘테이션 + 공차 예측)
                </p>
              </div>

              <div className="bg-muted p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="default">POST</Badge>
                  <code className="text-sm">/api/v1/generate_quote</code>
                </div>
                <p className="text-sm text-muted-foreground">
                  견적서 자동 생성 (분석 + 비용 산정 + PDF)
                </p>
              </div>

              <div className="bg-muted p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="success">GET</Badge>
                  <code className="text-sm">/api/v1/health</code>
                </div>
                <p className="text-sm text-muted-foreground">
                  모든 서비스의 헬스 상태 확인
                </p>
              </div>

              <div className="bg-muted p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="success">GET</Badge>
                  <code className="text-sm">/api/v1/download_quote/{'{'} quote_number{'}'}</code>
                </div>
                <p className="text-sm text-muted-foreground">
                  생성된 견적서 PDF 다운로드
                </p>
              </div>
            </div>
          </div>

          {/* 📝 사용 방법 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">📝 사용 방법</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  1
                </div>
                <div>
                  <h4 className="font-semibold">도면 업로드</h4>
                  <p className="text-sm text-muted-foreground">
                    공학 도면 파일을 업로드 (이미지 또는 PDF)
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  2
                </div>
                <div>
                  <h4 className="font-semibold">처리 옵션 선택</h4>
                  <p className="text-sm text-muted-foreground">
                    OCR, 세그멘테이션, 공차 예측 중 필요한 기능 선택
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  3
                </div>
                <div>
                  <h4 className="font-semibold">자동 처리</h4>
                  <p className="text-sm text-muted-foreground">
                    Gateway가 모든 API를 병렬로 호출하여 결과 통합
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  4
                </div>
                <div>
                  <h4 className="font-semibold">결과 확인</h4>
                  <p className="text-sm text-muted-foreground">
                    통합된 분석 결과와 견적서 확인 및 다운로드
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* ⚡ 성능 지표 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">⚡ 성능 지표</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  ~40-50초
                </div>
                <div className="text-sm text-muted-foreground">
                  전체 파이프라인 처리 시간<br/>
                  (병렬 처리로 최적화)
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">
                  99.9%
                </div>
                <div className="text-sm text-muted-foreground">
                  시스템 가용성<br/>
                  (헬스체크 기반)
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                  5개
                </div>
                <div className="text-sm text-muted-foreground">
                  통합 API 서비스<br/>
                  (마이크로서비스)
                </div>
              </div>
            </div>
          </div>

          {/* 💡 팁 */}
          <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
            <h4 className="font-semibold mb-2 text-blue-900 dark:text-blue-100">
              💡 최적의 결과를 위한 팁
            </h4>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <li>• 모든 API가 healthy 상태인지 먼저 확인</li>
              <li>• 대용량 파일은 처리 시간이 더 소요될 수 있음</li>
              <li>• 에러 발생 시 개별 API 테스트로 원인 파악</li>
              <li>• 견적서는 quote_number로 나중에도 다운로드 가능</li>
            </ul>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
