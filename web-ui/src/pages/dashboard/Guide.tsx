import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import Mermaid from '../../components/ui/Mermaid';
import ImageZoom from '../../components/ui/ImageZoom';
import { BookOpen, Layers, Zap, Code, Database, Server } from 'lucide-react';

export default function Guide() {
  const { t } = useTranslation();

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          {t('guide.title')}
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {t('guide.subtitle')}
        </p>
      </div>

      {/* Project Overview */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <BookOpen className="w-5 h-5 mr-2" />
            {t('guide.projectOverview')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-gray-700 dark:text-gray-300">
              {t('guide.projectDescription')}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-center mb-2">
                  <Zap className="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" />
                  <h3 className="font-semibold text-blue-900 dark:text-blue-100">{t('guide.corePerformance')}</h3>
                </div>
                <ul className="text-sm space-y-1 text-blue-800 dark:text-blue-200">
                  <li>• <strong>{t('guide.corePerf1')}</strong></li>
                  <li>• {t('guide.corePerf2')}</li>
                  <li>• {t('guide.corePerf3')}</li>
                </ul>
              </div>

              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-center mb-2">
                  <Database className="w-5 h-5 mr-2 text-green-600 dark:text-green-400" />
                  <h3 className="font-semibold text-green-900 dark:text-green-100">{t('guide.trainingData')}</h3>
                </div>
                <ul className="text-sm space-y-1 text-green-800 dark:text-green-200">
                  <li>• {t('guide.trainingData1')}</li>
                  <li>• {t('guide.trainingData2')}</li>
                  <li>• {t('guide.trainingData3')}</li>
                </ul>
              </div>

              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                <div className="flex items-center mb-2">
                  <Server className="w-5 h-5 mr-2 text-purple-600 dark:text-purple-400" />
                  <h3 className="font-semibold text-purple-900 dark:text-purple-100">{t('guide.microservices')}</h3>
                </div>
                <ul className="text-sm space-y-1 text-purple-800 dark:text-purple-200">
                  <li>• 12개 독립 API 서버</li>
                  <li>• {t('guide.microservices2')}</li>
                  <li>• {t('guide.microservices3')}</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Architecture */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Layers className="w-5 h-5 mr-2" />
            {t('guide.systemArchitecture')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.systemStructure')}
              </h3>
              <ImageZoom>
                <Mermaid chart={`flowchart TB
    subgraph Frontend["🌐 Frontend :5173"]
        UI[Web UI + BlueprintFlow]
    end

    subgraph Gateway["⚙️ Gateway :8000"]
        GW[통합 오케스트레이터]
    end

    subgraph Detection["🎯 Detection"]
        YOLO[YOLO :5005]
    end

    subgraph OCR["📝 OCR"]
        direction LR
        ED[eDOCr2 :5002]
        PD[PaddleOCR :5006]
        TE[Tesseract :5008]
        TR[TrOCR :5009]
        EN[Ensemble :5011]
    end

    subgraph Segmentation["🎨 Segmentation"]
        EG[EDGNet :5012]
    end

    subgraph Preprocessing["🔧 Preprocessing"]
        ES[ESRGAN :5010]
    end

    subgraph Analysis["📊 Analysis"]
        SK[SkinModel :5003]
    end

    subgraph AI["🤖 AI"]
        VL[VL :5004]
    end

    subgraph Knowledge["🧠 Knowledge"]
        KN[Knowledge :5007]
    end

    UI --> GW
    GW --> Detection
    GW --> OCR
    GW --> Segmentation
    GW --> Preprocessing
    GW --> Analysis
    GW --> AI
    GW --> Knowledge

    style Frontend fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Gateway fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Detection fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    style OCR fill:#dcfce7,stroke:#22c55e,stroke-width:2px
    style Segmentation fill:#fae8ff,stroke:#d946ef,stroke-width:2px
    style Preprocessing fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    style Analysis fill:#ffe4e6,stroke:#f43f5e,stroke-width:2px
    style AI fill:#e0e7ff,stroke:#6366f1,stroke-width:2px
    style Knowledge fill:#f3e8ff,stroke:#a855f7,stroke-width:2px`} />
              </ImageZoom>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* YOLOv11 Pipeline */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Code className="w-5 h-5 mr-2" />
            {t('guide.yoloPipeline')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.trainingInferencePipeline')}
              </h3>
              <ImageZoom>
                <Mermaid chart={`sequenceDiagram
    participant User as 사용자
    participant Gen as 합성 데이터 생성기
    participant Train as 학습 스크립트
    participant Model as YOLOv11 모델
    participant API as YOLOv11 API
    participant Web as Web UI

    User->>Gen: 1. 합성 데이터 생성 요청
    Gen->>Gen: 2. 랜덤 배치 (크기/방향/위치)
    Gen-->>Train: 3. 데이터셋 준비 (700/150/150)

    Train->>Model: 4. 학습 시작 (100 epochs)
    Model->>Model: 5. 전이 학습 (COCO weights)
    Model-->>Train: 6. 학습 완료 (mAP50: 80.4%)

    Train->>API: 7. 모델 배포 (best.pt)

    User->>Web: 8. 도면 업로드
    Web->>API: 9. POST /api/v1/detect
    API->>Model: 10. 추론 실행
    Model-->>API: 11. 검출 결과
    API-->>Web: 12. JSON + 시각화
    Web-->>User: 13. 결과 표시`} />
              </ImageZoom>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Details - 기능별 그룹화 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{t('guide.serviceRoles')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Gateway - 오케스트레이터 */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded text-sm">⚙️ Gateway</span>
              </h3>
              <div className="p-4 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20">
                <h4 className="font-bold text-orange-900 dark:text-orange-100 mb-2">Gateway API (포트 8000)</h4>
                <p className="text-sm text-orange-800 dark:text-orange-200 mb-2">모든 백엔드 API를 통합하는 오케스트레이터</p>
                <ul className="text-xs space-y-1 text-orange-700 dark:text-orange-300">
                  <li><strong>• 엔드포인트:</strong> GET /api/v1/health, POST /api/v1/process, POST /api/v1/quote</li>
                  <li><strong>• 특징:</strong> 여러 API 결과 병합, 단일 엔드포인트 제공</li>
                </ul>
              </div>
            </div>

            {/* 🎯 Detection */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-sm">🎯 Detection</span>
              </h3>
              <div className="p-4 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold text-blue-900 dark:text-blue-100">YOLOv11 API (포트 5005)</h4>
                  <Badge className="bg-blue-600">권장</Badge>
                </div>
                <p className="text-sm text-blue-800 dark:text-blue-200 mb-2">공학 도면에서 14개 클래스 객체 검출</p>
                <ul className="text-xs space-y-1 text-blue-700 dark:text-blue-300">
                  <li><strong>• 성능:</strong> mAP50 80.4%, Precision 81%, Recall 68.6%</li>
                  <li><strong>• 특징:</strong> 합성 데이터로 학습, CPU/GPU 지원</li>
                </ul>
              </div>
            </div>

            {/* 📝 OCR */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-sm">📝 OCR</span>
                <span className="text-sm text-muted-foreground">(5개 엔진)</span>
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">eDOCr2 (5002)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">도면 전용 OCR, GD&T 추출</p>
                </div>
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">PaddleOCR (5006)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">범용 다국어 OCR, GPU 가속</p>
                </div>
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">Tesseract (5008)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">레거시 OCR, 테이블 추출</p>
                </div>
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">TrOCR (5009)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">Transformer OCR, 필기체 인식</p>
                </div>
                <div className="p-3 border-l-4 border-amber-500 bg-amber-50 dark:bg-amber-900/20 md:col-span-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-amber-900 dark:text-amber-100 text-sm">OCR Ensemble (5011)</h4>
                    <Badge className="bg-amber-600 text-xs">앙상블</Badge>
                  </div>
                  <p className="text-xs text-amber-700 dark:text-amber-300">4개 OCR 엔진 가중치 투표 융합</p>
                </div>
              </div>
            </div>

            {/* 🎨 Segmentation */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-sm">🎨 Segmentation</span>
              </h3>
              <div className="p-4 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20">
                <h4 className="font-bold text-purple-900 dark:text-purple-100 mb-2">EDGNet API (포트 5012)</h4>
                <p className="text-sm text-purple-800 dark:text-purple-200 mb-2">도면 세그멘테이션 (레이어 분리)</p>
                <ul className="text-xs space-y-1 text-purple-700 dark:text-purple-300">
                  <li><strong>• 모델:</strong> UNet (엣지), GraphSAGE (분류)</li>
                  <li><strong>• 특징:</strong> 윤곽선, 텍스트, 치수 레이어 분리</li>
                </ul>
              </div>
            </div>

            {/* 🔧 Preprocessing */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded text-sm">🔧 Preprocessing</span>
              </h3>
              <div className="p-4 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
                <h4 className="font-bold text-yellow-900 dark:text-yellow-100 mb-2">ESRGAN API (포트 5010)</h4>
                <p className="text-sm text-yellow-800 dark:text-yellow-200 mb-2">Real-ESRGAN 이미지 업스케일링</p>
                <ul className="text-xs space-y-1 text-yellow-700 dark:text-yellow-300">
                  <li><strong>• 특징:</strong> 2x/4x 업스케일, 노이즈 제거</li>
                  <li><strong>• 활용:</strong> 저해상도 도면 전처리</li>
                </ul>
              </div>
            </div>

            {/* 📊 Analysis */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded text-sm">📊 Analysis</span>
              </h3>
              <div className="p-4 border-l-4 border-pink-500 bg-pink-50 dark:bg-pink-900/20">
                <h4 className="font-bold text-pink-900 dark:text-pink-100 mb-2">SkinModel API (포트 5003)</h4>
                <p className="text-sm text-pink-800 dark:text-pink-200 mb-2">공차 예측 및 제조 가능성 분석</p>
                <ul className="text-xs space-y-1 text-pink-700 dark:text-pink-300">
                  <li><strong>• 특징:</strong> 치수→공차 예측, 제조 난이도 산정</li>
                </ul>
              </div>
            </div>

            {/* 🤖 AI */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded text-sm">🤖 AI</span>
              </h3>
              <div className="p-4 border-l-4 border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold text-indigo-900 dark:text-indigo-100">VL API (포트 5004)</h4>
                  <Badge className="bg-indigo-600">멀티모달</Badge>
                </div>
                <p className="text-sm text-indigo-800 dark:text-indigo-200 mb-2">Vision-Language 멀티모달 분석</p>
                <ul className="text-xs space-y-1 text-indigo-700 dark:text-indigo-300">
                  <li><strong>• 모델:</strong> BLIP-base (로컬), Claude/GPT-4V (선택)</li>
                  <li><strong>• 특징:</strong> 이미지 캡셔닝, VQA, 프롬프트 기반 분석</li>
                </ul>
              </div>
            </div>

            {/* 🧠 Knowledge */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded text-sm">🧠 Knowledge</span>
              </h3>
              <div className="p-4 border-l-4 border-violet-500 bg-violet-50 dark:bg-violet-900/20">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold text-violet-900 dark:text-violet-100">Knowledge API (포트 5007)</h4>
                  <Badge className="bg-violet-600">GraphRAG</Badge>
                </div>
                <p className="text-sm text-violet-800 dark:text-violet-200 mb-2">Neo4j + GraphRAG 도메인 지식 엔진</p>
                <ul className="text-xs space-y-1 text-violet-700 dark:text-violet-300">
                  <li><strong>• 특징:</strong> 유사 부품 검색, 규격 검증, 비용 추정</li>
                  <li><strong>• 기술:</strong> GraphRAG + VectorRAG 하이브리드</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Start */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{t('guide.quickStartGuide')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">1️⃣ YOLOv11로 도면 분석 (권장)</h3>
              <ol className="space-y-2 text-sm ml-4">
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    1
                  </span>
                  <span>
                    <a href="/test/yolo" className="text-blue-600 hover:underline font-medium">
                      YOLOv11 테스트 페이지
                    </a>로 이동
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    2
                  </span>
                  <span>공학 도면 이미지 업로드 (JPG, PNG)</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    3
                  </span>
                  <span>옵션 조정: Confidence 0.25, Image Size 1280, Visualize 체크</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    4
                  </span>
                  <span>"Run Detection" 클릭</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    5
                  </span>
                  <span>결과 확인: 검출된 객체 목록, 바운딩 박스, 시각화 이미지</span>
                </li>
              </ol>
            </div>

            <div className="border-t pt-4">
              <h3 className="font-semibold mb-2 flex items-center text-cyan-900 dark:text-cyan-100">
                <span className="text-xl mr-2">➕</span>
                2️⃣ 새로운 API 추가하기 (동적 시스템)
              </h3>
              <ol className="space-y-2 text-sm ml-4">
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    1
                  </span>
                  <span>
                    <a href="/dashboard" className="text-cyan-600 hover:underline font-medium">
                      Dashboard
                    </a>에서 우측 상단 <strong>"API 추가"</strong> 버튼 클릭
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    2
                  </span>
                  <span>API 정보 입력: ID, 이름, URL (예: <code>http://localhost:5007</code>), 포트, 아이콘, 색상</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    3
                  </span>
                  <span>저장하면 <strong>즉시 자동 반영</strong>: Dashboard 헬스체크, Settings 패널, BlueprintFlow 노드</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    4
                  </span>
                  <span className="text-gray-700 dark:text-gray-300">
                    <strong>위치 무관:</strong> Docker 위치 상관없이 HTTP 통신 가능하면 OK
                    (localhost, 원격 서버, 클라우드 모두 가능)
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">
                    5
                  </span>
                  <span className="text-gray-700 dark:text-gray-300">
                    <strong>필수 요구사항:</strong> API는 <code>/api/v1/health</code> 엔드포인트 필요
                  </span>
                </li>
              </ol>
              <div className="mt-3 p-3 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded">
                <p className="text-xs text-cyan-800 dark:text-cyan-200">
                  💡 <strong>예시:</strong> 팀원이 192.168.1.200:5007에 Text Classifier API를 배포했다면,
                  Dashboard에서 해당 정보만 입력하면 코드 수정 없이 즉시 사용 가능!
                </p>
              </div>
            </div>

            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                💡 팁
              </h4>
              <ul className="text-sm space-y-1 text-yellow-800 dark:text-yellow-200">
                <li>• 첫 번째 추론은 모델 로딩으로 인해 느릴 수 있습니다 (이후 빠름)</li>
                <li>• 고해상도 이미지는 Image Size를 1920으로 설정하세요</li>
                <li>• 검출 결과가 너무 많으면 Confidence를 높이세요 (0.25 → 0.5)</li>
                <li>• 가이드 내 Mermaid 다이어그램은 <a href="https://mermaid.live" target="_blank" rel="noopener noreferrer" className="underline">mermaid.live</a>에서 확인 가능</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Documentation Links */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{t('guide.documentation')}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {t('guide.docDescription')}
          </p>

          {/* 사용자 가이드 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center text-blue-900 dark:text-blue-100">
              <span className="bg-blue-100 dark:bg-blue-900 p-2 rounded mr-2">📖</span>
              {t('guide.userGuide')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded">
                <div className="font-medium">USER_GUIDE.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">상세 사용자 매뉴얼 (10분 숙달)</div>
              </div>
              <div className="p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded">
                <div className="font-medium">API_USAGE_MANUAL.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">API 엔드포인트 및 사용법</div>
              </div>
              <div className="p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded">
                <div className="font-medium">TROUBLESHOOTING_GUIDE.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">문제 해결 가이드 (FAQ)</div>
              </div>
              <div className="p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded">
                <div className="font-medium">KOREAN_EXECUTION_GUIDE.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">한국어 실행 가이드</div>
              </div>
              <div className="p-3 border-l-4 border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20 rounded">
                <div className="font-medium flex items-center">
                  DYNAMIC_API_SYSTEM_GUIDE.md ⭐
                </div>
                <div className="text-xs text-cyan-600 dark:text-cyan-400 mt-1">
                  동적 API 추가 시스템 (Dashboard/Settings/BlueprintFlow 자동 반영)
                </div>
              </div>
              <div className="p-3 border-l-4 border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20 rounded">
                <div className="font-medium">BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md</div>
                <div className="text-xs text-cyan-600 dark:text-cyan-400 mt-1">BlueprintFlow API 통합 가이드</div>
              </div>
              <div className="p-3 border-l-4 border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20 rounded">
                <div className="font-medium">TESTING_GUIDE_DYNAMIC_API.md</div>
                <div className="text-xs text-cyan-600 dark:text-cyan-400 mt-1">동적 API 시스템 테스트 가이드 (23분 완전 검증)</div>
              </div>
            </div>
          </div>

          {/* 개발자 가이드 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center text-green-900 dark:text-green-100">
              <span className="bg-green-100 dark:bg-green-900 p-2 rounded mr-2">👨‍💻</span>
              {t('guide.developerGuide')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20 rounded">
                <div className="font-medium">CLAUDE_KR.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Claude AI 활용 가이드 (한국어)</div>
              </div>
              <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20 rounded">
                <div className="font-medium">CONTRIBUTING.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">기여 가이드 (코드 스타일, PR 규칙)</div>
              </div>
              <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20 rounded">
                <div className="font-medium">GIT_WORKFLOW.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Git 브랜치 전략 & 워크플로우</div>
              </div>
              <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20 rounded">
                <div className="font-medium">CLAUDE.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Claude AI 활용 가이드 (English)</div>
              </div>
            </div>
          </div>

          {/* 기술 구현 가이드 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center text-purple-900 dark:text-purple-100">
              <span className="bg-purple-100 dark:bg-purple-900 p-2 rounded mr-2">🔧</span>
              {t('guide.technicalGuide')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="p-3 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20 rounded">
                <div className="font-medium">yolo/IMPLEMENTATION_GUIDE.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">YOLOv11 상세 구현 가이드</div>
              </div>
              <div className="p-3 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20 rounded">
                <div className="font-medium">yolo/QUICKSTART.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">YOLO 빠른 시작 (5분)</div>
              </div>
              <div className="p-3 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20 rounded">
                <div className="font-medium">ocr/EDOCR_V1_V2_DEPLOYMENT.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">eDOCr v1/v2 배포 가이드</div>
              </div>
              <div className="p-3 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20 rounded">
                <div className="font-medium">ocr/OCR_IMPROVEMENT_STRATEGY.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">OCR 성능 개선 전략</div>
              </div>
              <div className="p-3 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20 rounded">
                <div className="font-medium">VL_API_IMPLEMENTATION_GUIDE.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Vision Language Model API 구현</div>
              </div>
              <div className="p-3 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20 rounded">
                <div className="font-medium">SYNTHETIC_DATA_STRATEGY.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">합성 데이터 생성 전략</div>
              </div>
            </div>
          </div>

          {/* 아키텍처 & 분석 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center text-orange-900 dark:text-orange-100">
              <span className="bg-orange-100 dark:bg-orange-900 p-2 rounded mr-2">🏗️</span>
              {t('guide.architectureAnalysis')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="p-3 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20 rounded">
                <div className="font-medium">PROJECT_STRUCTURE_ANALYSIS.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">프로젝트 구조 상세 분석</div>
              </div>
              <div className="p-3 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20 rounded">
                <div className="font-medium">DEPLOYMENT_STATUS.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">현재 배포 상태</div>
              </div>
              <div className="p-3 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20 rounded">
                <div className="font-medium">PRODUCTION_READINESS_ANALYSIS.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">프로덕션 준비도 평가</div>
              </div>
              <div className="p-3 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20 rounded">
                <div className="font-medium">IMPLEMENTATION_STATUS.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">구현 진행 현황</div>
              </div>
              <div className="p-3 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20 rounded">
                <div className="font-medium">DECISION_MATRIX.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">기술 의사결정 기록</div>
              </div>
            </div>
          </div>

          {/* 최종 보고서 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center text-red-900 dark:text-red-100">
              <span className="bg-red-100 dark:bg-red-900 p-2 rounded mr-2">📋</span>
              {t('guide.finalReports')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="p-3 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20 rounded">
                <div className="font-medium">FINAL_COMPREHENSIVE_REPORT.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">최종 종합 보고서 (전체 구현 요약)</div>
              </div>
              <div className="p-3 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20 rounded">
                <div className="font-medium">COMPREHENSIVE_EVALUATION_REPORT.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">종합 평가 보고서 (성능 평가)</div>
              </div>
            </div>
          </div>

          {/* 루트 문서 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center text-gray-900 dark:text-gray-100">
              <span className="bg-gray-100 dark:bg-gray-800 p-2 rounded mr-2">📄</span>
              {t('guide.rootDocs')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="p-3 border-l-4 border-gray-500 bg-gray-50 dark:bg-gray-800 rounded">
                <div className="font-medium">README.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">프로젝트 소개 및 빠른 시작</div>
              </div>
              <div className="p-3 border-l-4 border-gray-500 bg-gray-50 dark:bg-gray-800 rounded">
                <div className="font-medium">QUICKSTART.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">5분 빠른 시작 가이드</div>
              </div>
              <div className="p-3 border-l-4 border-gray-500 bg-gray-50 dark:bg-gray-800 rounded">
                <div className="font-medium">PROJECT_STRUCTURE.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">프로젝트 구조 가이드 (v2.0)</div>
              </div>
              <div className="p-3 border-l-4 border-gray-500 bg-gray-50 dark:bg-gray-800 rounded">
                <div className="font-medium">scripts/README.md</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">스크립트 가이드 (테스트/유틸리티)</div>
              </div>
            </div>
          </div>

          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2 flex items-center">
              <span className="mr-2">{t('guide.docAccess')}</span>
            </h4>
            <ul className="text-sm space-y-1 text-yellow-800 dark:text-yellow-200">
              <li>• <strong>로컬 접근:</strong> <code className="bg-yellow-100 dark:bg-yellow-900 px-2 py-1 rounded">/home/uproot/ax/poc/docs/</code></li>
              <li>• <strong>GitHub:</strong> 프로젝트 저장소의 docs/ 디렉토리</li>
              <li>• <strong>전체 색인:</strong> <code className="bg-yellow-100 dark:bg-yellow-900 px-2 py-1 rounded">docs/README.md</code> 참조</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* BlueprintFlow Architecture (Implemented) */}
      <Card className="mb-6 border-4 border-green-500">
        <CardHeader className="bg-green-50 dark:bg-green-900/20">
          <CardTitle className="flex items-center text-green-900 dark:text-green-100">
            <span className="text-2xl mr-2">✅</span>
            BlueprintFlow (Phase 1-4 완료)
            <Badge className="ml-3 bg-green-600">구현 완료</Badge>
          </CardTitle>
          <p className="text-sm text-green-800 dark:text-green-200 mt-2">
            비주얼 워크플로우 빌더 - 드래그 앤 드롭으로 API 파이프라인 조합
          </p>
          <div className="mt-3 flex gap-2">
            <a href="/blueprintflow/builder" className="px-3 py-1 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition-colors">
              빌더 열기
            </a>
            <a href="/blueprintflow/templates" className="px-3 py-1 bg-green-100 text-green-800 rounded-lg text-sm hover:bg-green-200 transition-colors dark:bg-green-800 dark:text-green-100">
              템플릿 보기
            </a>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* 구현 현황 */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 rounded text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400">13</div>
                <div className="text-sm text-green-800 dark:text-green-200">노드 타입</div>
              </div>
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">11</div>
                <div className="text-sm text-blue-800 dark:text-blue-200">API Executor</div>
              </div>
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border-l-4 border-purple-500 rounded text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">60%</div>
                <div className="text-sm text-purple-800 dark:text-purple-200">병렬 실행 속도향상</div>
              </div>
              <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border-l-4 border-cyan-500 rounded text-center">
                <div className="text-3xl font-bold text-cyan-600 dark:text-cyan-400">4</div>
                <div className="text-sm text-cyan-800 dark:text-cyan-200">템플릿</div>
              </div>
            </div>

            {/* 노드 타입 */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                지원 노드 타입 (13종)
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
                  <strong>입력 노드</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>• ImageInput</li>
                    <li>• TextInput (VL용)</li>
                  </ul>
                </div>
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded">
                  <strong>핵심 API</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>• YOLO</li>
                    <li>• eDOCr2</li>
                    <li>• PaddleOCR</li>
                    <li>• EDGNet</li>
                    <li>• SkinModel</li>
                    <li>• VL</li>
                  </ul>
                </div>
                <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded">
                  <strong>확장 API</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>• TrOCR</li>
                    <li>• ESRGAN</li>
                    <li>• OCR Ensemble</li>
                    <li>• Knowledge</li>
                  </ul>
                </div>
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded">
                  <strong>제어 노드</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>• IF (조건 분기)</li>
                    <li>• Loop</li>
                    <li>• Merge</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* 전체 시스템 아키텍처 */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.bfSystemStructure')}
              </h3>
              <ImageZoom>
                <Mermaid chart={`flowchart TB
    subgraph Frontend["🌐 Frontend :5173"]
        UI[React + ReactFlow]
        NP[노드 팔레트]
    end

    subgraph Gateway["⚙️ Gateway :8000"]
        PE[Pipeline Engine]
        EX[Executors x11]
    end

    subgraph APIs["🤖 Model APIs (기능별)"]
        DET["🎯 Detection<br/>YOLO"]
        OCR_G["📝 OCR<br/>eDOCr2 PaddleOCR +3"]
        SEG["🎨 Segmentation<br/>EDGNet"]
        PRE["🔧 Preprocessing<br/>ESRGAN"]
        ANA["📊 Analysis<br/>SkinModel"]
        AI_G["🤖 AI<br/>VL"]
        KNO["🧠 Knowledge"]
    end

    subgraph DB["💾 Storage"]
        PG[(PostgreSQL)]
    end

    UI -->|workflow JSON| PE
    PE --> EX
    EX --> APIs
    PE -.->|저장| PG

    style Frontend fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Gateway fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style APIs fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style DB fill:#fce4ec,stroke:#c2185b,stroke-width:2px`} />
              </ImageZoom>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                💡 Executor는 Gateway 내부 모듈로 각 API를 호출하는 어댑터 역할
              </p>
            </div>

            {/* 워크플로우 빌더 UI */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.workflowBuilderUI')}
              </h3>
              <ImageZoom>
                <Mermaid chart={`flowchart LR
    subgraph Left["좌측 사이드바"]
        NP[노드 팔레트]
        API[API 노드 x10]
        CTL[제어 노드 x3]
    end

    subgraph Center["중앙 캔버스"]
        RF[ReactFlow]
        CN[커스텀 노드]
        MM[미니맵]
    end

    subgraph Right["우측 패널"]
        PP[속성 패널]
        PE[파라미터 편집]
    end

    subgraph Top["상단 툴바"]
        TB[저장/실행/검증]
    end

    subgraph Bottom["하단"]
        EM[실행 모니터]
    end

    NP --> RF
    RF --> PP
    TB --> RF
    RF --> EM

    style Center fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Left fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Right fill:#e8f5e9,stroke:#388e3c,stroke-width:2px`} />
              </ImageZoom>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                💡 ReactFlow: 드래그 앤 드롭, 줌/팬, 연결 자동 생성 기능 제공
              </p>
            </div>

            {/* 파이프라인 엔진 실행 흐름 */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.pipelineEngineFlow')}
              </h3>
              <ImageZoom>
                <Mermaid chart={`sequenceDiagram
    participant U as 사용자
    participant WB as Builder
    participant PE as Pipeline Engine
    participant API as APIs

    U->>WB: 노드 배치 & 연결
    U->>WB: 실행 클릭
    WB->>PE: workflow JSON

    PE->>PE: DAG 검증
    PE->>PE: 실행 순서 계산

    loop 각 노드
        PE->>API: 노드 실행
        API-->>PE: 결과 반환
    end

    PE-->>WB: 완료
    WB-->>U: 결과 시각화`} />
              </ImageZoom>
            </div>

            {/* 조건부 분기 예시 */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.conditionalBranchExample')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {t('guide.conditionalBranchDesc')}
              </p>
              <ImageZoom>
                <Mermaid chart={`flowchart LR
    A[YOLO] --> B{IF 노드}
    B -->|detections > 0| C[eDOCr2]
    B -->|else| D[PaddleOCR]
    C --> E[결과]
    D --> E

    style B fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    style C fill:#d1fae5,stroke:#10b981,stroke-width:2px
    style D fill:#e5e7eb,stroke:#6b7280,stroke-width:2px`} />
              </ImageZoom>
            </div>

            {/* 구현 현황 (완료됨) */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
              <h3 className="font-semibold mb-3 text-green-900 dark:text-green-100">
                구현 현황 (Phase 1-4 완료)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-green-500">
                  <div className="font-medium text-green-900 dark:text-green-100 flex items-center">
                    ✅ Phase 1: 기반 구조
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>✓ ReactFlow 캔버스 구축</li>
                    <li>✓ 노드 팔레트 (13종)</li>
                    <li>✓ 드래그 앤 드롭</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-green-500">
                  <div className="font-medium text-green-900 dark:text-green-100 flex items-center">
                    ✅ Phase 2: 노드 구현
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>✓ 11개 API Executor</li>
                    <li>✓ IF/Merge/Loop 제어 노드</li>
                    <li>✓ TextInput (VL 연동)</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-green-500">
                  <div className="font-medium text-green-900 dark:text-green-100 flex items-center">
                    ✅ Phase 3: 노드 메타데이터
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>✓ 상세 패널 (파라미터 편집)</li>
                    <li>✓ 한국어/영어 번역</li>
                    <li>✓ 노드별 아이콘/색상</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-green-500">
                  <div className="font-medium text-green-900 dark:text-green-100 flex items-center">
                    ✅ Phase 4: 백엔드 엔진
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>✓ Pipeline Engine (DAG 실행)</li>
                    <li>✓ 병렬 실행 (60% 속도 향상)</li>
                    <li>✓ 실시간 진행 상황</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-amber-500 md:col-span-2">
                  <div className="font-medium text-amber-900 dark:text-amber-100 flex items-center">
                    🔄 Phase 5: VL + TextInput 통합 (진행 중)
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>• VL API prompt 파라미터 연동</li>
                    <li>• 멀티 입력 노드 지원</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* 구현 규모 */}
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center">
                구현 규모
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                    Frontend
                  </div>
                  <ul className="text-xs space-y-1 text-blue-800 dark:text-blue-200">
                    <li>• 컴포넌트: 20+ 파일</li>
                    <li>• 코드: ~3,500줄</li>
                    <li>• ReactFlow + Zustand</li>
                  </ul>
                </div>
                <div>
                  <div className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                    Backend (Executors)
                  </div>
                  <ul className="text-xs space-y-1 text-blue-800 dark:text-blue-200">
                    <li>• Executor: 11개</li>
                    <li>• 코드: ~2,500줄</li>
                    <li>• Pipeline Engine</li>
                  </ul>
                </div>
                <div>
                  <div className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                    API 통합
                  </div>
                  <ul className="text-xs space-y-1 text-blue-800 dark:text-blue-200">
                    <li>• 핵심: 6개 API</li>
                    <li>• 확장: 5개 API</li>
                    <li>• 지식 엔진: 1개</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* 참고 문서 */}
            <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded-lg">
              <h4 className="font-semibold text-cyan-900 dark:text-cyan-100 mb-2 flex items-center">
                <span className="mr-2">{t('guide.detailedDesignDocs')}</span>
              </h4>
              <ul className="text-sm space-y-2 text-cyan-800 dark:text-cyan-200">
                <li>
                  • <strong>완전한 설계서:</strong>{' '}
                  <code className="bg-cyan-100 dark:bg-cyan-900 px-2 py-1 rounded text-xs">
                    docs/BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md
                  </code>
                </li>
                <li>
                  • <strong>현재 vs BlueprintFlow 평가:</strong>{' '}
                  <code className="bg-cyan-100 dark:bg-cyan-900 px-2 py-1 rounded text-xs">
                    docs/BLUEPRINTFLOW_ARCHITECTURE_EVALUATION.md
                  </code>
                </li>
                <li>
                  • <strong>하이브리드 vs 완전 구현:</strong>{' '}
                  <code className="bg-cyan-100 dark:bg-cyan-900 px-2 py-1 rounded text-xs">
                    docs/HYBRID_VS_FULL_BLUEPRINTFLOW_COMPARISON.md
                  </code>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
