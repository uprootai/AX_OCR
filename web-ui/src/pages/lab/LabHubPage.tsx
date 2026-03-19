/**
 * LabHubPage — Lab 카테고리 허브
 *
 * 각 Lab의 목적, 상태, 핵심 메트릭을 카드로 보여주고
 * Active Lab은 해당 환경으로 이동시킨다.
 */
import { useTranslation } from 'react-i18next';
import {
  FlaskConical,
  Ruler,
  ScanText,
  Target,
  Triangle,
  Table2,
  Gem,
  ExternalLink,
  ArrowRight,
} from 'lucide-react';

interface LabCard {
  id: string;
  icon: typeof Ruler;
  color: string;       // tailwind color prefix (amber, blue, ...)
  status: 'active' | 'planned';
  href?: string;
  external?: boolean;
  metrics?: { label: string; value: string }[];
}

const LAB_CARDS: LabCard[] = [
  {
    id: 'dimension',
    icon: Ruler,
    color: 'red',
    status: 'active',
    href: '/bom/dimension-lab',
    external: true,
    metrics: [
      { label: 'OCR 엔진', value: '7개' },
      { label: '분류 방법', value: '11개' },
      { label: '매트릭스', value: '77셀' },
    ],
  },
  {
    id: 'ocrBenchmark',
    icon: ScanText,
    color: 'blue',
    status: 'planned',
    metrics: [
      { label: 'OCR 엔진', value: '8개' },
      { label: '비교 항목', value: '정확도·속도·문자별' },
    ],
  },
  {
    id: 'detection',
    icon: Target,
    color: 'green',
    status: 'planned',
    metrics: [
      { label: '모델', value: 'YOLO v11' },
      { label: '비교 항목', value: '신뢰도·해상도·모델타입' },
    ],
  },
  {
    id: 'tolerance',
    icon: Triangle,
    color: 'purple',
    status: 'planned',
    metrics: [
      { label: '파싱 방법', value: 'SkinModel · 규칙 기반' },
      { label: '대상', value: 'GD&T · 기하공차' },
    ],
  },
  {
    id: 'table',
    icon: Table2,
    color: 'cyan',
    status: 'planned',
    metrics: [
      { label: '추출 방법', value: 'TATR · YOLO+TD' },
      { label: '대상', value: 'Parts List · BOM 테이블' },
    ],
  },
  {
    id: 'material',
    icon: Gem,
    color: 'pink',
    status: 'planned',
    metrics: [
      { label: '분류 방법', value: 'VLM · 규칙 · 카탈로그' },
      { label: '대상', value: '소재·재질 분류' },
    ],
  },
];

// Tailwind 동적 클래스는 purge에 잡히지 않으므로 명시 매핑
const COLOR_MAP: Record<string, { bg: string; border: string; text: string; badge: string; hoverBg: string }> = {
  red:    { bg: 'bg-red-50 dark:bg-red-900/20',       border: 'border-red-200 dark:border-red-800',       text: 'text-red-600 dark:text-red-400',       badge: 'bg-red-600',    hoverBg: 'hover:border-red-400 dark:hover:border-red-600' },
  blue:   { bg: 'bg-blue-50 dark:bg-blue-900/20',     border: 'border-blue-200 dark:border-blue-800',     text: 'text-blue-600 dark:text-blue-400',     badge: 'bg-blue-600',   hoverBg: 'hover:border-blue-400 dark:hover:border-blue-600' },
  green:  { bg: 'bg-green-50 dark:bg-green-900/20',   border: 'border-green-200 dark:border-green-800',   text: 'text-green-600 dark:text-green-400',   badge: 'bg-green-600',  hoverBg: 'hover:border-green-400 dark:hover:border-green-600' },
  purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', border: 'border-purple-200 dark:border-purple-800', text: 'text-purple-600 dark:text-purple-400', badge: 'bg-purple-600', hoverBg: 'hover:border-purple-400 dark:hover:border-purple-600' },
  cyan:   { bg: 'bg-cyan-50 dark:bg-cyan-900/20',     border: 'border-cyan-200 dark:border-cyan-800',     text: 'text-cyan-600 dark:text-cyan-400',     badge: 'bg-cyan-600',   hoverBg: 'hover:border-cyan-400 dark:hover:border-cyan-600' },
  pink:   { bg: 'bg-pink-50 dark:bg-pink-900/20',     border: 'border-pink-200 dark:border-pink-800',     text: 'text-pink-600 dark:text-pink-400',     badge: 'bg-pink-600',   hoverBg: 'hover:border-pink-400 dark:hover:border-pink-600' },
};

function StatusBadge({ status }: { status: 'active' | 'planned' }) {
  if (status === 'active') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
        ACTIVE
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
      <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
      PLANNED
    </span>
  );
}

export default function LabHubPage() {
  const { t } = useTranslation();

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <FlaskConical className="h-7 w-7 text-amber-600 dark:text-amber-400" />
          <h1 className="text-2xl font-bold text-foreground">{t('lab.title')}</h1>
          <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-600 text-white rounded">
            LAB
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{t('lab.subtitle')}</p>
      </div>

      {/* Concept */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-2">{t('lab.concept')}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-amber-800 dark:text-amber-200">
          <div className="flex items-start gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">1</span>
            <span><strong>Ground Truth</strong> — {t('lab.step1')}</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">2</span>
            <span><strong>{t('lab.step2Label')}</strong> — {t('lab.step2')}</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">3</span>
            <span><strong>{t('lab.step3Label')}</strong> — {t('lab.step3')}</span>
          </div>
        </div>
      </div>

      {/* Lab Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {LAB_CARDS.map((lab) => {
          const c = COLOR_MAP[lab.color];
          const Icon = lab.icon;
          const isActive = lab.status === 'active';

          const cardContent = (
            <div
              className={`rounded-xl border-2 p-5 transition-all ${c.bg} ${c.border} ${isActive ? `cursor-pointer ${c.hoverBg} hover:shadow-md` : 'opacity-60'}`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${c.badge}`}>
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-foreground">{t(`lab.${lab.id}Title`)}</h3>
                    <p className="text-[11px] text-muted-foreground">{t(`lab.${lab.id}Desc`)}</p>
                  </div>
                </div>
                <StatusBadge status={lab.status} />
              </div>

              {/* Metrics */}
              {lab.metrics && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {lab.metrics.map((m, i) => (
                    <div key={i} className="px-2 py-1 bg-white/60 dark:bg-gray-800/40 rounded text-[11px]">
                      <span className="text-muted-foreground">{m.label}: </span>
                      <span className="font-semibold text-foreground">{m.value}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Action */}
              <div className={`flex items-center gap-1.5 text-xs font-medium ${isActive ? c.text : 'text-gray-400'}`}>
                {isActive ? (
                  <>
                    <span>{t('lab.openLab')}</span>
                    {lab.external ? <ExternalLink className="h-3 w-3" /> : <ArrowRight className="h-3 w-3" />}
                  </>
                ) : (
                  <span>{t('lab.comingSoon')}</span>
                )}
              </div>
            </div>
          );

          if (isActive && lab.href) {
            if (lab.external) {
              return (
                <a key={lab.id} href={lab.href} target="_blank" rel="noopener noreferrer" className="no-underline">
                  {cardContent}
                </a>
              );
            }
            return (
              <a key={lab.id} href={lab.href} className="no-underline">
                {cardContent}
              </a>
            );
          }

          return <div key={lab.id}>{cardContent}</div>;
        })}
      </div>
    </div>
  );
}
