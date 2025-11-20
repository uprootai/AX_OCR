import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import Mermaid from '../../components/ui/Mermaid';
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
                  <li>• {t('guide.microservices1')}</li>
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
              <Mermaid chart={`graph TB
    subgraph Frontend
        UI["Web UI :5173\nReact + Vite"]
    end

    subgraph BackendAPIs["Backend APIs"]
        GW["Gateway API :8000\n통합 API 게이트웨이"]
        YOLO["YOLOv11 API :5005\n⭐ 주력 엔진\nmAP50: 80.4%"]
        ED1["eDOCr v1 API :5001\nGPU 가속 OCR"]
        ED2["eDOCr v2 API :5002\n고급 OCR + 테이블"]
        EG["EDGNet API :5012\n세그멘테이션"]
        SK["Skin Model API :5003\n공차 예측"]
    end

    subgraph DataModels["Data & Models"]
        SYN["합성 데이터 생성기\n1000+ 이미지"]
        MODEL["YOLOv11n 모델\nbest.pt - 5.3MB"]
    end

    UI --> GW
    UI --> YOLO
    UI --> ED1
    UI --> ED2
    UI --> EG
    UI --> SK

    GW --> YOLO
    GW --> ED1
    GW --> ED2
    GW --> EG
    GW --> SK

    SYN -.학습.-> MODEL
    MODEL --> YOLO

    style YOLO stroke:#1976d2,stroke-width:3px
    style UI stroke:#7b1fa2
    style GW stroke:#f57c00
    style MODEL stroke:#388e3c`} />
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
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Details */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{t('guide.serviceRoles')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* YOLOv11 */}
            <div className="p-4 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-bold text-blue-900 dark:text-blue-100">
                  ⭐ YOLOv11 API (포트 5005)
                </h3>
                <Badge className="bg-blue-600">권장</Badge>
              </div>
              <p className="text-sm text-blue-800 dark:text-blue-200 mb-2">
                공학 도면에서 14개 클래스 객체 검출 (치수, GD&T, 공차 등)
              </p>
              <ul className="text-xs space-y-1 text-blue-700 dark:text-blue-300">
                <li><strong>• 엔드포인트:</strong> GET /api/v1/health, POST /api/v1/detect</li>
                <li><strong>• 성능:</strong> mAP50 80.4%, Precision 81%, Recall 68.6%</li>
                <li><strong>• 특징:</strong> 합성 데이터로 학습, 완전 무료, CPU/GPU 지원</li>
                <li><strong>• 테스트:</strong> <a href="/test/yolo" className="underline hover:text-blue-900 dark:hover:text-blue-100">/test/yolo</a></li>
              </ul>
            </div>

            {/* Gateway */}
            <div className="p-4 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20">
              <h3 className="font-bold text-orange-900 dark:text-orange-100 mb-2">
                Gateway API (포트 8000)
              </h3>
              <p className="text-sm text-orange-800 dark:text-orange-200 mb-2">
                모든 백엔드 API를 통합하는 게이트웨이
              </p>
              <ul className="text-xs space-y-1 text-orange-700 dark:text-orange-300">
                <li><strong>• 엔드포인트:</strong> GET /api/v1/health, POST /api/v1/process, POST /api/v1/quote</li>
                <li><strong>• 특징:</strong> 여러 API 결과 병합, 단일 엔드포인트 제공</li>
                <li><strong>• 테스트:</strong> <a href="/test/gateway" className="underline hover:text-orange-900 dark:hover:text-orange-100">/test/gateway</a></li>
              </ul>
            </div>

            {/* eDOCr v1/v2 */}
            <div className="p-4 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
              <h3 className="font-bold text-green-900 dark:text-green-100 mb-2">
                eDOCr v1/v2 API (포트 5001, 5002)
              </h3>
              <p className="text-sm text-green-800 dark:text-green-200 mb-2">
                OCR 기반 치수 및 GD&T 추출 (v1: GPU 가속, v2: 고급 기능)
              </p>
              <ul className="text-xs space-y-1 text-green-700 dark:text-green-300">
                <li><strong>• 엔드포인트:</strong> POST /api/v1/ocr, POST /api/v2/ocr</li>
                <li><strong>• v1 특징:</strong> GPU 가속, 빠른 처리</li>
                <li><strong>• v2 특징:</strong> 테이블 OCR (Tesseract), 고급 세그멘테이션</li>
                <li><strong>• 주의:</strong> F1 Score 8.3% (YOLOv11 권장)</li>
                <li><strong>• 테스트:</strong> <a href="/test/edocr2" className="underline hover:text-green-900 dark:hover:text-green-100">/test/edocr2</a></li>
              </ul>
            </div>

            {/* EDGNet */}
            <div className="p-4 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20">
              <h3 className="font-bold text-purple-900 dark:text-purple-100 mb-2">
                EDGNet API (포트 5012)
              </h3>
              <p className="text-sm text-purple-800 dark:text-purple-200 mb-2">
                도면 세그멘테이션 (레이어 분리)
              </p>
              <ul className="text-xs space-y-1 text-purple-700 dark:text-purple-300">
                <li><strong>• 엔드포인트:</strong> POST /api/v1/segment</li>
                <li><strong>• 특징:</strong> 선, 치수, 텍스트 레이어 분리</li>
                <li><strong>• 테스트:</strong> <a href="/test/edgnet" className="underline hover:text-purple-900 dark:hover:text-purple-100">/test/edgnet</a></li>
              </ul>
            </div>

            {/* Skin Model */}
            <div className="p-4 border-l-4 border-pink-500 bg-pink-50 dark:bg-pink-900/20">
              <h3 className="font-bold text-pink-900 dark:text-pink-100 mb-2">
                Skin Model API (포트 5003)
              </h3>
              <p className="text-sm text-pink-800 dark:text-pink-200 mb-2">
                공차 예측 및 검증
              </p>
              <ul className="text-xs space-y-1 text-pink-700 dark:text-pink-300">
                <li><strong>• 엔드포인트:</strong> POST /api/v1/predict, POST /api/v1/validate</li>
                <li><strong>• 특징:</strong> 기계 학습 기반 공차 예측</li>
                <li><strong>• 테스트:</strong> <a href="/test/skinmodel" className="underline hover:text-pink-900 dark:hover:text-pink-100">/test/skinmodel</a></li>
              </ul>
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

      {/* BlueprintFlow Architecture (Future Design) */}
      <Card className="mb-6 border-4 border-cyan-500">
        <CardHeader className="bg-cyan-50 dark:bg-cyan-900/20">
          <CardTitle className="flex items-center text-cyan-900 dark:text-cyan-100">
            <span className="text-2xl mr-2">🔮</span>
            {t('guide.blueprintflowArchitecture')}
          </CardTitle>
          <p className="text-sm text-cyan-800 dark:text-cyan-200 mt-2">
            {t('guide.blueprintflowSubtitle')}
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* 현재 vs BlueprintFlow 비교 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 border-l-4 border-gray-500 rounded">
                <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-2">
                  {t('guide.currentArchitecture')}
                </h3>
                <ul className="text-sm space-y-1 text-gray-700 dark:text-gray-300">
                  <li>✅ {t('guide.currentArch1')}</li>
                  <li>✅ {t('guide.currentArch2')}</li>
                  <li>✅ {t('guide.currentArch3')}</li>
                  <li>❌ {t('guide.currentArch4')}</li>
                  <li>❌ {t('guide.currentArch5')}</li>
                </ul>
              </div>

              <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border-l-4 border-cyan-500 rounded">
                <h3 className="font-bold text-cyan-900 dark:text-cyan-100 mb-2">
                  {t('guide.blueprintflowArch')}
                </h3>
                <ul className="text-sm space-y-1 text-cyan-700 dark:text-cyan-300">
                  <li>✅ {t('guide.bfArch1')}</li>
                  <li>✅ {t('guide.bfArch2')}</li>
                  <li>✅ {t('guide.bfArch3')}</li>
                  <li>✅ {t('guide.bfArch4')}</li>
                  <li>✅ {t('guide.bfArch5')}</li>
                </ul>
              </div>
            </div>

            {/* 전체 시스템 아키텍처 */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.bfSystemStructure')}
              </h3>
              <Mermaid chart={`%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'transparent','primaryBorderColor':'#333','lineColor':'#666','secondaryColor':'transparent','tertiaryColor':'transparent'}}}%%
graph TB
    subgraph "Frontend Layer :5173"
        UI["React App"]
        WB["WorkflowBuilder<br/>ReactFlow Canvas"]
        WM["WorkflowManager<br/>Save/Load/Share"]
        EX["ExecutionMonitor<br/>실시간 WebSocket"]
        NP["NodePalette<br/>8 API + 3 제어 노드"]
    end

    subgraph "Gateway API :8000"
        GW["FastAPI Server"]
        WE["/api/v1/workflow/execute<br/>POST 엔드포인트"]
        WR["/api/v1/workflow/save<br/>저장 엔드포인트"]
        PE["PipelineEngine<br/>DAG 실행 엔진"]
        DV["DAGValidator<br/>순환 참조 검증"]
        TS["TopologicalSort<br/>실행 순서 정렬"]
        DM["DataMapper<br/>노드 간 데이터 매핑"]
    end

    subgraph "Data Layer"
        WS["PostgreSQL<br/>workflow_definitions"]
        WH["Workflow History<br/>execution_logs"]
    end

    subgraph "Node Executors (gateway-api/executors/)"
        NE1["yolo_executor.py"]
        NE2["edocr_executor.py"]
        NE3["edgnet_executor.py"]
        NE4["skinmodel_executor.py"]
        NE5["if_executor.py<br/>조건 분기"]
        NE6["merge_executor.py<br/>병렬 합병"]
        NE7["loop_executor.py<br/>반복 처리"]
        NE8["vl_executor.py"]
    end

    subgraph "Model APIs (독립 컨테이너)"
        YOLO["YOLO API :5005<br/>객체 검출"]
        ED2["eDOCr2 v2 :5002<br/>차원 OCR"]
        EG["EDGNet :5012<br/>엣지 세그먼트"]
        SK["Skin Model :5003<br/>공차 분석"]
        VL["VL API :5004<br/>멀티모달 분석"]
        PD["PaddleOCR :5006<br/>범용 OCR"]
    end

    UI --> WB
    UI --> WM
    UI --> EX
    WB --> NP

    WB -->|"workflow JSON"| WE
    WM -->|"save/load"| WR
    EX -->|"ws://status"| GW

    WE --> PE
    WR --> WS
    PE --> WH
    PE --> DV
    PE --> TS
    PE --> DM

    PE -.->|"dynamic dispatch"| NE1
    PE -.->|"dynamic dispatch"| NE2
    PE -.->|"dynamic dispatch"| NE3
    PE -.->|"dynamic dispatch"| NE4
    PE -.->|"dynamic dispatch"| NE5
    PE -.->|"dynamic dispatch"| NE6
    PE -.->|"dynamic dispatch"| NE7
    PE -.->|"dynamic dispatch"| NE8

    NE1 -->|"HTTP POST"| YOLO
    NE2 -->|"HTTP POST"| ED2
    NE3 -->|"HTTP POST"| EG
    NE4 -->|"HTTP POST"| SK
    NE8 -->|"HTTP POST"| VL

    style WB stroke:#1976d2,stroke-width:3px
    style PE stroke:#f57c00,stroke-width:3px
    style GW stroke:#7b1fa2,stroke-width:2px
    style DV stroke:#d32f2f,stroke-width:2px
    style NE5 stroke:#388e3c,stroke-width:2px`} />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                💡 Executor는 Gateway 내부 모듈로 각 API를 호출하는 어댑터 역할
              </p>
            </div>

            {/* 워크플로우 빌더 UI */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.workflowBuilderUI')}
              </h3>
              <Mermaid chart={`%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'transparent','primaryBorderColor':'#333','lineColor':'#666','secondaryColor':'transparent','tertiaryColor':'transparent'}}}%%
graph TB
    subgraph "BlueprintFlowBuilder.tsx (메인 페이지)"
        WBP["워크플로우 상태 관리<br/>useWorkflowStore()"]

        subgraph "좌측 사이드바 (w-64)"
            NP["NodePalette.tsx"]
            NPG1["API 노드 그룹"]
            NPG2["제어 노드 그룹"]
            NPY["YoloNode<br/>드래그 가능"]
            NPE["EdocrNode<br/>드래그 가능"]
            NPI["IfNode<br/>조건 분기"]
            NPM["MergeNode<br/>병렬 합병"]
        end

        subgraph "중앙 캔버스 (flex-1)"
            RF["ReactFlow 컴포넌트"]
            CN["CustomNode.tsx<br/>노드 렌더러"]
            CE["CustomEdge.tsx<br/>엣지 렌더러"]
            MN["MiniMap<br/>미니맵"]
            CT["Controls<br/>줌/핏"]
            BG["Background<br/>격자무늬"]
        end

        subgraph "우측 패널 (w-80)"
            PP["PropertyPanel.tsx"]
            NI["NodeInspector<br/>선택된 노드 정보"]
            PF["ParamEditor<br/>동적 파라미터 폼"]
            VL["ValidationLog<br/>실시간 검증"]
        end

        subgraph "상단 툴바"
            TB["Toolbar.tsx"]
            SA["Save/Load 버튼"]
            EX["Execute 버튼"]
            VA["Validate 버튼"]
            UN["Undo/Redo"]
        end

        subgraph "하단 모니터"
            EM["ExecutionMonitor.tsx"]
            PR["ProgressBar<br/>전체 진행률"]
            NL["NodeLog<br/>노드별 상태"]
            WS["WebSocket 연결<br/>실시간 업데이트"]
        end
    end

    WBP --> NP
    WBP --> RF
    WBP --> PP
    WBP --> TB
    WBP --> EM

    NP --> NPG1
    NP --> NPG2
    NPG1 --> NPY
    NPG1 --> NPE
    NPG2 --> NPI
    NPG2 --> NPM

    RF --> CN
    RF --> CE
    RF --> MN
    RF --> CT
    RF --> BG

    PP --> NI
    PP --> PF
    PP --> VL

    TB --> SA
    TB --> EX
    TB --> VA
    TB --> UN

    EM --> PR
    EM --> NL
    EM --> WS

    style RF stroke:#1976d2,stroke-width:3px
    style WBP stroke:#7b1fa2,stroke-width:2px
    style CN stroke:#388e3c,stroke-width:2px
    style EM stroke:#f57c00,stroke-width:2px`} />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                💡 ReactFlow: 드래그 앤 드롭, 줌/팬, 연결 자동 생성 기능 제공
              </p>
            </div>

            {/* 파이프라인 엔진 실행 흐름 */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.pipelineEngineFlow')}
              </h3>
              <Mermaid chart={`sequenceDiagram
    participant U as 사용자
    participant WB as Workflow Builder
    participant GW as Gateway API
    participant PE as Pipeline Engine
    participant YE as YOLO Executor
    participant OE as OCR Executor

    U->>WB: 1. 노드 배치 (드래그 앤 드롭)
    U->>WB: 2. 노드 연결 (화살표)
    U->>WB: 3. 파라미터 설정

    U->>WB: 4. "실행" 클릭
    WB->>GW: 5. POST /api/v1/workflow/execute
    Note over WB,GW: workflow_definition JSON

    GW->>PE: 6. 워크플로우 실행 시작
    PE->>PE: 7. DAG 검증 (순환 참조, 고아 노드)
    PE->>PE: 8. Topological Sort (실행 순서)

    PE->>YE: 9. YOLO 노드 실행
    YE-->>PE: 10. {detections: [...]}

    PE->>PE: 11. 조건 평가 (IF 노드)
    PE->>OE: 12. OCR 노드 실행
    OE-->>PE: 13. {dimensions: [...]}

    PE-->>GW: 14. 실행 완료
    GW-->>WB: 15. 결과 반환
    WB-->>U: 16. 시각화 표시`} />
            </div>

            {/* 조건부 분기 예시 */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.conditionalBranchExample')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {t('guide.conditionalBranchDesc')}
              </p>
              <Mermaid chart={`sequenceDiagram
    participant PE as Pipeline Engine
    participant Y as YOLO Executor
    participant I as IF Executor
    participant E as eDOCr2 Executor
    participant P as PaddleOCR Executor

    PE->>Y: YOLO 실행
    Y-->>PE: {total_detections: 15}

    PE->>I: IF 노드 실행
    I->>I: 조건 평가<br/>detections > 0 ?
    Note over I: TRUE
    I-->>PE: next_branch: "edocr2"

    PE->>E: eDOCr2 실행
    Note over P: PaddleOCR 스킵됨
    E-->>PE: {dimensions: [...]}

    PE-->>PE: 실행 완료`} />
            </div>

            {/* 구현 로드맵 */}
            <div className="bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20 p-4 rounded-lg border border-cyan-200 dark:border-cyan-800">
              <h3 className="font-semibold mb-3 text-cyan-900 dark:text-cyan-100">
                {t('guide.implementationRoadmap')}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-cyan-500">
                  <div className="font-medium text-cyan-900 dark:text-cyan-100">
                    Phase 1: 기반 구조 (1주)
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>• Pipeline Engine 기본 구조</li>
                    <li>• DAG 빌더 & 검증기</li>
                    <li>• ReactFlow 통합</li>
                    <li>• 기본 Canvas 컴포넌트</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-blue-500">
                  <div className="font-medium text-blue-900 dark:text-blue-100">
                    Phase 2: 노드 구현 (1.5주)
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>• 8개 API Executor 구현</li>
                    <li>• IF/Merge/Loop 제어 노드</li>
                    <li>• 노드 UI 컴포넌트 (8개)</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-purple-500">
                  <div className="font-medium text-purple-900 dark:text-purple-100">
                    Phase 3: 데이터 흐름 (1주)
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>• 데이터 매핑 엔진</li>
                    <li>• Topological Sort & 병렬화</li>
                    <li>• 실행 모니터링 (SSE)</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-green-500">
                  <div className="font-medium text-green-900 dark:text-green-100">
                    Phase 4: 워크플로우 관리 (0.5주)
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>• PostgreSQL 스키마</li>
                    <li>• 저장/로드 API</li>
                    <li>• 버전 관리 UI</li>
                  </ul>
                </div>

                <div className="p-3 bg-white dark:bg-gray-900 rounded border-l-4 border-orange-500 md:col-span-2">
                  <div className="font-medium text-orange-900 dark:text-orange-100">
                    Phase 5: 테스트 및 최적화 (1주)
                  </div>
                  <ul className="text-xs mt-1 space-y-1 text-gray-700 dark:text-gray-300">
                    <li>• 단위/통합 테스트 (90% 커버리지)</li>
                    <li>• 성능 최적화 (오버헤드 5% 이내)</li>
                    <li>• 메모리 누수 제거</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* 코드 변경 규모 */}
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2 flex items-center">
                <span className="mr-2">{t('guide.implementationComplexity')}</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium text-yellow-900 dark:text-yellow-100 mb-1">
                    Frontend 변경
                  </div>
                  <ul className="text-xs space-y-1 text-yellow-800 dark:text-yellow-200">
                    <li>• 신규 파일: 10-15개</li>
                    <li>• 추가 코드: ~4,000줄</li>
                    <li>• 의존성: ReactFlow, Zustand</li>
                  </ul>
                </div>
                <div>
                  <div className="font-medium text-yellow-900 dark:text-yellow-100 mb-1">
                    Backend 변경
                  </div>
                  <ul className="text-xs space-y-1 text-yellow-800 dark:text-yellow-200">
                    <li>• 신규 파일: 8-10개</li>
                    <li>• 추가 코드: ~3,500줄</li>
                    <li>• 데이터베이스: PostgreSQL</li>
                  </ul>
                </div>
              </div>
              <div className="mt-3 p-2 bg-yellow-100 dark:bg-yellow-900 rounded">
                <p className="text-xs text-yellow-900 dark:text-yellow-100">
                  <strong>총 개발 공수:</strong> 약 34일 (5주) |
                  <strong> 추가 코드:</strong> 7,500줄 |
                  <strong> ROI:</strong> 하이브리드 대비 절반
                </p>
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
