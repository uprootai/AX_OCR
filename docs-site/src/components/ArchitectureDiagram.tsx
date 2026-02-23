import React from 'react';

const CATEGORIES: Record<string, { label: string; color: string; bg: string; services: { name: string; port: number; gpu?: boolean }[] }> = {
  detection: {
    label: 'Detection',
    color: '#e65100',
    bg: '#fff3e0',
    services: [
      { name: 'YOLO v11', port: 5005, gpu: true },
      { name: 'Table Detector', port: 5022, gpu: true },
    ],
  },
  ocr: {
    label: 'OCR',
    color: '#1b5e20',
    bg: '#e8f5e9',
    services: [
      { name: 'eDOCr2', port: 5002, gpu: true },
      { name: 'PaddleOCR', port: 5006 },
      { name: 'Tesseract', port: 5008 },
      { name: 'TrOCR', port: 5009, gpu: true },
      { name: 'OCR Ensemble', port: 5011, gpu: true },
      { name: 'Surya OCR', port: 5013 },
      { name: 'DocTR', port: 5014 },
      { name: 'EasyOCR', port: 5015 },
    ],
  },
  segmentation: {
    label: 'Segmentation',
    color: '#01579b',
    bg: '#e1f5fe',
    services: [
      { name: 'EDGNet', port: 5012, gpu: true },
      { name: 'Line Detector', port: 5016 },
    ],
  },
  preprocessing: {
    label: 'Preprocessing',
    color: '#4a148c',
    bg: '#f3e5f5',
    services: [{ name: 'ESRGAN', port: 5010, gpu: true }],
  },
  analysis: {
    label: 'Analysis',
    color: '#311b92',
    bg: '#ede7f6',
    services: [
      { name: 'SkinModel', port: 5003 },
      { name: 'PID Analyzer', port: 5018 },
      { name: 'Design Checker', port: 5019 },
      { name: 'Blueprint AI BOM', port: 5020, gpu: true },
      { name: 'PID Composer', port: 5021 },
    ],
  },
  knowledge: {
    label: 'Knowledge',
    color: '#880e4f',
    bg: '#fce4ec',
    services: [{ name: 'Knowledge', port: 5007 }],
  },
  ai: {
    label: 'AI',
    color: '#1a237e',
    bg: '#e8eaf6',
    services: [{ name: 'Vision-Language', port: 5004, gpu: true }],
  },
};

function ServiceBox({ name, port, gpu }: { name: string; port: number; gpu?: boolean }) {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 10px',
      background: 'white',
      borderRadius: '4px',
      fontSize: '0.8rem',
      border: '1px solid rgba(0,0,0,0.1)',
      whiteSpace: 'nowrap',
    }}>
      <strong>{name}</strong>
      <code style={{ fontSize: '0.7rem', color: '#666' }}>:{port}</code>
      {gpu && <span style={{ fontSize: '0.6rem', background: '#fff3e0', color: '#e65100', padding: '1px 4px', borderRadius: '3px', fontWeight: 600 }}>GPU</span>}
    </div>
  );
}

export default function ArchitectureDiagram() {
  return (
    <div style={{ padding: '16px', border: '1px solid var(--ifm-color-emphasis-300)', borderRadius: '8px', overflow: 'auto' }}>
      {/* User layer */}
      <div style={{ textAlign: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'inline-block', padding: '8px 24px', background: '#f5f5f5', borderRadius: '20px', fontWeight: 600, fontSize: '0.9rem' }}>
          User
        </div>
        <div style={{ fontSize: '1.2rem', color: '#999' }}>&#8595;</div>
      </div>

      {/* Frontend layer */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '12px' }}>
        <div style={{ padding: '8px 16px', background: '#e3f2fd', border: '2px solid #1565c0', borderRadius: '8px', textAlign: 'center' }}>
          <strong>Web UI</strong><br /><code>:5173</code>
        </div>
        <div style={{ padding: '8px 16px', background: '#e3f2fd', border: '2px solid #1565c0', borderRadius: '8px', textAlign: 'center' }}>
          <strong>BOM Frontend</strong><br /><code>:3000</code>
        </div>
      </div>

      <div style={{ textAlign: 'center', fontSize: '1.2rem', color: '#999', marginBottom: '12px' }}>&#8595;</div>

      {/* Gateway */}
      <div style={{ textAlign: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'inline-block', padding: '10px 32px', background: '#263238', color: 'white', borderRadius: '8px', fontWeight: 600 }}>
          Gateway API <code style={{ color: '#80cbc4' }}>:8000</code>
        </div>
      </div>

      <div style={{ textAlign: 'center', fontSize: '1.2rem', color: '#999', marginBottom: '16px' }}>&#8595;</div>

      {/* Service categories */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
        {Object.entries(CATEGORIES).map(([key, cat]) => (
          <div key={key} style={{ padding: '12px', borderRadius: '8px', background: cat.bg, border: `2px solid ${cat.color}30` }}>
            <div style={{ fontWeight: 700, color: cat.color, marginBottom: '8px', fontSize: '0.85rem' }}>
              {cat.label} ({cat.services.length})
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {cat.services.map(s => (
                <ServiceBox key={s.port} {...s} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Infrastructure */}
      <div style={{ marginTop: '16px', padding: '12px', background: '#eceff1', borderRadius: '8px', border: '2px solid #90a4ae' }}>
        <div style={{ fontWeight: 700, color: '#37474f', marginBottom: '8px', fontSize: '0.85rem' }}>Infrastructure</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <ServiceBox name="Neo4j" port={7687} />
          <ServiceBox name="Neo4j Browser" port={7474} />
        </div>
      </div>

      <div style={{ marginTop: '12px', textAlign: 'center', fontSize: '0.75rem', color: '#999' }}>
        Network: <code>ax_poc_network</code> (bridge) | GPU: 10 services | CPU: 11 services
      </div>
    </div>
  );
}
