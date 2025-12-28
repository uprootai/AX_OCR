import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import Mermaid from '../../components/ui/Mermaid';
import ImageZoom from '../../components/ui/ImageZoom';
import {
  BookOpen, Layers, Zap, Code, Database, Server,
  Rocket, FileText, FolderOpen, ChevronRight,
  Menu, X, Wrench, TestTube2, Terminal
} from 'lucide-react';

// 섹션 정의
const sections = [
  { id: 'overview', label: '프로젝트 개요', icon: BookOpen },
  { id: 'architecture', label: '시스템 아키텍처', icon: Layers },
  { id: 'pipeline', label: 'BlueprintFlow 파이프라인', icon: Code },
  { id: 'services', label: '서비스 역할', icon: Server },
  { id: 'quickstart', label: '빠른 시작', icon: Rocket },
  { id: 'apidev', label: 'API 개발 가이드', icon: Wrench },
  { id: 'specref', label: '스펙 레퍼런스', icon: Terminal },
  { id: 'testing', label: '테스트 가이드', icon: TestTube2 },
  { id: 'docs', label: '문서 가이드', icon: FileText },
  { id: 'blueprintflow', label: 'BlueprintFlow 상세', icon: FolderOpen },
];

export default function Guide() {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sectionRefs = useRef<{ [key: string]: HTMLElement | null }>({});

  // 스크롤 시 현재 섹션 감지
  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 100;

      for (const section of sections) {
        const element = sectionRefs.current[section.id];
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 섹션으로 스크롤
  const scrollToSection = (sectionId: string) => {
    const element = sectionRefs.current[sectionId];
    if (element) {
      const yOffset = -80;
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
      setActiveSection(sectionId);
      setSidebarOpen(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* 모바일 메뉴 버튼 */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-20 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700"
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* 서브사이드바 */}
      <aside className={`
        fixed lg:sticky top-16 left-0 h-[calc(100vh-4rem)] w-64
        bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700
        transform transition-transform duration-300 ease-in-out z-40
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        overflow-y-auto
      `}>
        <div className="p-4">
          <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
            목차
          </h2>
          <nav className="space-y-1">
            {sections.map((section) => {
              const Icon = section.icon;
              const isActive = activeSection === section.id;
              return (
                <button
                  key={section.id}
                  onClick={() => scrollToSection(section.id)}
                  className={`
                    w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors
                    ${isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }
                  `}
                >
                  <Icon className={`w-4 h-4 mr-3 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
                  <span className="truncate">{section.label}</span>
                  {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
                </button>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* 오버레이 (모바일) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* 메인 콘텐츠 */}
      <main className="flex-1 lg:ml-0 min-w-0">
        <div className="container mx-auto px-4 py-8 max-w-5xl">
          {/* 헤더 */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              {t('guide.title')}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {t('guide.subtitle')}
            </p>
          </div>

          {/* Section 1: 프로젝트 개요 */}
          <section
            id="overview"
            ref={(el) => { sectionRefs.current['overview'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card>
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
                        <h3 className="font-semibold text-blue-900 dark:text-blue-100">{t('guide.coreStrength')}</h3>
                      </div>
                      <ul className="text-sm space-y-1 text-blue-800 dark:text-blue-200">
                        <li>• <strong>{t('guide.coreStr1')}</strong></li>
                        <li>• {t('guide.coreStr2')}</li>
                        <li>• {t('guide.coreStr3')}</li>
                      </ul>
                    </div>

                    <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                      <div className="flex items-center mb-2">
                        <Database className="w-5 h-5 mr-2 text-green-600 dark:text-green-400" />
                        <h3 className="font-semibold text-green-900 dark:text-green-100">{t('guide.flexibleAPIs')}</h3>
                      </div>
                      <ul className="text-sm space-y-1 text-green-800 dark:text-green-200">
                        <li>• {t('guide.flexApi1')}</li>
                        <li>• {t('guide.flexApi2')}</li>
                        <li>• {t('guide.flexApi3')}</li>
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
          </section>

          {/* Section 2: 시스템 아키텍처 */}
          <section
            id="architecture"
            ref={(el) => { sectionRefs.current['architecture'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card>
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
        LD[LineDetector :5016]
    end

    subgraph Preprocessing["🔧 Preprocessing"]
        ES[ESRGAN :5010]
    end

    subgraph Analysis["📊 Analysis"]
        SK[SkinModel :5003]
        PA[PID-Analyzer :5018]
        DC[DesignChecker :5019]
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
          </section>

          {/* Section 3: BlueprintFlow 파이프라인 */}
          <section
            id="pipeline"
            ref={(el) => { sectionRefs.current['pipeline'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Code className="w-5 h-5 mr-2" />
                  {t('guide.blueprintflowPipeline')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                      {t('guide.workflowPipeline')}
                    </h3>
                    <ImageZoom>
                      <Mermaid chart={`sequenceDiagram
    participant User as 사용자
    participant Dashboard as Dashboard
    participant Builder as BlueprintFlow Builder
    participant Gateway as Gateway API
    participant APIs as 다양한 APIs

    User->>Dashboard: 1. 새 API 추가 (URL 입력)
    Dashboard->>Dashboard: 2. /api/v1/info 자동 검색
    Dashboard-->>User: 3. Custom API로 등록

    User->>Builder: 4. 워크플로우 설계
    Builder->>Builder: 5. 노드 배치 & 연결
    Builder-->>User: 6. 실시간 미리보기

    User->>Builder: 7. 실행 버튼 클릭
    Builder->>Gateway: 8. workflow JSON 전송
    Gateway->>APIs: 9. 병렬/순차 실행
    APIs-->>Gateway: 10. 결과 수집
    Gateway-->>Builder: 11. 통합 결과
    Builder-->>User: 12. 시각화 표시`} />
                    </ImageZoom>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 4: 서비스 역할 */}
          <section
            id="services"
            ref={(el) => { sectionRefs.current['services'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card>
              <CardHeader>
                <CardTitle>{t('guide.serviceRoles')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Gateway */}
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

                  {/* Detection */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-sm">🎯 Detection</span>
                      <span className="text-sm text-muted-foreground">(2개 엔진)</span>
                    </h3>
                    <div className="grid md:grid-cols-2 gap-3">
                      <div className="p-4 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20">
                        <h4 className="font-bold text-blue-900 dark:text-blue-100 mb-2">YOLOv11 API (포트 5005)</h4>
                        <p className="text-sm text-blue-800 dark:text-blue-200 mb-2">공학 도면에서 14개 클래스 객체 검출</p>
                        <ul className="text-xs space-y-1 text-blue-700 dark:text-blue-300">
                          <li><strong>• 검출 대상:</strong> 치수선, 화살표, 텍스트, GD&T 심볼 등</li>
                          <li><strong>• 특징:</strong> 합성 데이터로 학습, CPU/GPU 지원</li>
                        </ul>
                      </div>
                      <div className="p-4 border-l-4 border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-bold text-emerald-900 dark:text-emerald-100">YOLO P&ID 모드</h4>
                          <Badge className="bg-emerald-600 text-xs">model_type</Badge>
                        </div>
                        <p className="text-sm text-emerald-800 dark:text-emerald-200 mb-2">YOLO에서 model_type=pid_class_aware로 P&ID 심볼 검출</p>
                        <ul className="text-xs space-y-1 text-emerald-700 dark:text-emerald-300">
                          <li><strong>• 검출 대상:</strong> 밸브 15종, 펌프 5종, 계기 20종 등</li>
                          <li><strong>• 설정:</strong> model_type: pid_class_aware/pid_class_agnostic</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* OCR */}
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

                  {/* Segmentation */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                      <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-sm">🎨 Segmentation</span>
                      <span className="text-sm text-muted-foreground">(2개 엔진)</span>
                    </h3>
                    <div className="grid md:grid-cols-2 gap-3">
                      <div className="p-4 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20">
                        <h4 className="font-bold text-purple-900 dark:text-purple-100 mb-2">EDGNet API (포트 5012)</h4>
                        <p className="text-sm text-purple-800 dark:text-purple-200 mb-2">도면 세그멘테이션 (레이어 분리)</p>
                        <ul className="text-xs space-y-1 text-purple-700 dark:text-purple-300">
                          <li><strong>• 모델:</strong> UNet (엣지), GraphSAGE (분류)</li>
                          <li><strong>• 특징:</strong> 윤곽선, 텍스트, 치수 레이어 분리</li>
                        </ul>
                      </div>
                      <div className="p-4 border-l-4 border-teal-500 bg-teal-50 dark:bg-teal-900/20">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-bold text-teal-900 dark:text-teal-100">Line Detector (포트 5016)</h4>
                          <Badge className="bg-teal-600 text-xs">P&ID</Badge>
                        </div>
                        <p className="text-sm text-teal-800 dark:text-teal-200 mb-2">P&ID 배관 라인 및 신호선 검출</p>
                        <ul className="text-xs space-y-1 text-teal-700 dark:text-teal-300">
                          <li><strong>• 알고리즘:</strong> LSD + Hough Transform</li>
                          <li><strong>• 특징:</strong> 라인 분류, 교차점 검출, 병합</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* P&ID Analysis Pipeline */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                      <span className="px-2 py-1 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded text-sm">📊 P&ID Analysis</span>
                      <Badge className="bg-rose-600 text-xs">NEW</Badge>
                    </h3>
                    <div className="grid md:grid-cols-2 gap-3">
                      <div className="p-4 border-l-4 border-violet-500 bg-violet-50 dark:bg-violet-900/20">
                        <h4 className="font-bold text-violet-900 dark:text-violet-100 mb-2">P&ID Analyzer (포트 5018)</h4>
                        <p className="text-sm text-violet-800 dark:text-violet-200 mb-2">심볼 연결 분석 및 BOM 생성</p>
                        <ul className="text-xs space-y-1 text-violet-700 dark:text-violet-300">
                          <li><strong>• 출력:</strong> BOM, 밸브 시그널 리스트, 장비 목록</li>
                          <li><strong>• 특징:</strong> 그래프 기반 연결성 분석</li>
                        </ul>
                      </div>
                      <div className="p-4 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20">
                        <h4 className="font-bold text-red-900 dark:text-red-100 mb-2">Design Checker (포트 5019)</h4>
                        <p className="text-sm text-red-800 dark:text-red-200 mb-2">설계 규칙 검증 및 오류 검출</p>
                        <ul className="text-xs space-y-1 text-red-700 dark:text-red-300">
                          <li><strong>• 규칙:</strong> 20+ 설계 규칙 (6개 카테고리)</li>
                          <li><strong>• 표준:</strong> ISO 10628, ISA 5.1, ASME</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Other Services (collapsed) */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="p-4 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
                      <h4 className="font-bold text-yellow-900 dark:text-yellow-100 mb-1">🔧 ESRGAN (5010)</h4>
                      <p className="text-xs text-yellow-700 dark:text-yellow-300">2x/4x 업스케일링, 노이즈 제거</p>
                    </div>
                    <div className="p-4 border-l-4 border-pink-500 bg-pink-50 dark:bg-pink-900/20">
                      <h4 className="font-bold text-pink-900 dark:text-pink-100 mb-1">📊 SkinModel (5003)</h4>
                      <p className="text-xs text-pink-700 dark:text-pink-300">공차 예측 및 제조 가능성 분석</p>
                    </div>
                    <div className="p-4 border-l-4 border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-bold text-indigo-900 dark:text-indigo-100">🤖 VL (5004)</h4>
                        <Badge className="bg-indigo-600 text-xs">멀티모달</Badge>
                      </div>
                      <p className="text-xs text-indigo-700 dark:text-indigo-300">Vision-Language, BLIP/Claude/GPT-4V</p>
                    </div>
                    <div className="p-4 border-l-4 border-violet-500 bg-violet-50 dark:bg-violet-900/20">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-bold text-violet-900 dark:text-violet-100">🧠 Knowledge (5007)</h4>
                        <Badge className="bg-violet-600 text-xs">GraphRAG</Badge>
                      </div>
                      <p className="text-xs text-violet-700 dark:text-violet-300">Neo4j + GraphRAG 도메인 지식 엔진</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 5: 빠른 시작 */}
          <section
            id="quickstart"
            ref={(el) => { sectionRefs.current['quickstart'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card>
              <CardHeader>
                <CardTitle>{t('guide.quickStartGuide')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2 flex items-center text-green-900 dark:text-green-100">
                      <span className="text-xl mr-2">🚀</span>
                      1️⃣ BlueprintFlow로 워크플로우 빌드 (권장)
                    </h3>
                    <ol className="space-y-2 text-sm ml-4">
                      <li className="flex items-start">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">1</span>
                        <span><a href="/blueprintflow/builder" className="text-green-600 hover:underline font-medium">BlueprintFlow Builder</a>로 이동</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">2</span>
                        <span>좌측 팔레트에서 원하는 API 노드를 드래그하여 캔버스에 배치</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">3</span>
                        <span>노드 간 연결선을 드래그하여 워크플로우 구성</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">4</span>
                        <span>각 노드 클릭 → 우측 패널에서 파라미터 조정</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">5</span>
                        <span>"실행" 버튼 클릭 → 실시간 결과 확인</span>
                      </li>
                    </ol>
                  </div>

                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-2 flex items-center text-cyan-900 dark:text-cyan-100">
                      <span className="text-xl mr-2">➕</span>
                      2️⃣ 새로운 API 추가하기 (Custom API)
                    </h3>
                    <ol className="space-y-2 text-sm ml-4">
                      <li className="flex items-start">
                        <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">1</span>
                        <span><a href="/dashboard" className="text-cyan-600 hover:underline font-medium">Dashboard</a>에서 우측 상단 <strong>"API 추가"</strong> 버튼 클릭</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">2</span>
                        <span>API URL 입력 (예: <code>http://localhost:5007</code>) → <strong>"자동 검색"</strong> 클릭</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">3</span>
                        <span>API 정보가 자동으로 채워짐 (아이콘, 색상, 카테고리 등)</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">4</span>
                        <span>저장하면 <strong>즉시 반영</strong>: Dashboard, Settings, BlueprintFlow 노드</span>
                      </li>
                      <li className="flex items-start">
                        <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">5</span>
                        <span>테스트 후 <strong>"내보내기"</strong> 버튼으로 Built-in API로 전환 가능</span>
                      </li>
                    </ol>
                    <div className="mt-3 p-3 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded">
                      <p className="text-xs text-cyan-800 dark:text-cyan-200">
                        💡 <strong>핵심 가치:</strong> 어떤 OCR 엔진이든, 어떤 Detection 모델이든 URL만 있으면 바로 BlueprintFlow에서 다양한 조합으로 테스트할 수 있습니다!
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">💡 팁</h4>
                    <ul className="text-sm space-y-1 text-yellow-800 dark:text-yellow-200">
                      <li>• 첫 번째 API 호출은 모델 로딩으로 인해 느릴 수 있습니다 (이후 빠름)</li>
                      <li>• <a href="/blueprintflow/templates" className="underline">템플릿</a>을 사용하면 검증된 워크플로우로 빠르게 시작할 수 있습니다</li>
                      <li>• API는 <code>/api/v1/info</code> 엔드포인트를 제공하면 자동 검색됩니다</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 6: API 개발 가이드 */}
          <section
            id="apidev"
            ref={(el) => { sectionRefs.current['apidev'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card className="border-2 border-indigo-300 dark:border-indigo-700">
              <CardHeader className="bg-indigo-50 dark:bg-indigo-900/20">
                <CardTitle className="flex items-center text-indigo-900 dark:text-indigo-100">
                  <Wrench className="w-5 h-5 mr-2" />
                  API 개발 가이드
                  <Badge className="ml-3 bg-indigo-600">개발자용</Badge>
                </CardTitle>
                <p className="text-sm text-indigo-800 dark:text-indigo-200 mt-2">
                  Custom API → Built-in API 단일 통합 워크플로우
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* 핵심 원칙 */}
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded">
                    <h4 className="font-bold text-amber-900 dark:text-amber-100 mb-2">⚠️ 핵심 원칙: "하나의 플로우, 하나의 경로"</h4>
                    <p className="text-sm text-amber-800 dark:text-amber-200">
                      Custom API와 Built-in API는 <strong>별개의 옵션이 아닙니다</strong>. 모든 API는 동일한 경로를 거쳐 프로덕션화됩니다.
                    </p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-amber-700 dark:text-amber-300">
                      <code className="bg-amber-100 dark:bg-amber-900 px-2 py-1 rounded">Custom API = 테스트/검증 단계</code>
                      <span>→</span>
                      <code className="bg-amber-100 dark:bg-amber-900 px-2 py-1 rounded">Built-in API = 프로덕션 단계</code>
                    </div>
                  </div>

                  {/* 5단계 프로세스 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">📋 5단계 통합 프로세스</h3>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded text-center">
                        <div className="text-2xl mb-1">1️⃣</div>
                        <div className="text-sm font-medium text-blue-900 dark:text-blue-100">API 서버 구현</div>
                        <div className="text-xs text-blue-700 dark:text-blue-300">/api/v1/info 필수!</div>
                      </div>
                      <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded text-center">
                        <div className="text-2xl mb-1">2️⃣</div>
                        <div className="text-sm font-medium text-green-900 dark:text-green-100">Docker 실행</div>
                        <div className="text-xs text-green-700 dark:text-green-300">docker-compose up</div>
                      </div>
                      <div className="p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded text-center">
                        <div className="text-2xl mb-1">3️⃣</div>
                        <div className="text-sm font-medium text-purple-900 dark:text-purple-100">Dashboard 등록</div>
                        <div className="text-xs text-purple-700 dark:text-purple-300">URL 입력 → 자동 검색</div>
                      </div>
                      <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded text-center">
                        <div className="text-2xl mb-1">4️⃣</div>
                        <div className="text-sm font-medium text-orange-900 dark:text-orange-100">내보내기</div>
                        <div className="text-xs text-orange-700 dark:text-orange-300">코드 자동 생성</div>
                      </div>
                      <div className="p-3 bg-pink-50 dark:bg-pink-900/20 border border-pink-200 dark:border-pink-800 rounded text-center">
                        <div className="text-2xl mb-1">5️⃣</div>
                        <div className="text-sm font-medium text-pink-900 dark:text-pink-100">프로덕션 완료</div>
                        <div className="text-xs text-pink-700 dark:text-pink-300">Custom API OFF</div>
                      </div>
                    </div>
                  </div>

                  {/* 필수 엔드포인트 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">🔌 필수 엔드포인트</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                        <code className="text-sm font-mono text-green-600 dark:text-green-400">GET /health</code>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">기본 헬스체크</p>
                      </div>
                      <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                        <code className="text-sm font-mono text-green-600 dark:text-green-400">GET /api/v1/health</code>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">API 버전 헬스체크</p>
                      </div>
                      <div className="p-3 bg-indigo-50 dark:bg-indigo-900/30 rounded border border-indigo-300 dark:border-indigo-700">
                        <code className="text-sm font-mono text-indigo-600 dark:text-indigo-400">GET /api/v1/info</code>
                        <Badge className="ml-2 bg-indigo-600 text-xs">필수</Badge>
                        <p className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">자동 검색용 메타데이터</p>
                      </div>
                      <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                        <code className="text-sm font-mono text-green-600 dark:text-green-400">POST /api/v1/process</code>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">실제 처리 로직</p>
                      </div>
                    </div>
                  </div>

                  {/* /api/v1/info 응답 예시 */}
                  <div className="bg-gray-900 dark:bg-gray-950 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-400">GET /api/v1/info 응답 예시</span>
                      <span className="text-xs text-green-400">JSON</span>
                    </div>
                    <pre className="text-xs text-green-400 overflow-x-auto"><code>{`{
  "id": "myapi",
  "name": "MyAPI",
  "version": "1.0.0",
  "category": "ocr",
  "description": "My Custom API",
  "icon": "ScanText",
  "color": "#8b5cf6",
  "parameters": [
    { "name": "visualize", "type": "boolean", "default": true }
  ]
}`}</code></pre>
                  </div>

                  {/* 내보내기 기능 */}
                  <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded-lg">
                    <h4 className="font-semibold text-cyan-900 dark:text-cyan-100 mb-2 flex items-center">
                      <span className="mr-2">📤</span> 내보내기 버튼 → 자동 생성 코드
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                        <div className="font-medium text-cyan-800 dark:text-cyan-200">YAML 스펙</div>
                        <code className="text-cyan-600 dark:text-cyan-400">api_specs/{'{id}'}.yaml</code>
                      </div>
                      <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                        <div className="font-medium text-cyan-800 dark:text-cyan-200">노드 정의</div>
                        <code className="text-cyan-600 dark:text-cyan-400">nodeDefinitions.ts</code>
                      </div>
                      <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                        <div className="font-medium text-cyan-800 dark:text-cyan-200">Docker</div>
                        <code className="text-cyan-600 dark:text-cyan-400">docker-compose.yml</code>
                      </div>
                      <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                        <div className="font-medium text-cyan-800 dark:text-cyan-200">테스트</div>
                        <code className="text-cyan-600 dark:text-cyan-400">test_{'{id}'}.py</code>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 7: 스펙 레퍼런스 */}
          <section
            id="specref"
            ref={(el) => { sectionRefs.current['specref'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card className="border-2 border-emerald-300 dark:border-emerald-700">
              <CardHeader className="bg-emerald-50 dark:bg-emerald-900/20">
                <CardTitle className="flex items-center text-emerald-900 dark:text-emerald-100">
                  <Terminal className="w-5 h-5 mr-2" />
                  API 스펙 YAML 레퍼런스
                  <Badge className="ml-3 bg-emerald-600">v1</Badge>
                </CardTitle>
                <p className="text-sm text-emerald-800 dark:text-emerald-200 mt-2">
                  gateway-api/api_specs/*.yaml 파일 작성 가이드
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* YAML 구조 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">📄 YAML 스펙 구조</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      {[
                        { field: 'apiVersion', desc: 'v1 고정', color: 'blue' },
                        { field: 'kind', desc: 'APISpec 고정', color: 'blue' },
                        { field: 'metadata', desc: 'id, name, host, port', color: 'green' },
                        { field: 'server', desc: 'endpoint, method, timeout', color: 'green' },
                        { field: 'blueprintflow', desc: 'category, color, icon', color: 'purple' },
                        { field: 'inputs', desc: '입력 정의', color: 'orange' },
                        { field: 'outputs', desc: '출력 정의', color: 'orange' },
                        { field: 'parameters', desc: '파라미터 정의', color: 'pink' },
                      ].map((item) => (
                        <div key={item.field} className={`p-2 bg-${item.color}-50 dark:bg-${item.color}-900/20 rounded border border-${item.color}-200 dark:border-${item.color}-800`}>
                          <code className="text-xs font-mono">{item.field}</code>
                          <p className="text-xs text-gray-600 dark:text-gray-400">{item.desc}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 카테고리 목록 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">🏷️ 사용 가능한 카테고리</h3>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { cat: 'input', color: 'blue', desc: '입력 노드' },
                        { cat: 'detection', color: 'cyan', desc: '객체 검출' },
                        { cat: 'ocr', color: 'green', desc: '텍스트 인식' },
                        { cat: 'segmentation', color: 'purple', desc: '세그멘테이션' },
                        { cat: 'preprocessing', color: 'yellow', desc: '전처리' },
                        { cat: 'analysis', color: 'pink', desc: '분석' },
                        { cat: 'knowledge', color: 'violet', desc: '지식 엔진' },
                        { cat: 'ai', color: 'indigo', desc: 'AI/LLM' },
                        { cat: 'control', color: 'gray', desc: '제어 노드' },
                      ].map((item) => (
                        <span key={item.cat} className={`px-3 py-1 text-xs rounded-full bg-${item.color}-100 dark:bg-${item.color}-900/30 text-${item.color}-800 dark:text-${item.color}-200 border border-${item.color}-300 dark:border-${item.color}-700`}>
                          <strong>{item.cat}</strong> - {item.desc}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* 아이콘 목록 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">🎨 사용 가능한 아이콘</h3>
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded text-xs">
                      <code className="text-gray-700 dark:text-gray-300">
                        Image, Box, ScanText, Layers, Sparkles, FileText, Brain, Zap, GitBranch, RefreshCw, Merge, Eye, Server, Database, Search, Settings, Upload, Download, Play, Pause
                      </code>
                    </div>
                  </div>

                  {/* 파라미터 타입 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">⚙️ 파라미터 타입</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {[
                        { type: 'string', ui: 'text, select, textarea', example: '"default"' },
                        { type: 'number', ui: 'number, slider', example: '0.5' },
                        { type: 'integer', ui: 'number', example: '10' },
                        { type: 'boolean', ui: 'checkbox, switch', example: 'true' },
                      ].map((item) => (
                        <div key={item.type} className="p-2 bg-gray-50 dark:bg-gray-800 rounded border">
                          <code className="text-sm font-bold text-purple-600 dark:text-purple-400">{item.type}</code>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">UI: {item.ui}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">예: {item.example}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* YAML 예시 */}
                  <div className="bg-gray-900 dark:bg-gray-950 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-400">api_specs/myapi.yaml 예시</span>
                      <span className="text-xs text-yellow-400">YAML</span>
                    </div>
                    <pre className="text-xs text-green-400 overflow-x-auto"><code>{`apiVersion: v1
kind: APISpec

metadata:
  id: myapi
  name: MyAPI
  version: 1.0.0
  host: myapi-api      # Docker 서비스명
  port: 5020

server:
  endpoint: /api/v1/process
  method: POST
  contentType: multipart/form-data

blueprintflow:
  category: ocr
  color: "#8b5cf6"
  icon: ScanText
  requiresImage: true

parameters:
  - name: visualize
    type: boolean
    default: true
    description: 시각화 활성화
    uiType: checkbox`}</code></pre>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 8: 테스트 가이드 */}
          <section
            id="testing"
            ref={(el) => { sectionRefs.current['testing'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card className="border-2 border-rose-300 dark:border-rose-700">
              <CardHeader className="bg-rose-50 dark:bg-rose-900/20">
                <CardTitle className="flex items-center text-rose-900 dark:text-rose-100">
                  <TestTube2 className="w-5 h-5 mr-2" />
                  API 검증 테스트 가이드
                  <Badge className="ml-3 bg-rose-600">QA</Badge>
                </CardTitle>
                <p className="text-sm text-rose-800 dark:text-rose-200 mt-2">
                  Custom API 테스트 → Built-in 전환 전 검증 체크리스트
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* 테스트 단계 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">🧪 3단계 테스트 프로세스</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <h4 className="font-bold text-blue-900 dark:text-blue-100 mb-2">Phase 1: API 서버 테스트</h4>
                        <ul className="text-xs space-y-1 text-blue-800 dark:text-blue-200">
                          <li>✓ /health 엔드포인트 응답</li>
                          <li>✓ /api/v1/info 메타데이터 반환</li>
                          <li>✓ /api/v1/process 기본 처리</li>
                          <li>✓ 에러 케이스 핸들링</li>
                        </ul>
                      </div>
                      <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                        <h4 className="font-bold text-green-900 dark:text-green-100 mb-2">Phase 2: UI 통합 테스트</h4>
                        <ul className="text-xs space-y-1 text-green-800 dark:text-green-200">
                          <li>✓ Dashboard에서 API 검색됨</li>
                          <li>✓ BlueprintFlow 노드 표시됨</li>
                          <li>✓ 파라미터 UI 정상 작동</li>
                          <li>✓ 워크플로우 실행 성공</li>
                        </ul>
                      </div>
                      <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                        <h4 className="font-bold text-purple-900 dark:text-purple-100 mb-2">Phase 3: 프로덕션 검증</h4>
                        <ul className="text-xs space-y-1 text-purple-800 dark:text-purple-200">
                          <li>✓ YAML 스펙 유효성 검사</li>
                          <li>✓ pytest 테스트 통과</li>
                          <li>✓ Custom/Built-in 전환 확인</li>
                          <li>✓ 기존 워크플로우 호환성</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* curl 테스트 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">💻 Bash 테스트 명령어</h3>
                    <div className="space-y-3">
                      <div className="bg-gray-900 dark:bg-gray-950 p-3 rounded-lg">
                        <div className="text-xs text-gray-400 mb-1"># 1. 헬스체크</div>
                        <code className="text-xs text-green-400">curl http://localhost:5020/health</code>
                      </div>
                      <div className="bg-gray-900 dark:bg-gray-950 p-3 rounded-lg">
                        <div className="text-xs text-gray-400 mb-1"># 2. API 정보 확인</div>
                        <code className="text-xs text-green-400">curl http://localhost:5020/api/v1/info | jq</code>
                      </div>
                      <div className="bg-gray-900 dark:bg-gray-950 p-3 rounded-lg">
                        <div className="text-xs text-gray-400 mb-1"># 3. 이미지 처리 테스트</div>
                        <code className="text-xs text-green-400">curl -X POST http://localhost:5020/api/v1/process \<br/>  -F "file=@test.jpg" -F "visualize=true"</code>
                      </div>
                    </div>
                  </div>

                  {/* pytest 테스트 */}
                  <div>
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">🐍 pytest 자동화 테스트</h3>
                    <div className="bg-gray-900 dark:bg-gray-950 p-4 rounded-lg">
                      <div className="text-xs text-gray-400 mb-2"># gateway-api/tests/test_myapi.py</div>
                      <pre className="text-xs text-green-400 overflow-x-auto"><code>{`import pytest
import httpx

API_URL = "http://localhost:5020"

def test_health():
    r = httpx.get(f"{API_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_info():
    r = httpx.get(f"{API_URL}/api/v1/info")
    assert r.status_code == 200
    info = r.json()
    assert "id" in info
    assert "category" in info

def test_process():
    with open("test.jpg", "rb") as f:
        r = httpx.post(
            f"{API_URL}/api/v1/process",
            files={"file": f}
        )
    assert r.status_code == 200
    assert r.json()["success"] is True`}</code></pre>
                    </div>
                    <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                      <code>cd gateway-api && pytest tests/test_myapi.py -v</code>
                    </div>
                  </div>

                  {/* 체크리스트 */}
                  <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-3">✅ Built-in 전환 전 최종 체크리스트</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <h5 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">API 서버</h5>
                        <ul className="space-y-1 text-yellow-700 dark:text-yellow-300 text-xs">
                          <li>□ 모든 엔드포인트 정상 응답</li>
                          <li>□ 에러 케이스 처리 완료</li>
                          <li>□ 오버레이 이미지 생성됨</li>
                          <li>□ 타임아웃 없음 (60초 이내)</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">BlueprintFlow 통합</h5>
                        <ul className="space-y-1 text-yellow-700 dark:text-yellow-300 text-xs">
                          <li>□ 노드 팔레트에 표시됨</li>
                          <li>□ 다른 노드와 연결 가능</li>
                          <li>□ 병렬 실행 시 정상 작동</li>
                          <li>□ 결과 데이터 형식 올바름</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 9: 문서 가이드 */}
          <section
            id="docs"
            ref={(el) => { sectionRefs.current['docs'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card>
              <CardHeader>
                <CardTitle>{t('guide.documentation')}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {t('guide.docDescription')}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center">
                      <span className="mr-2">📖</span> 사용자 가이드
                    </h3>
                    <ul className="text-sm space-y-1 text-blue-800 dark:text-blue-200">
                      <li>• INSTALLATION_GUIDE.md</li>
                      <li>• TROUBLESHOOTING.md</li>
                      <li>• ADMIN_MANUAL.md</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2 flex items-center">
                      <span className="mr-2">👨‍💻</span> 개발자 가이드
                    </h3>
                    <ul className="text-sm space-y-1 text-green-800 dark:text-green-200">
                      <li>• API_SPEC_SYSTEM_GUIDE.md</li>
                      <li>• DYNAMIC_API_SYSTEM_GUIDE.md</li>
                      <li>• BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-2 flex items-center">
                      <span className="mr-2">🔮</span> BlueprintFlow
                    </h3>
                    <ul className="text-sm space-y-1 text-purple-800 dark:text-purple-200">
                      <li>• BlueprintFlow 개요</li>
                      <li>• 아키텍처 설계</li>
                      <li>• VL + TextInput 통합</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                    <h3 className="font-semibold text-orange-900 dark:text-orange-100 mb-2 flex items-center">
                      <span className="mr-2">⚙️</span> 기술 구현
                    </h3>
                    <ul className="text-sm space-y-1 text-orange-800 dark:text-orange-200">
                      <li>• YOLO 빠른 시작</li>
                      <li>• eDOCr v1/v2 배포</li>
                      <li>• 합성 데이터 전략</li>
                    </ul>
                  </div>
                </div>

                <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    <strong>📚 전체 문서 보기:</strong>{' '}
                    <a href="/docs" className="text-blue-600 hover:underline">/docs 페이지</a>에서 모든 문서를 검색하고 읽을 수 있습니다.
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 7: BlueprintFlow 상세 */}
          <section
            id="blueprintflow"
            ref={(el) => { sectionRefs.current['blueprintflow'] = el; }}
            className="mb-12 scroll-mt-20"
          >
            <Card className="border-4 border-green-500">
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
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 rounded text-center">
                      <div className="text-3xl font-bold text-green-600 dark:text-green-400">17</div>
                      <div className="text-sm text-green-800 dark:text-green-200">노드 타입</div>
                    </div>
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded text-center">
                      <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">15</div>
                      <div className="text-sm text-blue-800 dark:text-blue-200">API Executor</div>
                    </div>
                    <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border-l-4 border-purple-500 rounded text-center">
                      <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">60%</div>
                      <div className="text-sm text-purple-800 dark:text-purple-200">속도 향상</div>
                    </div>
                    <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border-l-4 border-cyan-500 rounded text-center">
                      <div className="text-3xl font-bold text-cyan-600 dark:text-cyan-400">4</div>
                      <div className="text-sm text-cyan-800 dark:text-cyan-200">템플릿</div>
                    </div>
                  </div>

                  {/* 노드 타입 */}
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                    <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">지원 노드 타입 (17종)</h3>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
                        <strong>입력 노드</strong>
                        <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                          <li>• ImageInput</li>
                          <li>• TextInput</li>
                        </ul>
                      </div>
                      <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded">
                        <strong>핵심 API</strong>
                        <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                          <li>• YOLO, eDOCr2</li>
                          <li>• PaddleOCR, EDGNet</li>
                          <li>• SkinModel, VL</li>
                        </ul>
                      </div>
                      <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded">
                        <strong>확장 API</strong>
                        <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                          <li>• TrOCR, ESRGAN</li>
                          <li>• OCR Ensemble</li>
                          <li>• Knowledge</li>
                        </ul>
                      </div>
                      <div className="p-2 bg-rose-100 dark:bg-rose-900/30 rounded">
                        <strong>P&ID 분석</strong>
                        <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                          <li>• YOLO (P&ID 모드), LineDetector</li>
                          <li>• PID Analyzer</li>
                          <li>• Design Checker</li>
                        </ul>
                      </div>
                      <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded">
                        <strong>제어 노드</strong>
                        <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                          <li>• IF (조건 분기)</li>
                          <li>• Loop, Merge</li>
                        </ul>
                      </div>
                    </div>
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

    NP --> RF
    RF --> PP

    style Center fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Left fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Right fill:#e8f5e9,stroke:#388e3c,stroke-width:2px`} />
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

                  {/* 참고 문서 */}
                  <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded-lg">
                    <h4 className="font-semibold text-cyan-900 dark:text-cyan-100 mb-2 flex items-center">
                      <span className="mr-2">{t('guide.detailedDesignDocs')}</span>
                    </h4>
                    <ul className="text-sm space-y-2 text-cyan-800 dark:text-cyan-200">
                      <li>• <strong>완전한 설계서:</strong> <code className="bg-cyan-100 dark:bg-cyan-900 px-2 py-1 rounded text-xs">docs/BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md</code></li>
                      <li>• <strong>API 통합 가이드:</strong> <code className="bg-cyan-100 dark:bg-cyan-900 px-2 py-1 rounded text-xs">docs/BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md</code></li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

        </div>
      </main>
    </div>
  );
}
