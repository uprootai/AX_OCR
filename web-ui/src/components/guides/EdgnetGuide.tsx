import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import Mermaid from '../ui/Mermaid';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

export default function EdgnetGuide() {
  const [isOpen, setIsOpen] = useState(true);

  const systemDiagram = `
flowchart LR
    A[도면 이미지] --> B[EDGNet API<br/>포트 5002]
    B --> C[Graph Neural Network]
    C --> D{세그멘테이션}
    D --> E[윤곽선<br/>Contour]
    D --> F[텍스트<br/>Text]
    D --> G[치수<br/>Dimension]
    E --> H[GraphSAGE<br/>관계 분석]
    F --> H
    G --> H
    H --> I[벡터화<br/>Bezier Curves]
    I --> J[결과 반환<br/>JSON + SVG]

    style B fill:#ea580c,stroke:#fb923c,stroke-width:3px,color:#fff
    style C fill:#065f46,stroke:#34d399,stroke-width:3px,color:#fff
    style H fill:#1e40af,stroke:#60a5fa,stroke-width:3px,color:#fff
    style J fill:#7e22ce,stroke:#c084fc,stroke-width:3px,color:#fff
  `;

  const processDiagram = `
sequenceDiagram
    participant User as 사용자
    participant UI as Web UI
    participant API as EDGNet API
    participant GNN as Graph Network

    User->>UI: 1. 도면 이미지 업로드
    UI->>API: 2. POST /api/v1/segment

    API->>API: 3. 전처리<br/>(노이즈 제거, 이진화)
    API->>GNN: 4. 그래프 구축
    Note over GNN: 픽셀 → 노드<br/>인접성 → 엣지

    GNN->>GNN: 5. GraphSAGE 분석
    Note over GNN: 90.82% 정확도

    GNN-->>API: 6. 분류 결과
    Note over API: Contour/Text/Dimension

    API->>API: 7. 벡터화 (Bezier)
    API-->>UI: 8. JSON + SVG 반환
    UI-->>User: 9. 시각화 표시
  `;

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              EDGNet 사용 가이드
              <Badge>Graph Neural Network</Badge>
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              그래프 신경망으로 도면을 세그멘테이션하고 벡터화합니다 (정확도 90.82%)
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
                <h4 className="font-semibold mb-2">🔵 윤곽선 (Contour)</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 기하학적 도형</li>
                  <li>• 선, 원, 호</li>
                  <li>• 부품 형상</li>
                  <li>• 정확도: 92%</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">📝 텍스트 (Text)</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 도면 번호</li>
                  <li>• 주석, 노트</li>
                  <li>• 재질 정보</li>
                  <li>• 정확도: 88%</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">📏 치수 (Dimension)</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• 치수선</li>
                  <li>• 치수 값</li>
                  <li>• GD&T 기호</li>
                  <li>• 정확도: 91%</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 💡 EDGNet의 역할 */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2 flex items-center gap-2">
              💡 EDGNet의 역할
            </h4>
            <ul className="text-sm text-yellow-800 dark:text-yellow-200 space-y-1.5">
              <li>• EDGNet은 치수선의 <strong>위치</strong>를 분류합니다 (치수가 어디에 있는지)</li>
              <li>• 실제 치수 <strong>값</strong>(예: "Ø50", "100mm")을 읽으려면 <strong className="text-yellow-900 dark:text-yellow-100">YOLOv11</strong> 또는 <strong className="text-yellow-900 dark:text-yellow-100">eDOCr</strong>를 사용하세요</li>
              <li>• <strong>EDGNet + YOLOv11</strong> 조합으로 가장 정확한 결과를 얻을 수 있습니다</li>
              <li>• EDGNet은 도면의 <strong>구조적 분석</strong> (레이어 분리, 벡터화)에 특화되어 있습니다</li>
            </ul>
          </div>

          {/* 🧠 GraphSAGE 기술 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">🧠 GraphSAGE 기술</h3>
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 p-4 rounded-lg">
              <p className="text-sm mb-3">
                GraphSAGE (Graph Sample and Aggregate)는 이웃 노드의 정보를 집계하여
                각 픽셀의 컨텍스트를 이해하는 그래프 신경망 기술입니다.
              </p>
              <div className="grid md:grid-cols-2 gap-3 text-sm">
                <div>
                  <h5 className="font-semibold mb-1">✅ 장점</h5>
                  <ul className="text-muted-foreground space-y-1">
                    <li>• 고정확도 (90.82%)</li>
                    <li>• 관계 기반 분류</li>
                    <li>• 복잡한 도면 처리</li>
                    <li>• 노이즈 강건성</li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-semibold mb-1">📊 성능</h5>
                  <ul className="text-muted-foreground space-y-1">
                    <li>• F1 Score: 0.91</li>
                    <li>• Precision: 89.5%</li>
                    <li>• Recall: 92.3%</li>
                    <li>• 처리 시간: ~3-5초</li>
                  </ul>
                </div>
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
                  <h4 className="font-semibold">이미지 업로드</h4>
                  <p className="text-sm text-muted-foreground">
                    공학 도면 이미지를 업로드합니다 (JPG, PNG 권장)
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  2
                </div>
                <div>
                  <h4 className="font-semibold">출력 형식 선택</h4>
                  <p className="text-sm text-muted-foreground">
                    JSON (구조화된 데이터) 또는 SVG (벡터 그래픽) 선택
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  3
                </div>
                <div>
                  <h4 className="font-semibold">세그멘테이션 실행</h4>
                  <p className="text-sm text-muted-foreground">
                    GraphSAGE가 도면을 분석하여 3가지 카테고리로 분류
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
                    분류된 요소와 벡터화된 결과를 확인
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 📊 출력 형식 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">📊 출력 형식</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">JSON 형식</h4>
                <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
{`{
  "num_components": 150,
  "classifications": {
    "contour": 80,
    "text": 30,
    "dimension": 40
  },
  "graph": {
    "nodes": 150,
    "edges": 280,
    "avg_degree": 3.73
  }
}`}
                </pre>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2">벡터화 정보</h4>
                <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
{`{
  "vectorization": {
    "num_bezier_curves": 150,
    "total_length": 12450.5,
    "format": "svg"
  },
  "visualization_url": "/result/xxx.svg"
}`}
                </pre>
              </div>
            </div>
          </div>

          {/* 💡 팁 */}
          <div className="bg-orange-50 dark:bg-orange-950 p-4 rounded-lg">
            <h4 className="font-semibold mb-2 text-orange-900 dark:text-orange-100">
              💡 최적의 결과를 위한 팁
            </h4>
            <ul className="text-sm text-orange-800 dark:text-orange-200 space-y-1">
              <li>• 깨끗한 배경의 도면 사용 (노이즈 최소화)</li>
              <li>• 선명한 이미지 권장 (DPI 300 이상)</li>
              <li>• 복잡한 도면은 GraphSAGE가 가장 우수</li>
              <li>• 벡터화된 결과는 CAD 소프트웨어와 호환</li>
            </ul>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
