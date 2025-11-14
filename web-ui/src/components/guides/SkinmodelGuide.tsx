import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import Mermaid from '../ui/Mermaid';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

export default function SkinmodelGuide() {
  const [isOpen, setIsOpen] = useState(true);

  const systemDiagram = `
flowchart LR
    A[세그멘테이션<br/>결과] --> B[Skin Model API<br/>포트 5003]
    B --> C[3D 형상 분석]
    C --> D[공차 예측<br/>AI 모델]
    D --> E[가공 공정<br/>추론]
    E --> F{분석 결과}
    F --> G[필수 공차]
    F --> H[가공 난이도]
    F --> I[비용 예측]
    G --> J[결과 반환<br/>JSON]
    H --> J
    I --> J

    style B fill:#7e22ce,stroke:#c084fc,stroke-width:3px,color:#fff
    style C fill:#065f46,stroke:#34d399,stroke-width:3px,color:#fff
    style D fill:#ea580c,stroke:#fb923c,stroke-width:3px,color:#fff
    style J fill:#1e40af,stroke:#60a5fa,stroke-width:3px,color:#fff
  `;

  const processDiagram = `
sequenceDiagram
    participant User as 사용자
    participant UI as Web UI
    participant API as Skin Model API
    participant AI as AI Engine

    User->>UI: 1. 세그멘테이션 결과 전송
    UI->>API: 2. POST /api/v1/predict

    API->>AI: 3. 형상 분석
    Note over AI: 윤곽선 → 3D 형상

    AI->>AI: 4. 공차 필요성 판단
    Note over AI: 기계 학습 모델

    AI-->>API: 5. 공차 위치 예측
    Note over API: 좌표 + 타입

    API->>API: 6. 가공 공정 추론
    Note over API: 선삭, 밀링, 연삭...

    API->>API: 7. 비용 산정
    API-->>UI: 8. JSON 응답
    UI-->>User: 9. 결과 시각화
  `;

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Skin Model 사용 가이드
              <Badge>AI 공차 예측</Badge>
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              3D 형상 분석으로 필수 공차를 자동 예측하고 가공 공정을 추론합니다
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

          {/* 🔄 처리 프로세스 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">🔄 처리 프로세스</h3>
            <Mermaid chart={processDiagram} />
          </div>

          {/* 🎯 주요 기능 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">🎯 주요 기능</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">🎯 공차 예측</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 필수 공차 위치</li>
                  <li>• 공차 타입 (IT 등급)</li>
                  <li>• 중요도 점수</li>
                  <li>• 정확도: 87%</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">🔧 가공 공정</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 선삭 (Turning)</li>
                  <li>• 밀링 (Milling)</li>
                  <li>• 연삭 (Grinding)</li>
                  <li>• 드릴링 (Drilling)</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">💰 비용 산정</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 재료비</li>
                  <li>• 가공 시간</li>
                  <li>• 난이도 보정</li>
                  <li>• 총 예상 비용</li>
                </ul>
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
                  <h4 className="font-semibold">세그멘테이션 결과 준비</h4>
                  <p className="text-sm text-muted-foreground">
                    EDGNet으로 먼저 세그멘테이션을 수행하거나 JSON 파일 업로드
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  2
                </div>
                <div>
                  <h4 className="font-semibold">재질 정보 입력</h4>
                  <p className="text-sm text-muted-foreground">
                    부품 재질을 선택 (탄소강, 스테인리스, 알루미늄 등)
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  3
                </div>
                <div>
                  <h4 className="font-semibold">공차 예측 실행</h4>
                  <p className="text-sm text-muted-foreground">
                    AI 모델이 형상을 분석하여 필수 공차 위치와 값을 예측
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  4
                </div>
                <div>
                  <h4 className="font-semibold">결과 분석</h4>
                  <p className="text-sm text-muted-foreground">
                    예측된 공차, 가공 공정, 비용을 확인하고 검토
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 📊 공차 등급 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">📊 IT 공차 등급</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="p-2 text-left">IT 등급</th>
                    <th className="p-2 text-left">정밀도</th>
                    <th className="p-2 text-left">가공 방법</th>
                    <th className="p-2 text-left">용도</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t">
                    <td className="p-2 font-semibold">IT6-IT7</td>
                    <td className="p-2">매우 높음</td>
                    <td className="p-2">연삭, 정밀 가공</td>
                    <td className="p-2">베어링, 정밀 기어</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2 font-semibold">IT8-IT9</td>
                    <td className="p-2">높음</td>
                    <td className="p-2">밀링, 선삭</td>
                    <td className="p-2">일반 끼워맞춤</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2 font-semibold">IT10-IT11</td>
                    <td className="p-2">중간</td>
                    <td className="p-2">일반 가공</td>
                    <td className="p-2">비정밀 부품</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2 font-semibold">IT12-IT14</td>
                    <td className="p-2">낮음</td>
                    <td className="p-2">주조, 단조</td>
                    <td className="p-2">구조 부품</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* ⚡ 성능 지표 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">⚡ 성능 지표</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">예측 정확도</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>위치 정확도:</span>
                    <span className="font-semibold">87%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>타입 정확도:</span>
                    <span className="font-semibold">83%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>비용 오차:</span>
                    <span className="font-semibold">±15%</span>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">처리 성능</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>평균 처리 시간:</span>
                    <span className="font-semibold">~2-4초</span>
                  </div>
                  <div className="flex justify-between">
                    <span>동시 처리:</span>
                    <span className="font-semibold">최대 10건</span>
                  </div>
                  <div className="flex justify-between">
                    <span>메모리 사용:</span>
                    <span className="font-semibold">~500MB</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 💡 팁 */}
          <div className="bg-purple-50 dark:bg-purple-950 p-4 rounded-lg">
            <h4 className="font-semibold mb-2 text-purple-900 dark:text-purple-100">
              💡 최적의 결과를 위한 팁
            </h4>
            <ul className="text-sm text-purple-800 dark:text-purple-200 space-y-1">
              <li>• 정확한 재질 정보 입력이 중요 (비용 산정에 영향)</li>
              <li>• EDGNet 세그멘테이션 결과와 함께 사용 권장</li>
              <li>• 예측 결과는 참고용이며, 전문가 검토 필요</li>
              <li>• 복잡한 형상일수록 정확도 향상</li>
            </ul>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
