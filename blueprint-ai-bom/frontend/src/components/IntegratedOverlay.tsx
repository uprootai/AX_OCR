/**
 * IntegratedOverlay - 통합 시각화 컴포넌트
 * 심볼, 선, 치수, 텍스트, 마스크, 폴리곤을 한 화면에 레이어로 표시하고 제어
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import type { Detection, MaskRLE } from '../types';

/**
 * RLE (Run-Length Encoding) 마스크 디코딩
 * Detectron2 COCO RLE 형식을 이진 마스크로 변환
 */
function decodeRLE(rle: MaskRLE): Uint8Array {
    const [height, width] = rle.size;
    const mask = new Uint8Array(height * width);

    let position = 0;
    let value = 0; // 0으로 시작 (COCO RLE 형식)

    for (const count of rle.counts) {
        for (let i = 0; i < count; i++) {
            if (position < mask.length) {
                mask[position++] = value;
            }
        }
        value = 1 - value; // 0과 1을 번갈아 설정
    }

    return mask;
}

/**
 * Canvas에 마스크 렌더링
 */
function renderMaskToCanvas(
    ctx: CanvasRenderingContext2D,
    mask: MaskRLE,
    color: string,
    opacity: number = 0.4
) {
    const [height, width] = mask.size;
    const decoded = decodeRLE(mask);

    // 색상 파싱 (hex to RGB)
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    const a = Math.round(opacity * 255);

    const imageData = ctx.createImageData(width, height);

    for (let i = 0; i < decoded.length; i++) {
        if (decoded[i] === 1) {
            const idx = i * 4;
            imageData.data[idx] = r;
            imageData.data[idx + 1] = g;
            imageData.data[idx + 2] = b;
            imageData.data[idx + 3] = a;
        }
    }

    ctx.putImageData(imageData, 0, 0);
}

interface Point {
    x: number;
    y: number;
}

interface Dimension {
    id: string;
    bbox: { x1: number; y1: number; x2: number; y2: number };
    value: string;
    modified_value: string | null;
    text?: string; // OCR raw text
    verification_status: string;
}

interface Line {
    id: string;
    start: Point;
    end: Point;
    line_type: string;
    line_style: string;
    color?: string;
    thickness?: number;
}

interface Intersection {
    id: string;
    point: Point;
}

interface Link {
    dimension_id: string;
    symbol_id: string;
}

interface IntegratedOverlayProps {
    imageData: string;
    imageSize: { width: number; height: number };
    detections?: Detection[];
    lines?: Line[];
    dimensions?: Dimension[];
    intersections?: Intersection[];
    links?: Link[];
    maxWidth?: string | number;
    maxHeight?: string | number;
}

// 레이어 가시성 상태
interface LayerVisibility {
    symbols: boolean;
    lines: boolean;
    dimensions: boolean;
    links: boolean;
    labels: boolean;
    masks: boolean;      // Detectron2 마스크
    polygons: boolean;   // Detectron2 폴리곤
}

