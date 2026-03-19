/**
 * GroundTruthEditor — 도면 위에 드래그로 OD/ID/W bbox 그리기 + 값 입력
 *
 * SVG mousedown/move/up → 사각형 드래그 → 역할 선택 + 값 입력
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { Trash2, Save } from 'lucide-react';
import { sessionApi, analysisApi } from '../../lib/api';
import type { GtAnnotation, GtRole } from './types';
import { ROLE_COLORS, ROLE_LABELS } from './types';

interface Props {
  sessionId: string;
  annotations: GtAnnotation[];
  onChange: (anns: GtAnnotation[]) => void;
  onSaved: () => void;
}

export function GroundTruthEditor({ sessionId, annotations, onChange, onSaved }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 });
  const [scale, setScale] = useState(1);
  const [drawing, setDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<{ x: number; y: number } | null>(null);
  const [drawEnd, setDrawEnd] = useState<{ x: number; y: number } | null>(null);
  const [activeRole, setActiveRole] = useState<GtRole>('od');
  const [pendingValue, setPendingValue] = useState('');
  const [showValueInput, setShowValueInput] = useState(false);
  const [pendingBbox, setPendingBbox] = useState<GtAnnotation['bbox'] | null>(null);
  const [saving, setSaving] = useState(false);

  // 이미지 로드
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    sessionApi.getImage(sessionId).then(({ image_base64, mime_type }) => {
      if (!cancelled) setImageUrl(`data:${mime_type};base64,${image_base64}`);
    });
    return () => { cancelled = true; };
  }, [sessionId]);

  // 이미지 크기 측정
  const handleImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImgSize({ w: img.naturalWidth, h: img.naturalHeight });
  }, []);

  // 스케일 관찰
  useEffect(() => {
    if (!containerRef.current || !imgSize.w) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) setScale(entry.contentRect.width / imgSize.w);
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [imgSize.w]);

  // SVG 좌표 변환
  const toImgCoords = useCallback((clientX: number, clientY: number) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const rect = containerRef.current.getBoundingClientRect();
    return {
      x: Math.round((clientX - rect.left) / scale),
      y: Math.round((clientY - rect.top) / scale),
    };
  }, [scale]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (showValueInput) return;
    const pt = toImgCoords(e.clientX, e.clientY);
    setDrawing(true);
    setDrawStart(pt);
    setDrawEnd(pt);
  }, [toImgCoords, showValueInput]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!drawing) return;
    setDrawEnd(toImgCoords(e.clientX, e.clientY));
  }, [drawing, toImgCoords]);

  const handleMouseUp = useCallback(() => {
    if (!drawing || !drawStart || !drawEnd) return;
    setDrawing(false);

    const x1 = Math.min(drawStart.x, drawEnd.x);
    const y1 = Math.min(drawStart.y, drawEnd.y);
    const x2 = Math.max(drawStart.x, drawEnd.x);
    const y2 = Math.max(drawStart.y, drawEnd.y);

    // 최소 크기 필터 (너무 작은 드래그 무시)
    if (x2 - x1 < 10 || y2 - y1 < 10) {
      setDrawStart(null);
      setDrawEnd(null);
      return;
    }

    setPendingBbox({ x1, y1, x2, y2 });
    setShowValueInput(true);
    setPendingValue('');
  }, [drawing, drawStart, drawEnd]);

  const handleConfirmValue = useCallback(() => {
    if (!pendingBbox || !pendingValue.trim()) return;
    const newAnn: GtAnnotation = {
      role: activeRole,
      value: pendingValue.trim(),
      bbox: pendingBbox,
    };
    onChange([...annotations, newAnn]);
    setShowValueInput(false);
    setPendingBbox(null);
    setDrawStart(null);
    setDrawEnd(null);
  }, [pendingBbox, pendingValue, activeRole, annotations, onChange]);

  const handleCancelValue = useCallback(() => {
    setShowValueInput(false);
    setPendingBbox(null);
    setDrawStart(null);
    setDrawEnd(null);
  }, []);

  const handleDelete = useCallback((idx: number) => {
    onChange(annotations.filter((_, i) => i !== idx));
  }, [annotations, onChange]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await analysisApi.saveGroundTruth(sessionId, annotations);
      onSaved();
    } finally {
      setSaving(false);
    }
  }, [sessionId, annotations, onSaved]);

  const scaledHeight = imgSize.h * scale;

  return (
    <div className="space-y-4">
      {/* 도구바 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">역할 선택:</span>
          {(['od', 'id', 'w'] as GtRole[]).map((role) => (
            <button
              key={role}
              onClick={() => setActiveRole(role)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border-2 transition ${
                activeRole === role
                  ? 'text-white'
                  : 'bg-transparent hover:opacity-80'
              }`}
              style={{
                borderColor: ROLE_COLORS[role],
                backgroundColor: activeRole === role ? ROLE_COLORS[role] : 'transparent',
                color: activeRole === role ? 'white' : ROLE_COLORS[role],
              }}
            >
              {ROLE_LABELS[role]}
            </button>
          ))}

          <div className="flex-1" />

          <span className="text-xs text-gray-400">
            {annotations.length}개 어노테이션
          </span>

          <button
            onClick={handleSave}
            disabled={saving || annotations.length === 0}
            className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5"
          >
            <Save className="w-4 h-4" />
            {saving ? '저장 중...' : '저장'}
          </button>
        </div>

        <p className="mt-2 text-xs text-gray-400">
          도면 위에 드래그하여 {ROLE_LABELS[activeRole]} 영역을 선택하세요. 선택 후 치수 값을 입력합니다.
        </p>
      </div>

      {/* 이미지 + 오버레이 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div
          ref={containerRef}
          className="relative w-full overflow-auto border border-gray-200 dark:border-gray-700 rounded-lg select-none"
          style={{ cursor: showValueInput ? 'default' : 'crosshair' }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => { if (drawing) { setDrawing(false); setDrawStart(null); setDrawEnd(null); } }}
        >
          {imageUrl ? (
            <div className="relative" style={{ width: '100%', height: scaledHeight || 'auto' }}>
              <img
                src={imageUrl}
                alt="Drawing"
                className="w-full h-auto"
                style={{ display: 'block', pointerEvents: 'none' }}
                onLoad={handleImageLoad}
              />
              <svg
                className="absolute top-0 left-0 w-full"
                style={{ height: scaledHeight }}
                viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
                preserveAspectRatio="xMinYMin meet"
              >
                {/* 기존 어노테이션 */}
                {annotations.map((ann, idx) => (
                  <g key={idx}>
                    <rect
                      x={ann.bbox.x1} y={ann.bbox.y1}
                      width={ann.bbox.x2 - ann.bbox.x1}
                      height={ann.bbox.y2 - ann.bbox.y1}
                      fill={ROLE_COLORS[ann.role]}
                      fillOpacity={0.15}
                      stroke={ROLE_COLORS[ann.role]}
                      strokeWidth={3}
                      rx={4}
                    />
                    {/* 라벨 */}
                    <rect
                      x={ann.bbox.x1} y={ann.bbox.y1 - 24}
                      width={Math.max(80, ann.value.length * 10 + 50)}
                      height={22}
                      fill={ROLE_COLORS[ann.role]}
                      rx={4}
                    />
                    <text
                      x={ann.bbox.x1 + 4} y={ann.bbox.y1 - 8}
                      fill="white" fontSize={13} fontWeight="bold"
                    >
                      {ann.role.toUpperCase()}: {ann.value}
                    </text>
                  </g>
                ))}

                {/* 현재 드래그 중인 사각형 */}
                {drawing && drawStart && drawEnd && (
                  <rect
                    x={Math.min(drawStart.x, drawEnd.x)}
                    y={Math.min(drawStart.y, drawEnd.y)}
                    width={Math.abs(drawEnd.x - drawStart.x)}
                    height={Math.abs(drawEnd.y - drawStart.y)}
                    fill={ROLE_COLORS[activeRole]}
                    fillOpacity={0.2}
                    stroke={ROLE_COLORS[activeRole]}
                    strokeWidth={2}
                    strokeDasharray="6,3"
                  />
                )}

                {/* 확정 대기 중인 bbox */}
                {showValueInput && pendingBbox && (
                  <rect
                    x={pendingBbox.x1} y={pendingBbox.y1}
                    width={pendingBbox.x2 - pendingBbox.x1}
                    height={pendingBbox.y2 - pendingBbox.y1}
                    fill={ROLE_COLORS[activeRole]}
                    fillOpacity={0.25}
                    stroke={ROLE_COLORS[activeRole]}
                    strokeWidth={3}
                    strokeDasharray="8,4"
                  />
                )}
              </svg>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">이미지 로딩...</div>
          )}

          {/* 값 입력 모달 */}
          {showValueInput && pendingBbox && (
            <div
              className="absolute bg-white dark:bg-gray-800 rounded-lg shadow-xl border-2 p-3 z-10"
              style={{
                left: Math.min(pendingBbox.x1 * scale, (containerRef.current?.clientWidth || 400) - 220),
                top: Math.max(pendingBbox.y2 * scale + 8, 0),
                borderColor: ROLE_COLORS[activeRole],
              }}
              onClick={(e) => e.stopPropagation()}
              onMouseDown={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="px-2 py-0.5 rounded text-xs font-bold text-white"
                  style={{ backgroundColor: ROLE_COLORS[activeRole] }}
                >
                  {activeRole.toUpperCase()}
                </span>
                <span className="text-xs text-gray-500">치수 값 입력</span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  autoFocus
                  type="text"
                  value={pendingValue}
                  onChange={(e) => setPendingValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleConfirmValue();
                    if (e.key === 'Escape') handleCancelValue();
                  }}
                  placeholder="예: 150"
                  className="w-24 px-2 py-1 border rounded text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <button
                  onClick={handleConfirmValue}
                  disabled={!pendingValue.trim()}
                  className="px-2 py-1 bg-blue-600 text-white rounded text-xs disabled:opacity-50"
                >
                  확인
                </button>
                <button onClick={handleCancelValue} className="px-2 py-1 text-gray-500 hover:text-gray-700 text-xs">
                  취소
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 어노테이션 목록 */}
      {annotations.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Ground Truth 어노테이션</h3>
          <div className="space-y-1.5">
            {annotations.map((ann, idx) => (
              <div key={idx} className="flex items-center gap-3 text-sm">
                <span
                  className="px-2 py-0.5 rounded text-xs font-bold text-white min-w-[36px] text-center"
                  style={{ backgroundColor: ROLE_COLORS[ann.role] }}
                >
                  {ann.role.toUpperCase()}
                </span>
                <span className="font-mono text-gray-900 dark:text-white">{ann.value}</span>
                <span className="text-xs text-gray-400">
                  ({ann.bbox.x1}, {ann.bbox.y1}) → ({ann.bbox.x2}, {ann.bbox.y2})
                </span>
                <button
                  onClick={() => handleDelete(idx)}
                  className="ml-auto text-gray-400 hover:text-red-500 transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
