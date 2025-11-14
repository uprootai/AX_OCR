import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import Mermaid from '../ui/Mermaid';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

export default function EdocrGuide() {
  const [isOpen, setIsOpen] = useState(true);

  const systemDiagram = `
flowchart LR
    A[도면 이미지<br/>업로드] --> B[eDOCr API<br/>포트 5001/5002]
    B --> C{버전 선택}
    C -->|v1 GPU| D[CUDA 가속<br/>빠른 처리]
    C -->|v2 Advanced| E[고급 기능<br/>테이블 추출]
    D --> F[치수 추출]
    E --> F
    F --> G[GD&T 추출]
    G --> H[텍스트 블록]
    H --> I[결과 반환<br/>JSON]

    style B fill:#1e40af,stroke:#60a5fa,stroke-width:3px,color:#fff
    style D fill:#065f46,stroke:#34d399,stroke-width:3px,color:#fff
    style E fill:#ea580c,stroke:#fb923c,stroke-width:3px,color:#fff
    style I fill:#0c4a6e,stroke:#38bdf8,stroke-width:3px,color:#fff
  `;

  const processDiagram = `
sequenceDiagram
    participant User as 사용자
    participant UI as Web UI
    participant API as eDOCr API
    participant GPU as GPU Engine

    User->>UI: 1. 이미지 업로드
    User->>UI: 2. 버전 선택 (v1/v2)
    User->>UI: 3. 옵션 설정
    UI->>API: 4. POST /api/v1/ocr

    alt v1 (GPU)
        API->>GPU: 5. CUDA 가속 처리
        GPU-->>API: 6. 빠른 결과
    else v2 (Advanced)
        API->>API: 5. 고급 알고리즘
        Note over API: 테이블, 다국어 지원
    end

    API-->>UI: 7. JSON 응답
    UI-->>User: 8. 시각화 표시
  `;

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              eDOCr v1/v2 사용 가이드
              <Badge variant="success">GPU</Badge>
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              GPU 가속 OCR 엔진으로 공학 도면에서 치수, GD&T, 텍스트를 자동으로 추출합니다
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
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  eDOCr v1
                  <Badge variant="success">GPU</Badge>
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• ✅ CUDA GPU 가속</li>
                  <li>• ✅ 빠른 처리 속도 (~5-10초)</li>
                  <li>• ✅ 치수 추출 (선형, 각도, 반경)</li>
                  <li>• ✅ GD&T 기호 검출</li>
                  <li>• ✅ 기본 텍스트 인식</li>
                </ul>
              </div>

              <div className="bg-card p-4 rounded-lg border">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  eDOCr v2
                  <Badge>Advanced</Badge>
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• ✅ 고급 알고리즘</li>
                  <li>• ✅ 테이블 자동 추출</li>
                  <li>• ✅ 다국어 지원 (한글, 영어)</li>
                  <li>• ✅ 클러스터링 기반 그룹화</li>
                  <li>• ✅ 향상된 정확도</li>
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
                  <h4 className="font-semibold">파일 업로드</h4>
                  <p className="text-sm text-muted-foreground">
                    공학 도면 이미지를 업로드합니다 (JPG, PNG, PDF 지원)
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  2
                </div>
                <div>
                  <h4 className="font-semibold">버전 선택</h4>
                  <p className="text-sm text-muted-foreground">
                    v1 (GPU 가속, 빠름) 또는 v2 (고급 기능, 정확함) 선택
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                  3
                </div>
                <div>
                  <h4 className="font-semibold">옵션 설정</h4>
                  <p className="text-sm text-muted-foreground">
                    치수, GD&T, 텍스트, 테이블 추출 옵션 선택
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
                    추출된 치수, GD&T, 텍스트를 JSON 형식으로 확인
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* ⚡ 성능 비교 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">⚡ 성능 비교</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="p-2 text-left">항목</th>
                    <th className="p-2 text-left">v1 (GPU)</th>
                    <th className="p-2 text-left">v2 (Advanced)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t">
                    <td className="p-2">처리 속도</td>
                    <td className="p-2 text-green-600 font-semibold">⚡ ~5-10초</td>
                    <td className="p-2">~15-25초</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2">치수 정확도</td>
                    <td className="p-2">85%</td>
                    <td className="p-2 text-green-600 font-semibold">✅ 92%</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2">GD&T 검출</td>
                    <td className="p-2">기본</td>
                    <td className="p-2 text-green-600 font-semibold">✅ 고급</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2">테이블 추출</td>
                    <td className="p-2 text-muted-foreground">미지원</td>
                    <td className="p-2 text-green-600 font-semibold">✅ 지원</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2">다국어</td>
                    <td className="p-2">영어</td>
                    <td className="p-2 text-green-600 font-semibold">✅ 한글, 영어</td>
                  </tr>
                  <tr className="border-t">
                    <td className="p-2">권장 용도</td>
                    <td className="p-2">빠른 프로토타이핑</td>
                    <td className="p-2">정확한 생산 분석</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* 💡 팁 */}
          <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
            <h4 className="font-semibold mb-2 text-blue-900 dark:text-blue-100">
              💡 최적의 결과를 위한 팁
            </h4>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <li>• 고해상도 이미지 사용 (최소 1000x1000 권장)</li>
              <li>• 명확한 흑백 대비의 도면이 가장 좋음</li>
              <li>• v1은 속도가 중요할 때, v2는 정확도가 중요할 때 사용</li>
              <li>• 한글 포함 도면은 v2 + language=kor 옵션 사용</li>
            </ul>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
