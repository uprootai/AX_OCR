import React from 'react';

/* ─── Types ────────────────────────────────────────────── */

export interface FlowNode {
  id: string;
  label: string;
  sub?: string;
  color?: string;
  bg?: string;
  shape?: 'rect' | 'diamond' | 'rounded' | 'stadium';
}

export interface FlowEdge {
  from: string;
  to: string;
  label?: string;
  dashed?: boolean;
}

interface Props {
  nodes: FlowNode[];
  edges: FlowEdge[];
  layers: string[][];
  direction?: 'LR' | 'TD';
  title?: string;
  nodeWidth?: number;
  nodeHeight?: number;
}

/* ─── Constants ────────────────────────────────────────── */

const DEF_W = 130;
const DEF_H = 56;
const LAYER_GAP = 52;
const NODE_GAP = 16;
const DIAMOND_SZ = 68;
const ARROW = 8;
const PAD = 16;

/* ─── Component ────────────────────────────────────────── */

export default function FlowDiagram({
  nodes, edges, layers, direction = 'LR', title,
  nodeWidth = DEF_W, nodeHeight = DEF_H,
}: Props) {
  const nm = new Map(nodes.map(n => [n.id, n]));
  const mid = (title ?? '').replace(/[^a-z0-9]/gi, '').slice(0, 8).toLowerCase() || 'fd';
  const mkr = `fa${mid}`;
  const isLR = direction === 'LR';

  const sz = (n: FlowNode) =>
    n.shape === 'diamond' ? { w: DIAMOND_SZ, h: DIAMOND_SZ } : { w: nodeWidth, h: nodeHeight };

  /* ── Layout ─────────────────────────────────────────── */
  const pos: Record<string, { x: number; y: number; w: number; h: number }> = {};

  if (isLR) {
    let maxH = 0;
    for (const layer of layers) {
      let h = 0;
      for (const nid of layer) { const n = nm.get(nid); if (n) h += sz(n).h; }
      h += Math.max(0, layer.length - 1) * NODE_GAP;
      maxH = Math.max(maxH, h);
    }
    let x = PAD;
    for (const layer of layers) {
      let lh = 0;
      for (const nid of layer) { const n = nm.get(nid); if (n) lh += sz(n).h; }
      lh += Math.max(0, layer.length - 1) * NODE_GAP;
      let y = PAD + (maxH - lh) / 2;
      let mw = 0;
      for (const nid of layer) {
        const n = nm.get(nid); if (!n) continue;
        const { w, h } = sz(n);
        pos[nid] = { x, y, w, h };
        y += h + NODE_GAP;
        mw = Math.max(mw, w);
      }
      x += mw + LAYER_GAP;
    }
  } else {
    let maxW = 0;
    for (const layer of layers) {
      let w = 0;
      for (const nid of layer) { const n = nm.get(nid); if (n) w += sz(n).w; }
      w += Math.max(0, layer.length - 1) * NODE_GAP;
      maxW = Math.max(maxW, w);
    }
    let y = PAD;
    for (const layer of layers) {
      let lw = 0;
      for (const nid of layer) { const n = nm.get(nid); if (n) lw += sz(n).w; }
      lw += Math.max(0, layer.length - 1) * NODE_GAP;
      let x = PAD + (maxW - lw) / 2;
      let mh = 0;
      for (const nid of layer) {
        const n = nm.get(nid); if (!n) continue;
        const { w, h } = sz(n);
        pos[nid] = { x, y, w, h };
        x += w + NODE_GAP;
        mh = Math.max(mh, h);
      }
      y += mh + LAYER_GAP;
    }
  }

  /* ── Dimensions ─────────────────────────────────────── */
  let totalW = 0, totalH = 0;
  for (const p of Object.values(pos)) {
    totalW = Math.max(totalW, p.x + p.w);
    totalH = Math.max(totalH, p.y + p.h);
  }
  totalW += PAD;
  totalH += PAD;

  /* ── Arrow paths ────────────────────────────────────── */
  const arrows = edges.map(e => {
    const fp = pos[e.from], tp = pos[e.to];
    if (!fp || !tp) return null;
    let x1: number, y1: number, x2: number, y2: number;
    if (isLR) {
      x1 = fp.x + fp.w; y1 = fp.y + fp.h / 2;
      x2 = tp.x;        y2 = tp.y + tp.h / 2;
    } else {
      x1 = fp.x + fp.w / 2; y1 = fp.y + fp.h;
      x2 = tp.x + tp.w / 2; y2 = tp.y;
    }
    const cx = isLR ? Math.min(Math.abs(x2 - x1) * 0.4, 40) : 0;
    const cy = isLR ? 0 : Math.min(Math.abs(y2 - y1) * 0.4, 40);
    const d = `M${x1},${y1} C${x1 + cx},${y1 + cy} ${x2 - cx},${y2 - cy} ${x2},${y2}`;
    return { d, label: e.label, lx: (x1 + x2) / 2, ly: (y1 + y2) / 2, dashed: e.dashed };
  }).filter(Boolean) as { d: string; label?: string; lx: number; ly: number; dashed?: boolean }[];

  /* ── Render ─────────────────────────────────────────── */
  return (
    <div style={{
      border: '1px solid var(--sl-color-gray-5)',
      borderRadius: '8px',
      overflowX: 'auto',
      background: 'var(--sl-color-bg)',
    }}>
      {title && (
        <div style={{ fontWeight: 700, fontSize: '0.9rem', padding: '12px 16px 0', color: 'var(--sl-color-gray-1)' }}>
          {title}
        </div>
      )}
      <div style={{ position: 'relative', width: totalW, height: totalH, margin: '0 auto' }}>
        {/* Nodes */}
        {nodes.map(node => {
          const p = pos[node.id];
          if (!p) return null;
          const color = node.color || 'var(--sl-color-gray-2)';
          const rawBg = node.bg || 'var(--sl-color-gray-6)';
          const bg = node.bg
            ? `color-mix(in srgb, ${node.bg} 55%, var(--sl-color-bg))`
            : rawBg;

          if (node.shape === 'diamond') {
            return (
              <div key={node.id} style={{
                position: 'absolute', left: p.x, top: p.y, width: p.w, height: p.h,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <div style={{
                  width: p.w * 0.72, height: p.h * 0.72,
                  transform: 'rotate(45deg)', background: bg,
                  border: `2px solid ${color}`, borderRadius: '4px',
                  position: 'absolute',
                }} />
                <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', lineHeight: 1.2 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color }}>{node.label}</div>
                  {node.sub && <div style={{ fontSize: '0.65rem', color: 'var(--sl-color-gray-3)' }}>{node.sub}</div>}
                </div>
              </div>
            );
          }

          const radius = node.shape === 'rect' ? '4px'
            : node.shape === 'stadium' ? `${p.h / 2}px` : '8px';

          return (
            <div key={node.id} style={{
              position: 'absolute', left: p.x, top: p.y, width: p.w, height: p.h,
              background: bg, border: `2px solid ${color}`, borderRadius: radius,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              padding: '4px 8px', boxSizing: 'border-box',
            }}>
              <div style={{ fontWeight: 600, fontSize: '0.8rem', color, textAlign: 'center', lineHeight: 1.2 }}>
                {node.label}
              </div>
              {node.sub && (
                <div style={{ fontSize: '0.65rem', color: 'var(--sl-color-gray-3)', marginTop: '2px', textAlign: 'center' }}>
                  {node.sub}
                </div>
              )}
            </div>
          );
        })}

        {/* SVG arrows */}
        <svg style={{ position: 'absolute', top: 0, left: 0, width: totalW, height: totalH, pointerEvents: 'none' }}>
          <defs>
            <marker id={mkr} markerWidth={ARROW} markerHeight={ARROW}
              refX={ARROW - 1} refY={ARROW / 2} orient="auto">
              <polygon points={`0 1,${ARROW - 1} ${ARROW / 2},0 ${ARROW - 1}`}
                fill="var(--sl-color-gray-4)" />
            </marker>
          </defs>
          {arrows.map((a, i) => (
            <g key={i}>
              <path d={a.d} stroke="var(--sl-color-gray-4)" strokeWidth="1.5"
                fill="none" strokeDasharray={a.dashed ? '6 3' : undefined}
                markerEnd={`url(#${mkr})`} />
              {a.label && (
                <>
                  <rect x={a.lx - a.label.length * 3.5 - 4} y={a.ly - 9}
                    width={a.label.length * 7 + 8} height={16} rx={4}
                    fill="var(--sl-color-bg)" opacity={0.92} />
                  <text x={a.lx} y={a.ly + 1} textAnchor="middle" dominantBaseline="middle"
                    fontSize="11" fontWeight="600" fill="var(--sl-color-gray-2)"
                    fontFamily="var(--sl-font)">
                    {a.label}
                  </text>
                </>
              )}
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}
