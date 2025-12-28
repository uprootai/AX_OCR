/**
 * GuidePage - Blueprint AI BOM 사용 가이드
 *
 * 노드 관계, 설정 시나리오, 워크플로우 가이드 제공
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Zap,
  Settings,
  GitBranch,
  CheckCircle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  Ruler,
  Eye,
  Upload,
  Search,
  Edit3,
  Download,
  AlertTriangle,
  Info,
  Home,
} from 'lucide-react';

// 시나리오 타입 정의
interface Scenario {
  id: string;
  title: string;
  icon: string;
  description: string;
  preset: string;
  settings: {
    symbol_detection: boolean;
    dimension_ocr: boolean;
    line_detection: boolean;
    confidence: number;
  };
  workflow: string[];
  tips: string[];
}

// 워크플로우 단계
interface WorkflowStep {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  details: string[];
}

export function GuidePage() {
  const [expandedScenario, setExpandedScenario] = useState<string | null>('electrical');
  const [activeTab, setActiveTab] = useState<'overview' | 'workflow' | 'scenarios' | 'settings'>('overview');

  // 워크플로우 단계 정의
  const workflowSteps: WorkflowStep[] = [
    {
      id: 1,
      title: '도면 업로드',
      description: '분석할 도면 이미지를 업로드합니다',
      icon: <Upload className="w-6 h-6" />,
      details: [
        '지원 형식: PNG, JPG, JPEG, PDF',
        '권장 해상도: 2000x2000 이상',
        '최대 파일 크기: 50MB',
        '세션 ID가 자동 생성됩니다',
      ],
    },
    {
      id: 2,
      title: 'AI 검출',
      description: 'YOLO 모델이 심볼을 자동 검출합니다',
      icon: <Search className="w-6 h-6" />,
      details: [
        '27개 전장 부품 클래스 검출',
        'GPU 사용 시 2-3초, CPU 시 8-10초',
        '신뢰도 0.4 이상 결과만 표시',
        '바운딩 박스와 클래스명 제공',
      ],
    },
    {
      id: 3,
      title: 'Human-in-the-Loop 검증',
      description: '검출 결과를 확인하고 수정합니다',
      icon: <Edit3 className="w-6 h-6" />,
      details: [
        '우선순위 기반 검증 큐 제공',
        '승인/거부/수정 3가지 액션',
        '바운딩 박스 직접 수정 가능',
        '일괄 승인 및 자동 승인 지원',
      ],
    },
    {
      id: 4,
      title: 'BOM 생성',
      description: '검증된 결과로 BOM을 생성합니다',
      icon: <FileSpreadsheet className="w-6 h-6" />,
      details: [
        '승인된 심볼만 BOM에 포함',
        '동일 심볼은 수량으로 합산',
        '가격 정보 자동 매칭',
        'Excel/CSV/JSON/PDF 내보내기',
      ],
    },
  ];

  // 시나리오 정의
  const scenarios: Scenario[] = [
    {
      id: 'electrical',
      title: '전력 설비 단선도',
      icon: '⚡',
      description: 'MCP Panel, 배전반, 변전소 도면 등 전력 설비 심볼 검출에 최적화',
      preset: 'electrical',
      settings: {
        symbol_detection: true,
        dimension_ocr: false,
        line_detection: false,
        confidence: 0.4,
      },
      workflow: [
        '도면 업로드',
        'YOLO 검출 실행 (전장 부품 27클래스)',
        '검출 결과 검증 (우선순위 큐 활용)',
        'BOM 생성 및 내보내기',
      ],
      tips: [
        '신뢰도 0.4가 기본값입니다. 과검출 시 0.5~0.6으로 조정하세요.',
        '수작업 라벨 추가로 놓친 심볼을 보완할 수 있습니다.',
        'Ground Truth가 있으면 정확도 비교가 가능합니다.',
      ],
    },
    {
      id: 'mechanical',
      title: '기계 부품도 (치수 중심)',
      icon: '⚙️',
      description: '샤프트, 플랜지 등 치수 정보가 중요한 기계 부품도 분석',
      preset: 'mechanical_part',
      settings: {
        symbol_detection: false,
        dimension_ocr: true,
        line_detection: true,
        confidence: 0.5,
      },
      workflow: [
        '도면 업로드',
        'eDOCr2 치수 OCR 실행',
        '치수 검증 및 단위 확인',
        'GD&T 기하공차 분석 (선택)',
        '치수 목록 내보내기',
      ],
      tips: [
        '치수 OCR은 한국어/영어 모두 지원합니다.',
        '공차 표기 (±0.1mm)도 자동 파싱됩니다.',
        'GD&T 편집기로 기하공차를 수정할 수 있습니다.',
      ],
    },
    {
      id: 'pid',
      title: 'P&ID 배관도',
      icon: '🔧',
      description: '배관계장도의 심볼과 연결선을 함께 분석',
      preset: 'pid',
      settings: {
        symbol_detection: true,
        dimension_ocr: false,
        line_detection: true,
        confidence: 0.3,
      },
      workflow: [
        '도면 업로드',
        'P&ID 심볼 검출 (YOLO P&ID 모드)',
        '연결선 검출 및 분석',
        '심볼-배관 연결 관계 추출',
        '검증 및 BOM 생성',
      ],
      tips: [
        'P&ID는 신뢰도를 0.3으로 낮게 설정하세요.',
        '선 검출을 활성화하면 배관 연결을 분석합니다.',
        '연결 관계는 수동으로 수정할 수 있습니다.',
      ],
    },
    {
      id: 'assembly',
      title: '조립도',
      icon: '🔩',
      description: '심볼 검출과 치수 OCR을 함께 사용하는 복합 분석',
      preset: 'assembly',
      settings: {
        symbol_detection: true,
        dimension_ocr: true,
        line_detection: true,
        confidence: 0.4,
      },
      workflow: [
        '도면 업로드',
        '심볼 검출 + 치수 OCR 동시 실행',
        '치수-심볼 관계 자동 추출',
        '검증 및 관계 수정',
        'BOM + 치수 목록 통합 생성',
      ],
      tips: [
        '관계 추출은 치수선 분석을 기반으로 합니다.',
        '근접성 기반 자동 연결이 적용됩니다.',
        '잘못된 관계는 삭제 후 수동 연결하세요.',
      ],
    },
  ];

  // 클래스 목록 (27개)
  const classCategories = [
    {
      category: '차단기류',
      classes: ['GCB (가스차단기)', 'VCB (진공차단기)', 'OCB (유입차단기)', '차단기'],
    },
    {
      category: '개폐기류',
      classes: ['DS (단로기)', 'ES (접지개폐기)', 'GS (가스구간개폐기)', 'LBS (부하개폐기)', '단로기_1P', '부하개폐기_1P'],
    },
    {
      category: '변성기류',
      classes: ['TR (변압기)', 'CT (변류기)', 'PT (계기용변압기)', 'GPT (접지형계기용변압기)', 'MOF (계기용변성기)'],
    },
    {
      category: '보호기류',
      classes: ['ARRESTER (피뢰기)', '피뢰기', 'TVSS (서지흡수기)', '퓨즈', '고장점표시기'],
    },
    {
      category: '기타 설비',
      classes: ['BUS (모선)', 'SC (직렬콘덴서)', 'SHUNT_REACTOR (분로리액터)', 'SS (정류기)', 'TC (탭절환기)', 'RECLOSER (리클로저)', '접지'],
    },
  ];

  // Active Learning 우선순위
  const priorityLevels = [
    { level: 'CRITICAL', color: 'bg-red-500', condition: '신뢰도 < 0.7', action: '즉시 확인 필요' },
    { level: 'HIGH', color: 'bg-orange-500', condition: '심볼 연결 없음', action: '연결 확인 필요' },
    { level: 'MEDIUM', color: 'bg-yellow-500', condition: '신뢰도 0.7-0.9', action: '검토 권장' },
    { level: 'LOW', color: 'bg-green-500', condition: '신뢰도 ≥ 0.9', action: '자동 승인 후보' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Blueprint AI BOM 가이드</h1>
                <p className="text-sm text-gray-500">v8.0 - AI 기반 도면 분석 및 BOM 생성</p>
              </div>
            </div>
            <Link
              to="/"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <Home className="w-4 h-4" />
              워크플로우로 이동
            </Link>
          </div>
        </div>
      </header>

      {/* 탭 네비게이션 */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            {[
              { id: 'overview', label: '개요', icon: <Info className="w-4 h-4" /> },
              { id: 'workflow', label: '워크플로우', icon: <GitBranch className="w-4 h-4" /> },
              { id: 'scenarios', label: '사용 시나리오', icon: <Zap className="w-4 h-4" /> },
              { id: 'settings', label: '설정 가이드', icon: <Settings className="w-4 h-4" /> },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600 font-medium'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 개요 탭 */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* 시스템 개요 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">시스템 개요</h2>

              {/* 파이프라인 다이어그램 */}
              <div className="bg-gray-50 rounded-lg p-6 mb-6">
                <div className="flex items-center justify-center gap-2 text-sm font-medium overflow-x-auto">
                  <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-800 rounded-lg whitespace-nowrap">
                    <Upload className="w-4 h-4" />
                    도면 업로드
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-800 rounded-lg whitespace-nowrap">
                    <Search className="w-4 h-4" />
                    YOLO 검출
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex items-center gap-2 px-4 py-2 bg-orange-100 text-orange-800 rounded-lg whitespace-nowrap">
                    <Ruler className="w-4 h-4" />
                    OCR 치수
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg whitespace-nowrap">
                    <Eye className="w-4 h-4" />
                    검증
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex items-center gap-2 px-4 py-2 bg-emerald-100 text-emerald-800 rounded-lg whitespace-nowrap">
                    <FileSpreadsheet className="w-4 h-4" />
                    BOM 생성
                  </div>
                </div>
              </div>

              {/* 핵심 기능 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-medium text-blue-900 mb-2">AI 심볼 검출</h3>
                  <p className="text-sm text-blue-700">YOLOv11 기반 27개 전장 부품 클래스 자동 검출. GPU 사용 시 2-3초 처리.</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <h3 className="font-medium text-purple-900 mb-2">OCR 치수 인식</h3>
                  <p className="text-sm text-purple-700">eDOCr2 기반 한국어 치수 인식. mm, inch 단위 및 공차 자동 파싱.</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <h3 className="font-medium text-green-900 mb-2">Human-in-the-Loop</h3>
                  <p className="text-sm text-green-700">Active Learning 기반 우선순위 검증 큐. 일괄 승인 및 자동 승인 지원.</p>
                </div>
              </div>
            </section>

            {/* 검출 클래스 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">검출 가능 클래스 (27개)</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {classCategories.map((cat) => (
                  <div key={cat.category} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">{cat.category}</h3>
                    <ul className="space-y-1">
                      {cat.classes.map((cls) => (
                        <li key={cls} className="text-sm text-gray-600 flex items-center gap-2">
                          <CheckCircle className="w-3 h-3 text-green-500" />
                          {cls}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>

            {/* Active Learning 우선순위 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">검증 우선순위 (Active Learning)</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">우선순위</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">조건</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">권장 액션</th>
                    </tr>
                  </thead>
                  <tbody>
                    {priorityLevels.map((p) => (
                      <tr key={p.level} className="border-b border-gray-100">
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium text-white ${p.color}`}>
                            {p.level}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-700">{p.condition}</td>
                        <td className="py-3 px-4 text-sm text-gray-700">{p.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* 워크플로우 탭 */}
        {activeTab === 'workflow' && (
          <div className="space-y-6">
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">분석 워크플로우</h2>

              {/* 워크플로우 다이어그램 */}
              <div className="relative">
                {workflowSteps.map((step, index) => (
                  <div key={step.id} className="flex gap-6 mb-8 last:mb-0">
                    {/* 스텝 번호 및 연결선 */}
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                        {step.id}
                      </div>
                      {index < workflowSteps.length - 1 && (
                        <div className="w-0.5 h-full bg-blue-200 mt-2" />
                      )}
                    </div>

                    {/* 스텝 내용 */}
                    <div className="flex-1 pb-8">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                          {step.icon}
                        </div>
                        <h3 className="text-lg font-medium text-gray-900">{step.title}</h3>
                      </div>
                      <p className="text-gray-600 mb-4">{step.description}</p>
                      <ul className="space-y-2">
                        {step.details.map((detail, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            {detail}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* 노드 관계도 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">기능 간 관계도</h2>
              <div className="bg-gray-50 rounded-lg p-6 font-mono text-sm overflow-x-auto">
                <pre className="text-gray-700">{`
┌─────────────────────────────────────────────────────────────────────┐
│                        Blueprint AI BOM                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐     ┌──────────────┐     ┌──────────────┐            │
│   │ 이미지    │────▶│   분석 옵션   │────▶│   AI 검출    │            │
│   │ 업로드    │     │   (프리셋)    │     │   (YOLO)    │            │
│   └──────────┘     └──────────────┘     └──────┬───────┘            │
│                                                 │                    │
│         ┌───────────────────┬──────────────────┼──────────┐         │
│         ▼                   ▼                  ▼          ▼         │
│   ┌──────────┐       ┌──────────┐       ┌──────────┐ ┌──────────┐   │
│   │ 치수 OCR │       │ 선 검출  │       │ 심볼 검증 │ │ GD&T    │   │
│   │ (eDOCr2) │       │ (Lines)  │       │ (HitL)   │ │ 분석    │   │
│   └────┬─────┘       └────┬─────┘       └────┬─────┘ └────┬─────┘   │
│        │                  │                  │            │         │
│        └─────────┬────────┴──────────────────┴────────────┘         │
│                  ▼                                                   │
│           ┌──────────────┐                                          │
│           │  관계 추출   │ ◀── 치수선 분석, 근접성 기반             │
│           └──────┬───────┘                                          │
│                  │                                                   │
│                  ▼                                                   │
│           ┌──────────────┐     ┌──────────────┐                     │
│           │  BOM 생성    │────▶│   내보내기   │                     │
│           │              │     │ Excel/CSV/   │                     │
│           │              │     │ JSON/PDF     │                     │
│           └──────────────┘     └──────────────┘                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─ 범례 ─────────────────────────────────────────────────────────────┐
│ HitL = Human-in-the-Loop (검증 큐)                                  │
│ GD&T = 기하공차 (Geometric Dimensioning & Tolerancing)             │
│ ────▶ = 데이터 흐름                                                 │
└─────────────────────────────────────────────────────────────────────┘
                `}</pre>
              </div>
            </section>
          </div>
        )}

        {/* 시나리오 탭 */}
        {activeTab === 'scenarios' && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <h3 className="font-medium text-blue-900">프리셋 선택 가이드</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    도면 유형에 따라 최적화된 프리셋을 선택하세요. 프리셋은 분석 옵션을 자동으로 설정합니다.
                  </p>
                </div>
              </div>
            </div>

            {scenarios.map((scenario) => (
              <div
                key={scenario.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
              >
                <button
                  onClick={() => setExpandedScenario(expandedScenario === scenario.id ? null : scenario.id)}
                  className="w-full flex items-center justify-between p-6 hover:bg-gray-50 transition"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-3xl">{scenario.icon}</span>
                    <div className="text-left">
                      <h3 className="text-lg font-medium text-gray-900">{scenario.title}</h3>
                      <p className="text-sm text-gray-500">{scenario.description}</p>
                    </div>
                  </div>
                  {expandedScenario === scenario.id ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </button>

                {expandedScenario === scenario.id && (
                  <div className="px-6 pb-6 border-t border-gray-100">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                      {/* 권장 설정 */}
                      <div>
                        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                          <Settings className="w-4 h-4" />
                          권장 설정
                        </h4>
                        <div className="space-y-2 bg-gray-50 rounded-lg p-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">심볼 검출</span>
                            <span className={scenario.settings.symbol_detection ? 'text-green-600 font-medium' : 'text-gray-400'}>
                              {scenario.settings.symbol_detection ? 'ON' : 'OFF'}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">치수 OCR</span>
                            <span className={scenario.settings.dimension_ocr ? 'text-green-600 font-medium' : 'text-gray-400'}>
                              {scenario.settings.dimension_ocr ? 'ON' : 'OFF'}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">선 검출</span>
                            <span className={scenario.settings.line_detection ? 'text-green-600 font-medium' : 'text-gray-400'}>
                              {scenario.settings.line_detection ? 'ON' : 'OFF'}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">신뢰도 임계값</span>
                            <span className="text-blue-600 font-medium">{scenario.settings.confidence}</span>
                          </div>
                        </div>
                      </div>

                      {/* 워크플로우 */}
                      <div>
                        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                          <GitBranch className="w-4 h-4" />
                          권장 워크플로우
                        </h4>
                        <ol className="space-y-2">
                          {scenario.workflow.map((step, i) => (
                            <li key={i} className="flex items-center gap-3 text-sm">
                              <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                                {i + 1}
                              </span>
                              <span className="text-gray-700">{step}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>

                    {/* 팁 */}
                    <div className="mt-6">
                      <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                        팁 & 주의사항
                      </h4>
                      <ul className="space-y-2">
                        {scenario.tips.map((tip, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                            <span className="text-amber-500 mt-0.5">•</span>
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 설정 가이드 탭 */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* 신뢰도 설정 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">신뢰도 임계값 가이드</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">임계값</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">특성</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">권장 상황</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-gray-100">
                      <td className="py-3 px-4 font-mono text-sm">0.3</td>
                      <td className="py-3 px-4 text-sm text-gray-700">높은 재현율 (Recall), 오검출 가능</td>
                      <td className="py-3 px-4 text-sm text-gray-700">P&ID, 복잡한 도면</td>
                    </tr>
                    <tr className="border-b border-gray-100">
                      <td className="py-3 px-4 font-mono text-sm font-medium text-blue-600">0.4 (기본)</td>
                      <td className="py-3 px-4 text-sm text-gray-700">균형잡힌 Precision-Recall</td>
                      <td className="py-3 px-4 text-sm text-gray-700">일반 전력 설비 도면</td>
                    </tr>
                    <tr className="border-b border-gray-100">
                      <td className="py-3 px-4 font-mono text-sm">0.5</td>
                      <td className="py-3 px-4 text-sm text-gray-700">높은 정밀도 (Precision)</td>
                      <td className="py-3 px-4 text-sm text-gray-700">과검출이 문제인 경우</td>
                    </tr>
                    <tr className="border-b border-gray-100">
                      <td className="py-3 px-4 font-mono text-sm">0.6+</td>
                      <td className="py-3 px-4 text-sm text-gray-700">매우 높은 정밀도, 미검출 가능</td>
                      <td className="py-3 px-4 text-sm text-gray-700">단순한 도면, 정확도 우선</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* OCR 엔진 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">OCR 엔진 선택</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-green-200 bg-green-50 rounded-lg p-4">
                  <h3 className="font-medium text-green-900 mb-2">eDOCr2 (권장)</h3>
                  <ul className="space-y-1 text-sm text-green-700">
                    <li>• 한국어 치수에 최적화</li>
                    <li>• 공차 표기 자동 파싱</li>
                    <li>• 기계 도면 특화</li>
                  </ul>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">PaddleOCR</h3>
                  <ul className="space-y-1 text-sm text-gray-600">
                    <li>• 다국어 지원</li>
                    <li>• 범용 텍스트 인식</li>
                    <li>• 레이아웃 분석 가능</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* 내보내기 형식 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">내보내기 형식</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="border border-gray-200 rounded-lg p-4 text-center">
                  <Download className="w-8 h-8 text-green-600 mx-auto mb-2" />
                  <h3 className="font-medium text-gray-900">Excel (.xlsx)</h3>
                  <p className="text-sm text-gray-500 mt-1">표준 스프레드시트</p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4 text-center">
                  <Download className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <h3 className="font-medium text-gray-900">CSV</h3>
                  <p className="text-sm text-gray-500 mt-1">텍스트 기반</p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4 text-center">
                  <Download className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                  <h3 className="font-medium text-gray-900">JSON</h3>
                  <p className="text-sm text-gray-500 mt-1">개발자용 데이터</p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4 text-center">
                  <Download className="w-8 h-8 text-red-600 mx-auto mb-2" />
                  <h3 className="font-medium text-gray-900">PDF</h3>
                  <p className="text-sm text-gray-500 mt-1">인쇄용 보고서</p>
                </div>
              </div>
            </section>

            {/* 단축키 */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">단축키</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">전체 승인</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">Ctrl + A</kbd>
                  </div>
                  <div className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">전체 거부</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">Ctrl + R</kbd>
                  </div>
                  <div className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">다음 항목</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">→</kbd>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">이전 항목</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">←</kbd>
                  </div>
                  <div className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">확대</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">+</kbd>
                  </div>
                  <div className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">축소</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">-</kbd>
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>

      {/* 푸터 */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>Blueprint AI BOM v8.0 - Powered by YOLOv11 + eDOCr2</span>
            <span>AX POC BlueprintFlow</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default GuidePage;
