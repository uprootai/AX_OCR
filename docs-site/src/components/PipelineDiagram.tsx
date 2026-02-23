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
  { label: 'Upload', sub: 'Image', color: '#37474f', bg: '#eceff1' },
  { label: 'VLM', sub: 'Classification', color: '#7b1fa2', bg: '#f3e5f5' },
  { label: 'YOLO', sub: 'Detection', color: '#e65100', bg: '#fff3e0' },
  { label: 'OCR', sub: 'eDOCr2 + 7', color: '#1b5e20', bg: '#e8f5e9' },
  { label: 'Dimension', sub: 'Parsing', color: '#00838f', bg: '#e0f7fa' },
  { label: 'Tolerance', sub: 'SkinModel', color: '#4a148c', bg: '#f3e5f5' },
  { label: 'BOM', sub: 'Generation', color: '#1565c0', bg: '#e3f2fd' },
  { label: 'Quote', sub: 'PDF Export', color: '#c62828', bg: '#ffebee' },
];

const PID_PIPELINE: PipelineStep[] = [
  { label: 'Upload', sub: 'P&ID', color: '#37474f', bg: '#eceff1' },
  { label: 'VLM', sub: 'Classify', color: '#7b1fa2', bg: '#f3e5f5' },
  { label: 'Symbol', sub: 'YOLO', color: '#e65100', bg: '#fff3e0' },
  { label: 'Line', sub: 'Detector', color: '#2e7d32', bg: '#e8f5e9' },
  { label: 'Connect', sub: 'PID Analyzer', color: '#00838f', bg: '#e0f7fa' },
  { label: 'Design', sub: 'Checker', color: '#c62828', bg: '#ffebee' },
  { label: 'Report', sub: 'Generation', color: '#37474f', bg: '#eceff1' },
];

const BOM_PIPELINE: PipelineStep[] = [
  { label: 'Detection', sub: '73 classes', color: '#e65100', bg: '#fff3e0' },
  { label: 'Classify', sub: 'BOM items', color: '#7b1fa2', bg: '#f3e5f5' },
  { label: 'Dimension', sub: 'eDOCr2', color: '#1b5e20', bg: '#e8f5e9' },
  { label: 'Verify', sub: 'Agent/Human', color: '#00838f', bg: '#e0f7fa' },
  { label: 'BOM', sub: 'Generation', color: '#1565c0', bg: '#e3f2fd' },
  { label: 'Pricing', sub: 'Cost Calc', color: '#4a148c', bg: '#f3e5f5' },
  { label: 'Export', sub: 'PDF/Excel', color: '#c62828', bg: '#ffebee' },
];

const PIPELINES: Record<string, { title: string; steps: PipelineStep[] }> = {
  main: { title: 'Mechanical Drawing Pipeline', steps: MAIN_PIPELINE },
  pid: { title: 'P&ID Pipeline', steps: PID_PIPELINE },
  bom: { title: 'BOM Pipeline', steps: BOM_PIPELINE },
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
      border: '1px solid var(--ifm-color-emphasis-300)',
      borderRadius: '8px',
      overflowX: 'auto',
    }}>
      {pipelines.map((p, i) => (
        <PipelineRow key={i} steps={p.steps} title={pipelines.length > 1 ? p.title : undefined} />
      ))}
    </div>
  );
}
