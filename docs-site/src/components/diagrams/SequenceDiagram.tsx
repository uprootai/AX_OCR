import React from 'react';

/* ─── Types ────────────────────────────────────────────── */

export interface Participant {
  id: string;
  label: string;
  color?: string;
}

export interface Message {
  from: string;
  to: string;
  label: string;
  type?: 'sync' | 'reply' | 'self';
}

export interface LoopBlock {
  label: string;
  start: number;
  end: number;
}

interface Props {
  participants: Participant[];
  messages: Message[];
  loops?: LoopBlock[];
  title?: string;
}

/* ─── Constants ────────────────────────────────────────── */

const P_W = 130;
const P_H = 36;
const P_GAP = 50;
const MSG_H = 44;
const PAD = 24;
const TOP = 16;
const BOT = 44;

/* ─── Component ────────────────────────────────────────── */

export default function SequenceDiagram({ participants, messages, loops = [], title }: Props) {
  const mid = React.useId().replace(/:/g, '');
  const mkr = `sm${mid}`;
  const mkrR = `sr${mid}`;

  const pIdx = new Map(participants.map((p, i) => [p.id, i]));
  const totalW = PAD * 2 + participants.length * P_W + Math.max(0, participants.length - 1) * P_GAP;
  const msgStart = TOP + P_H + 24;
  const totalH = msgStart + messages.length * MSG_H + BOT + P_H;

  const px = (i: number) => PAD + i * (P_W + P_GAP) + P_W / 2;

  const renderParticipant = (p: Participant, i: number, y: number) => {
    const cx = px(i);
    const c = p.color || 'var(--ifm-color-primary)';
    return (
      <g key={`${p.id}-${y}`}>
        <rect x={cx - P_W / 2} y={y} width={P_W} height={P_H} rx={6}
          fill={c} opacity={0.12} stroke={c} strokeWidth={1.5} />
        <text x={cx} y={y + P_H / 2} textAnchor="middle" dominantBaseline="central"
          fontSize="12" fontWeight="600" fill="var(--ifm-color-emphasis-800)"
          fontFamily="var(--ifm-font-family-base)">
          {p.label}
        </text>
      </g>
    );
  };

  return (
    <div style={{
      border: '1px solid var(--ifm-color-emphasis-300)',
      borderRadius: '8px', overflowX: 'auto',
      background: 'var(--ifm-background-surface-color, var(--ifm-background-color))',
    }}>
      {title && (
        <div style={{ fontWeight: 700, fontSize: '0.9rem', padding: '12px 16px 0', color: 'var(--ifm-color-emphasis-800)' }}>
          {title}
        </div>
      )}
      <svg width={totalW} height={totalH} style={{ display: 'block', margin: '0 auto' }}>
        <defs>
          <marker id={mkr} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <polygon points="0 1,7 4,0 7" fill="var(--ifm-color-emphasis-600)" />
          </marker>
          <marker id={mkrR} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <polygon points="0 1,7 4,0 7" fill="var(--ifm-color-emphasis-400)" />
          </marker>
        </defs>

        {/* Top participants */}
        {participants.map((p, i) => renderParticipant(p, i, TOP))}

        {/* Lifelines */}
        {participants.map((p, i) => (
          <line key={`ll-${p.id}`}
            x1={px(i)} y1={TOP + P_H} x2={px(i)} y2={totalH - BOT}
            stroke="var(--ifm-color-emphasis-300)" strokeDasharray="4 4" strokeWidth={1} />
        ))}

        {/* Loop blocks */}
        {loops.map((lp, li) => {
          const y1 = msgStart + lp.start * MSG_H - 10;
          const y2 = msgStart + (lp.end + 1) * MSG_H + 6;
          return (
            <g key={`lp-${li}`}>
              <rect x={PAD - 6} y={y1} width={totalW - PAD * 2 + 12} height={y2 - y1}
                rx={4} fill="none" stroke="var(--ifm-color-emphasis-300)"
                strokeWidth={1} strokeDasharray="4 2" />
              <rect x={PAD - 6} y={y1} width={lp.label.length * 7 + 16} height={16}
                rx={3} fill="var(--ifm-color-emphasis-200)" />
              <text x={PAD + 2} y={y1 + 11} fontSize="10" fontWeight="600"
                fill="var(--ifm-color-emphasis-600)" fontFamily="var(--ifm-font-family-base)">
                {lp.label}
              </text>
            </g>
          );
        })}

        {/* Messages */}
        {messages.map((msg, mi) => {
          const fi = pIdx.get(msg.from);
          const ti = pIdx.get(msg.to);
          if (fi === undefined || ti === undefined) return null;

          const y = msgStart + mi * MSG_H + MSG_H / 2;
          const x1 = px(fi);
          const x2 = px(ti);
          const isReply = msg.type === 'reply';
          const isSelf = msg.type === 'self' || msg.from === msg.to;

          if (isSelf) {
            const lw = 36, lh = 18;
            return (
              <g key={mi}>
                <path d={`M${x1},${y} L${x1 + lw},${y} L${x1 + lw},${y + lh} L${x1 + 4},${y + lh}`}
                  stroke="var(--ifm-color-emphasis-500)" strokeWidth={1.5}
                  fill="none" markerEnd={`url(#${mkr})`} />
                <text x={x1 + lw + 8} y={y + lh / 2} fontSize="11" dominantBaseline="central"
                  fill="var(--ifm-color-emphasis-700)" fontFamily="var(--ifm-font-family-base)">
                  {msg.label}
                </text>
              </g>
            );
          }

          return (
            <g key={mi}>
              <line x1={x1} y1={y} x2={x2} y2={y}
                stroke={isReply ? 'var(--ifm-color-emphasis-400)' : 'var(--ifm-color-emphasis-600)'}
                strokeWidth={1.5} strokeDasharray={isReply ? '6 3' : undefined}
                markerEnd={`url(#${isReply ? mkrR : mkr})`} />
              <text x={(x1 + x2) / 2} y={y - 8} textAnchor="middle" fontSize="11"
                fill="var(--ifm-color-emphasis-700)" fontFamily="var(--ifm-font-family-base)">
                {msg.label}
              </text>
            </g>
          );
        })}

        {/* Bottom participants */}
        {participants.map((p, i) => renderParticipant(p, i, totalH - BOT))}
      </svg>
    </div>
  );
}
