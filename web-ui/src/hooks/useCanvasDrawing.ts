/**
 * useCanvasDrawing Hook
 *
 * Canvas에 이미지와 오버레이를 그리는 공통 로직
 * YOLOVisualization, OCRVisualization 등에서 사용
 */

import { useEffect, useRef, useCallback, useState } from 'react';

export interface CanvasDrawingOptions {
  /** 이미지 파일 또는 base64 */
  imageSource: File | string | null;
  /** 캔버스 렌더링 활성화 여부 */
  enabled?: boolean;
  /** 이미지 로드 완료 콜백 */
  onImageLoad?: (img: HTMLImageElement, ctx: CanvasRenderingContext2D) => void;
  /** 커스텀 드로잉 함수 */
  drawOverlay?: (ctx: CanvasRenderingContext2D, img: HTMLImageElement, scaleFactor: number) => void;
}

export interface CanvasDrawingResult {
  /** 캔버스 ref */
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  /** 이미지 크기 */
  imageSize: { width: number; height: number } | null;
  /** 스케일 팩터 */
  scaleFactor: number;
  /** 로딩 상태 */
  isLoading: boolean;
  /** 에러 */
  error: string | null;
  /** 수동 다시 그리기 */
  redraw: () => void;
}

/**
 * 스케일 팩터 계산
 * 1000px 기준으로 1-4 범위
 */
export function calculateScaleFactor(width: number, height: number): number {
  return Math.max(1, Math.min(4, Math.max(width, height) / 1000));
}

/**
 * 라벨 오버랩 체크 유틸리티
 */
export function createLabelOverlapChecker() {
  const usedPositions: Array<{ x: number; y: number; width: number; height: number }> = [];

  return {
    checkOverlap: (x: number, y: number, width: number, height: number): boolean => {
      return usedPositions.some(
        (used) =>
          !(
            x + width < used.x ||
            x > used.x + used.width ||
            y + height < used.y ||
            y > used.y + used.height
          )
      );
    },
    addPosition: (x: number, y: number, width: number, height: number) => {
      usedPositions.push({ x, y, width, height });
    },
    clear: () => {
      usedPositions.length = 0;
    },
  };
}

/**
 * Canvas 드로잉 훅
 */
export function useCanvasDrawing({
  imageSource,
  enabled = true,
  onImageLoad,
  drawOverlay,
}: CanvasDrawingOptions): CanvasDrawingResult {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [scaleFactor, setScaleFactor] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 이미지 로드 및 그리기
  const draw = useCallback(() => {
    if (!enabled || !imageSource) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsLoading(true);
    setError(null);

    const img = new Image();

    // 이미지 소스 결정
    let url: string;
    let shouldRevoke = false;

    if (typeof imageSource === 'string') {
      // base64 또는 URL
      url = imageSource.startsWith('data:') || imageSource.startsWith('http')
        ? imageSource
        : `data:image/png;base64,${imageSource}`;
    } else {
      // File 객체
      url = URL.createObjectURL(imageSource);
      shouldRevoke = true;
    }

    img.onload = () => {
      // 캔버스 크기 설정
      canvas.width = img.width;
      canvas.height = img.height;

      // 이미지 그리기
      ctx.drawImage(img, 0, 0);

      // 스케일 팩터 계산
      const scale = calculateScaleFactor(img.width, img.height);
      setScaleFactor(scale);
      setImageSize({ width: img.width, height: img.height });

      // 콜백 호출
      onImageLoad?.(img, ctx);

      // 커스텀 오버레이 그리기
      drawOverlay?.(ctx, img, scale);

      setIsLoading(false);

      // URL 정리
      if (shouldRevoke) {
        URL.revokeObjectURL(url);
      }
    };

    img.onerror = () => {
      setError('이미지 로드 실패');
      setIsLoading(false);
      if (shouldRevoke) {
        URL.revokeObjectURL(url);
      }
    };

    img.src = url;
  }, [imageSource, enabled, onImageLoad, drawOverlay]);

  // 이미지 소스 변경 시 다시 그리기
  useEffect(() => {
    draw();
  }, [draw]);

  return {
    canvasRef,
    imageSize,
    scaleFactor,
    isLoading,
    error,
    redraw: draw,
  };
}

/**
 * 바운딩 박스 그리기 유틸리티
 */
export function drawBoundingBox(
  ctx: CanvasRenderingContext2D,
  bbox: { x: number; y: number; width: number; height: number },
  options: {
    color?: string;
    lineWidth?: number;
    label?: string;
    confidence?: number;
    fontSize?: number;
    padding?: number;
  } = {}
) {
  const {
    color = '#3b82f6',
    lineWidth = 2,
    label,
    confidence,
    fontSize = 12,
    padding = 3,
  } = options;

  const { x, y, width, height } = bbox;

  // 박스 그리기
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.strokeRect(x, y, width, height);

  // 라벨 그리기
  if (label) {
    const labelText = confidence !== undefined
      ? `${label} (${(confidence * 100).toFixed(1)}%)`
      : label;

    ctx.font = `bold ${fontSize}px Pretendard, Arial, sans-serif`;
    const textMetrics = ctx.measureText(labelText);
    const labelWidth = textMetrics.width + padding * 2;
    const labelHeight = fontSize + padding * 2;
    const labelY = Math.max(0, y - labelHeight - 2);

    // 라벨 배경
    ctx.fillStyle = color;
    ctx.fillRect(x, labelY, labelWidth, labelHeight);

    // 라벨 텍스트
    ctx.fillStyle = 'white';
    ctx.fillText(labelText, x + padding, labelY + fontSize + padding / 2);
  }
}

export default useCanvasDrawing;