export function IntegratedOverlay({
    imageData,
    imageSize,
    detections = [],
    lines = [],
    dimensions = [],
    intersections = [],
    links = [],
    maxWidth = '100%',
    maxHeight,
}: IntegratedOverlayProps) {
    const [visibility, setVisibility] = useState<LayerVisibility>({
        symbols: true,
        lines: true,
        dimensions: true,
        links: true,
        labels: true,
        masks: true,      // Detectron2 마스크
        polygons: true,   // Detectron2 폴리곤
    });

    // Canvas refs for mask rendering
    const maskCanvasRef = useRef<HTMLCanvasElement>(null);

    // Detectron2 데이터 확인
    const hasPolygons = detections.some(d => d.polygons && d.polygons.length > 0);
    const hasMasks = detections.some(d => d.mask && d.mask.counts && d.mask.counts.length > 0);

    // 마스크 색상 (클래스별 고유 색상)
    const getMaskColor = useCallback((index: number): string => {
        const colors = [
            '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e',
            '#14b8a6', '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6',
            '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
        ];
        return colors[index % colors.length];
    }, []);

    // 폴리곤 좌표를 SVG points 문자열로 변환
    const polygonToPoints = useCallback((polygon: number[][]): string => {
        return polygon.map(([x, y]) => `${x},${y}`).join(' ');
    }, []);

    // 마스크 렌더링 (Canvas)
    useEffect(() => {
        if (!visibility.masks || !hasMasks || !maskCanvasRef.current) return;

        const canvas = maskCanvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Canvas 크기 설정
        canvas.width = imageSize.width;
        canvas.height = imageSize.height;

        // 기존 내용 지우기
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 각 검출의 마스크 렌더링
        detections.forEach((det, idx) => {
            if (det.mask && det.mask.counts && det.mask.counts.length > 0) {
                const color = getMaskColor(idx);
                renderMaskToCanvas(ctx, det.mask, color, 0.4);
            }
        });
    }, [visibility.masks, hasMasks, detections, imageSize, getMaskColor]);



    // 컨테이너 크기 측정 (간단히 window resize나 mount 시 계산)
    // 실제로는 ResizeObserver가 좋지만 여기서는 props나 기본값 의존

    // 색상 상수
    const COLORS = {
        symbol: '#ef4444',     // Red
        line: '#3b82f6',       // Blue
        dimension: '#22c55e',  // Green
        link: '#a855f7',       // Purple
    };

    const LINE_TYPE_COLORS: Record<string, string> = {
        process: '#3b82f6',      // blue
        cooling: '#06b6d4',      // cyan
        steam: '#f97316',        // orange
        signal: '#8b5cf6',       // purple
        electrical: '#f59e0b',   // amber
        dimension: '#22c55e',    // green
        extension: '#84cc16',    // lime
        leader: '#14b8a6',       // teal
        unknown: '#6b7280',      // gray
    };

    const toggleLayer = (layer: keyof LayerVisibility) => {
        setVisibility(prev => ({ ...prev, [layer]: !prev[layer] }));
    };

    return (
        <div className="relative group bg-gray-100 dark:bg-gray-900 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700"
            style={{ maxWidth, maxHeight: maxHeight || 'auto' }}>

            {/* 툴바 (오른쪽 상단) */}
            <div className="absolute top-4 right-4 z-20 flex flex-col gap-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-2 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 transition-opacity opacity-0 group-hover:opacity-100">
                <div className="text-xs font-semibold text-gray-500 mb-1 px-2">레이어</div>

                <button
                    onClick={() => toggleLayer('symbols')}
                    className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs ${visibility.symbols ? 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                >
                    <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-red-500"></span>
                        심볼 ({detections.length})
                    </span>
                    {visibility.symbols ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>

                <button
                    onClick={() => toggleLayer('lines')}
                    className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs ${visibility.lines ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                >
                    <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                        선 ({lines.length})
                    </span>
                    {visibility.lines ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>

                <button
                    onClick={() => toggleLayer('dimensions')}
                    className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs ${visibility.dimensions ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                >
                    <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                        치수 ({dimensions.length})
                    </span>
                    {visibility.dimensions ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>

                <button
                    onClick={() => toggleLayer('links')}
                    className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs ${visibility.links ? 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                    disabled={links.length === 0}
                >
                    <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                        연결 ({links.length})
                    </span>
                    {visibility.links ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>

                {/* Detectron2 마스크/폴리곤 토글 */}
                {(hasPolygons || hasMasks) && (
                    <>
                        <div className="h-px bg-gray-200 dark:bg-gray-700 my-1"></div>
                        <div className="text-xs font-semibold text-gray-500 px-2">Detectron2</div>

                        {hasMasks && (
                            <button
                                onClick={() => toggleLayer('masks')}
                                className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs ${visibility.masks ? 'bg-pink-50 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }`}
                            >
                                <span className="flex items-center gap-1.5">
                                    <span className="w-2 h-2 rounded-full bg-pink-500"></span>
                                    마스크
                                </span>
                                {visibility.masks ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                            </button>
                        )}

                        {hasPolygons && (
                            <button
                                onClick={() => toggleLayer('polygons')}
                                className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs ${visibility.polygons ? 'bg-cyan-50 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }`}
                            >
                                <span className="flex items-center gap-1.5">
                                    <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                                    폴리곤
                                </span>
                                {visibility.polygons ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                            </button>
                        )}
                    </>
                )}

                <div className="h-px bg-gray-200 dark:bg-gray-700 my-1"></div>

                <button
                    onClick={() => toggleLayer('labels')}
                    className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs ${visibility.labels ? 'text-gray-900 dark:text-white bg-gray-100 dark:bg-gray-700' : 'text-gray-500'
                        }`}
                >
                    <span>텍스트 라벨</span>
                    {visibility.labels ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>
            </div>

            {/* 메인 뷰포트 (이미지 + Canvas + SVG 오버레이) */}
            <div className="relative w-full h-full">
                {/* 이미지 */}
                <img
                    src={imageData}
                    alt="Blueprint"
                    className="w-full h-auto block select-none"
                    draggable={false}
                />

                {/* Canvas 레이어 (Detectron2 마스크) */}
                {hasMasks && visibility.masks && (
                    <canvas
                        ref={maskCanvasRef}
                        className="absolute top-0 left-0 w-full h-full pointer-events-none"
                        style={{ mixBlendMode: 'multiply' }}
                    />
                )}

                {/* SVG 레이어 */}
                <svg
                    className="absolute top-0 left-0 w-full h-full pointer-events-none"
                    viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                >
                    {/* A. 연결선 (Links) - 가장 아래 */}
                    {visibility.links && links.map((link, idx) => {
                        const dim = dimensions.find(d => d.id === link.dimension_id);
                        const sym = detections.find(d => d.id === link.symbol_id);
                        if (!dim || !sym) return null;

                        // 치수 중심
                        const dimCx = (dim.bbox.x1 + dim.bbox.x2) / 2;
                        const dimCy = (dim.bbox.y1 + dim.bbox.y2) / 2;
                        // 심볼 중심
                        const symCx = (sym.bbox.x1 + sym.bbox.x2) / 2;
                        const symCy = (sym.bbox.y1 + sym.bbox.y2) / 2;

                        return (
                            <line
                                key={`link-${idx}`}
                                x1={dimCx}
                                y1={dimCy}
                                x2={symCx}
                                y2={symCy}
                                stroke={COLORS.link}
                                strokeWidth={2}
                                strokeDasharray="4,4"
                                opacity={0.6}
                            />
                        );
                    })}

                    {/* B. 선 (Lines) */}
                    {visibility.lines && lines.map((line) => (
                        <line
                            key={`line-${line.id}`}
                            x1={line.start.x}
                            y1={line.start.y}
                            x2={line.end.x}
                            y2={line.end.y}
                            stroke={LINE_TYPE_COLORS[line.line_type] || LINE_TYPE_COLORS.unknown}
                            strokeWidth={line.thickness || 2}
                            opacity={0.8}
                        />
                    ))}

                    {/* C. 폴리곤 (Detectron2 Polygons) - 심볼 아래 */}
                    {visibility.polygons && hasPolygons && detections.map((det, idx) => (
                        det.polygons && det.polygons.length > 0 && (
                            <g key={`poly-${det.id}`}>
                                {det.polygons.map((polygon, polyIdx) => (
                                    <polygon
                                        key={`poly-${det.id}-${polyIdx}`}
                                        points={polygonToPoints(polygon)}
                                        fill={getMaskColor(idx)}
                                        fillOpacity={0.25}
                                        stroke={getMaskColor(idx)}
                                        strokeWidth={2}
                                        strokeLinejoin="round"
                                    />
                                ))}
                            </g>
                        )
                    ))}

                    {/* D. 심볼 (Symbols) */}
                    {visibility.symbols && detections.map((det, idx) => (
                        <g key={`sym-${det.id}`}>
                            <rect
                                x={det.bbox.x1}
                                y={det.bbox.y1}
                                width={det.bbox.x2 - det.bbox.x1}
                                height={det.bbox.y2 - det.bbox.y1}
                                fill="none"
                                stroke={det.polygons && det.polygons.length > 0 ? getMaskColor(idx) : COLORS.symbol}
                                strokeWidth={2}
                            />
                            {visibility.labels && (
                                <text
                                    x={det.bbox.x1}
                                    y={det.bbox.y1 - 5}
                                    fill={det.polygons && det.polygons.length > 0 ? getMaskColor(idx) : COLORS.symbol}
                                    fontSize={14}
                                    fontWeight="bold"
                                >
                                    {det.modified_class_name || det.class_name}
                                </text>
                            )}
                        </g>
                    ))}

                    {/* D. 치수 (Dimensions) */}
                    {visibility.dimensions && dimensions.map((dim) => (
                        <g key={`dim-${dim.id}`}>
                            <rect
                                x={dim.bbox.x1}
                                y={dim.bbox.y1}
                                width={dim.bbox.x2 - dim.bbox.x1}
                                height={dim.bbox.y2 - dim.bbox.y1}
                                fill={COLORS.dimension}
                                fillOpacity={0.1}
                                stroke={COLORS.dimension}
                                strokeWidth={1}
                                strokeDasharray="2,2"
                            />
                            {visibility.labels && (
                                <text
                                    x={(dim.bbox.x1 + dim.bbox.x2) / 2}
                                    y={(dim.bbox.y1 + dim.bbox.y2) / 2}
                                    fill={COLORS.dimension}
                                    fontSize={12}
                                    textAnchor="middle"
                                    dominantBaseline="middle"
                                    fontWeight="bold"
                                    style={{ textShadow: '0 0 2px white' }}
                                >
                                    {dim.modified_value || dim.value}
                                </text>
                            )}
                        </g>
                    ))}

                    {/* E. 교차점 (Intersections) */}
                    {visibility.lines && intersections.map(inte => (
                        <circle
                            key={`int-${inte.id}`}
                            cx={inte.point.x}
                            cy={inte.point.y}
                            r={3}
                            fill="red"
                        />
                    ))}
                </svg>
            </div>
        </div>
    );
}
