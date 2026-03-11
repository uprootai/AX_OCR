import React from 'react';

interface PipelineStep {
  label: string;
  sub?: string;
  color: string;
  bg: string;
}

const ARROW = '\u2192';

function PipelineRow({ steps, title }: { steps: PipelineStep[]; title?: string }) {
  return (
    <div style={{ marginBottom: '16px' }}>
      {title && <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#666', marginBottom: '8px' }}>{title}</div>}
      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '4px' }}>
        {steps.map((step, i) => (
          <React.Fragment key={i}>
            <div style={{
              padding: '10px 16px',
              background: step.bg,
              border: `2px solid ${step.color}`,
              borderRadius: '8px',
              textAlign: 'center',
              minWidth: '90px',
            }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', color: step.color }}>{step.label}</div>
              {step.sub && <div style={{ fontSize: '0.7rem', color: '#666', marginTop: '2px' }}>{step.sub}</div>}
            </div>
            {i < steps.length - 1 && (
              <span style={{ fontSize: '1.3rem', color: '#bbb', padding: '0 2px' }}>{ARROW}</span>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

const MAIN_PIPELINE: PipelineStep[] = [
  { label: '업로드', sub: '이미지', color: '#37474f', bg: '#eceff1' },
  { label: 'VLM', sub: '분류', color: '#7b1fa2', bg: '#f3e5f5' },
  { label: 'YOLO', sub: '검출', color: '#e65100', bg: '#fff3e0' },
  { label: 'OCR', sub: 'eDOCr2 + 7', color: '#1b5e20', bg: '#e8f5e9' },
  { label: '치수', sub: '파싱', color: '#00838f', bg: '#e0f7fa' },
  { label: '공차', sub: 'SkinModel', color: '#4a148c', bg: '#f3e5f5' },
  { label: 'BOM', sub: '생성', color: '#1565c0', bg: '#e3f2fd' },
  { label: '견적', sub: 'PDF 내보내기', color: '#c62828', bg: '#ffebee' },
];

const PID_PIPELINE: PipelineStep[] = [
  { label: '업로드', sub: 'P&ID', color: '#37474f', bg: '#eceff1' },
  { label: 'VLM', sub: '분류', color: '#7b1fa2', bg: '#f3e5f5' },
  { label: '심볼', sub: 'YOLO', color: '#e65100', bg: '#fff3e0' },
  { label: '라인', sub: '검출', color: '#2e7d32', bg: '#e8f5e9' },
  { label: '연결', sub: 'PID Analyzer', color: '#00838f', bg: '#e0f7fa' },
  { label: '설계', sub: '검증', color: '#c62828', bg: '#ffebee' },
  { label: '리포트', sub: '생성', color: '#37474f', bg: '#eceff1' },
];

const BOM_PIPELINE: PipelineStep[] = [
  { label: '검출', sub: '73 클래스', color: '#e65100', bg: '#fff3e0' },
  { label: '분류', sub: 'BOM 항목', color: '#7b1fa2', bg: '#f3e5f5' },
  { label: '치수', sub: 'eDOCr2', color: '#1b5e20', bg: '#e8f5e9' },
  { label: '검증', sub: '에이전트/사람', color: '#00838f', bg: '#e0f7fa' },
  { label: 'BOM', sub: '생성', color: '#1565c0', bg: '#e3f2fd' },
  { label: '단가', sub: '원가 계산', color: '#4a148c', bg: '#f3e5f5' },
  { label: '내보내기', sub: 'PDF/Excel', color: '#c62828', bg: '#ffebee' },
];

const PIPELINES: Record<string, { title: string; steps: PipelineStep[] }> = {
  main: { title: '기계 도면 파이프라인', steps: MAIN_PIPELINE },
  pid: { title: 'P&ID 파이프라인', steps: PID_PIPELINE },
  bom: { title: 'BOM 파이프라인', steps: BOM_PIPELINE },
};

interface Props {
  type?: 'main' | 'pid' | 'bom' | 'all';
}

export default function PipelineDiagram({ type = 'all' }: Props) {
  const pipelines = type === 'all'
    ? Object.values(PIPELINES)
    : [PIPELINES[type]];

  return (
    <div style={{
      padding: '16px',
      border: '1px solid var(--sl-color-gray-5)',
      borderRadius: '8px',
      overflowX: 'auto',
    }}>
      {pipelines.map((p, i) => (
        <PipelineRow key={i} steps={p.steps} title={pipelines.length > 1 ? p.title : undefined} />
      ))}
    </div>
  );
}
