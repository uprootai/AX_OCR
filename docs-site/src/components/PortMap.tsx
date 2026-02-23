import React from 'react';

interface PortEntry {
  port: number;
  name: string;
  category: string;
  gpu?: boolean;
}

const PORTS: PortEntry[] = [
  { port: 5002, name: 'eDOCr2', category: 'ocr', gpu: true },
  { port: 5003, name: 'SkinModel', category: 'analysis' },
  { port: 5004, name: 'Vision-Language', category: 'ai', gpu: true },
  { port: 5005, name: 'YOLO v11', category: 'detection', gpu: true },
  { port: 5006, name: 'PaddleOCR', category: 'ocr' },
  { port: 5007, name: 'Knowledge', category: 'knowledge' },
  { port: 5008, name: 'Tesseract', category: 'ocr' },
  { port: 5009, name: 'TrOCR', category: 'ocr', gpu: true },
  { port: 5010, name: 'ESRGAN', category: 'preprocessing', gpu: true },
  { port: 5011, name: 'OCR Ensemble', category: 'ocr', gpu: true },
  { port: 5012, name: 'EDGNet', category: 'segmentation', gpu: true },
  { port: 5013, name: 'Surya OCR', category: 'ocr' },
  { port: 5014, name: 'DocTR', category: 'ocr' },
  { port: 5015, name: 'EasyOCR', category: 'ocr' },
  { port: 5016, name: 'Line Detector', category: 'segmentation' },
  { port: 5018, name: 'PID Analyzer', category: 'analysis' },
  { port: 5019, name: 'Design Checker', category: 'analysis' },
  { port: 5020, name: 'Blueprint AI BOM', category: 'analysis', gpu: true },
  { port: 5021, name: 'PID Composer', category: 'analysis' },
  { port: 5022, name: 'Table Detector', category: 'detection', gpu: true },
];

const INFRA = [
  { port: 3000, name: 'BOM Frontend', category: 'frontend' },
  { port: 5173, name: 'Web UI', category: 'frontend' },
  { port: 7474, name: 'Neo4j Browser', category: 'database' },
  { port: 7687, name: 'Neo4j Bolt', category: 'database' },
  { port: 8000, name: 'Gateway API', category: 'gateway' },
];

const CATEGORY_COLORS: Record<string, { bg: string; color: string }> = {
  detection: { bg: '#fff3e0', color: '#e65100' },
  ocr: { bg: '#e8f5e9', color: '#1b5e20' },
  segmentation: { bg: '#e1f5fe', color: '#01579b' },
  preprocessing: { bg: '#f3e5f5', color: '#4a148c' },
  analysis: { bg: '#ede7f6', color: '#311b92' },
  knowledge: { bg: '#fce4ec', color: '#880e4f' },
  ai: { bg: '#e8eaf6', color: '#1a237e' },
  frontend: { bg: '#e3f2fd', color: '#1565c0' },
  database: { bg: '#efebe9', color: '#3e2723' },
  gateway: { bg: '#263238', color: '#ffffff' },
};

function PortRow({ entry }: { entry: PortEntry & { gpu?: boolean } }) {
  const cc = CATEGORY_COLORS[entry.category] || { bg: '#f5f5f5', color: '#333' };
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '6px 10px',
      borderRadius: '6px',
      background: cc.bg,
      border: `1px solid ${cc.color}20`,
    }}>
      <code style={{ fontWeight: 700, fontSize: '0.85rem', minWidth: '45px', color: cc.color }}>{entry.port}</code>
      <span style={{ flex: 1, fontWeight: 500, fontSize: '0.85rem' }}>{entry.name}</span>
      <span style={{
        fontSize: '0.65rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        padding: '2px 6px',
        borderRadius: '3px',
        background: `${cc.color}15`,
        color: cc.color,
      }}>
        {entry.category}
      </span>
      {entry.gpu && (
        <span style={{ fontSize: '0.6rem', background: '#ff6f00', color: 'white', padding: '1px 5px', borderRadius: '3px', fontWeight: 700 }}>
          GPU
        </span>
      )}
    </div>
  );
}

export default function PortMap() {
  return (
    <div style={{ border: '1px solid var(--ifm-color-emphasis-300)', borderRadius: '8px', padding: '16px' }}>
      <div style={{ fontWeight: 700, marginBottom: '12px', fontSize: '0.9rem' }}>ML Services (5002-5022)</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '6px', marginBottom: '20px' }}>
        {PORTS.map(p => <PortRow key={p.port} entry={p} />)}
      </div>

      <div style={{ fontWeight: 700, marginBottom: '12px', fontSize: '0.9rem' }}>Infrastructure</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '6px' }}>
        {INFRA.map(p => <PortRow key={p.port} entry={p} />)}
      </div>

      <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
        {Object.entries(CATEGORY_COLORS).map(([cat, cc]) => (
          <span key={cat} style={{
            fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px',
            background: cc.bg, color: cc.color, fontWeight: 600, textTransform: 'uppercase',
            border: `1px solid ${cc.color}30`,
          }}>
            {cat}
          </span>
        ))}
      </div>
    </div>
  );
}
