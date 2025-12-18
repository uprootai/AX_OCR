/**
 * DrawingCanvas - 이미지 위에 바운딩 박스를 그리는 캔버스 컴포넌트
 * Streamlit 스타일의 드래그로 사각형 그리기 기능
 */

import { useState, useRef, useCallback } from 'react';
import { MousePointer2, Square, Trash2, Check } from 'lucide-react';

interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

interface DrawingCanvasProps {
  imageData: string;
  imageSize: { width: number; height: number };
  onBoxDrawn: (box: BoundingBox) => void;
  existingBoxes?: Array<{
    bbox: BoundingBox;
    label?: string;
    color?: string;
  }>;
  selectedClass?: string;
  /** 컨테이너 최대 너비 (예: '66%', '800px') */
  maxWidth?: string;
}

export function DrawingCanvas({
  imageData,
  imageSize,
  onBoxDrawn,
  existingBoxes = [],
  selectedClass,
  maxWidth,
}: DrawingCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [currentPoint, setCurrentPoint] = useState<{ x: number; y: number } | null>(null);
  const [drawnBox, setDrawnBox] = useState<BoundingBox | null>(null);
  const [drawingMode, setDrawingMode] = useState(true);


  // 마우스 좌표를 이미지 좌표로 변환
  const getImageCoordinates = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current) return null;

    const img = containerRef.current.querySelector('img');
    if (!img) return null;

    const imgRect = img.getBoundingClientRect();

    // 이미지가 w-full로 너비에 맞춰 확대되므로 단순 비율 계산
    const scaleX = imageSize.width / imgRect.width;
    const scaleY = imageSize.height / imgRect.height;

    // 마우스 위치에서 이미지 시작점 빼기
    const mouseX = e.clientX - imgRect.left;
    const mouseY = e.clientY - imgRect.top;

    // 이미지 좌표로 변환
    const x = mouseX * scaleX;
    const y = mouseY * scaleY;

    // 범위 제한
    return {
      x: Math.max(0, Math.min(imageSize.width, Math.round(x))),
      y: Math.max(0, Math.min(imageSize.height, Math.round(y))),
    };
  }, [imageSize]);

  // 마우스 다운 - 그리기 시작
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!drawingMode) return;

    const coords = getImageCoordinates(e);
    if (!coords) return;

    setIsDrawing(true);
    setStartPoint(coords);
    setCurrentPoint(coords);
    setDrawnBox(null);
  }, [drawingMode, getImageCoordinates]);

  // 마우스 이동 - 그리기 중
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDrawing || !startPoint) return;

    const coords = getImageCoordinates(e);
    if (!coords) return;

    setCurrentPoint(coords);
  }, [isDrawing, startPoint, getImageCoordinates]);

  // 마우스 업 - 그리기 완료
  const handleMouseUp = useCallback(() => {
    if (!isDrawing || !startPoint || !currentPoint) {
      setIsDrawing(false);
      return;
    }

    // 최소 크기 확인 (10px 이상)
    const width = Math.abs(currentPoint.x - startPoint.x);
    const height = Math.abs(currentPoint.y - startPoint.y);

    if (width > 10 && height > 10) {
      const box: BoundingBox = {
        x1: Math.min(startPoint.x, currentPoint.x),
        y1: Math.min(startPoint.y, currentPoint.y),
        x2: Math.max(startPoint.x, currentPoint.x),
        y2: Math.max(startPoint.y, currentPoint.y),
      };
      setDrawnBox(box);
    }

    setIsDrawing(false);
  }, [isDrawing, startPoint, currentPoint]);

  // 박스 확정
  const handleConfirmBox = useCallback(() => {
    if (drawnBox) {
      onBoxDrawn(drawnBox);
      setDrawnBox(null);
      setStartPoint(null);
      setCurrentPoint(null);
    }
  }, [drawnBox, onBoxDrawn]);

  // 박스 취소
  const handleCancelBox = useCallback(() => {
    setDrawnBox(null);
    setStartPoint(null);
    setCurrentPoint(null);
  }, []);

  // 현재 그리고 있는 박스 계산
  const currentBox = isDrawing && startPoint && currentPoint ? {
    x1: Math.min(startPoint.x, currentPoint.x),
    y1: Math.min(startPoint.y, currentPoint.y),
    x2: Math.max(startPoint.x, currentPoint.x),
    y2: Math.max(startPoint.y, currentPoint.y),
  } : null;

  return (
    <div className={`space-y-4 ${maxWidth ? 'mx-auto' : ''}`} style={maxWidth ? { maxWidth } : undefined}>
      {/* 툴바 */}
      <div className="flex flex-wrap items-center gap-3 bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
        {/* 그리기 모드 버튼 */}
        <button
          onClick={() => setDrawingMode(!drawingMode)}
          className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
            drawingMode
              ? 'bg-primary-600 text-white'
              : 'bg-white dark:bg-gray-600 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-500'
          }`}
        >
          {drawingMode ? (
            <>
              <Square className="w-4 h-4" />
              <span className="text-sm">그리기 모드</span>
            </>
          ) : (
            <>
              <MousePointer2 className="w-4 h-4" />
              <span className="text-sm">보기 모드</span>
            </>
          )}
        </button>

        {selectedClass && (
          <span className="text-sm text-gray-600 dark:text-gray-400">
            선택된 클래스: <strong className="text-primary-600 dark:text-primary-400">{selectedClass}</strong>
          </span>
        )}

        <div className="flex-1 text-right text-xs text-gray-500 dark:text-gray-400">
          {drawingMode ? '이미지 위에서 드래그하여 바운딩 박스를 그리세요' : '보기 모드'}
        </div>
      </div>

      {/* 캔버스 컨테이너 */}
      <div
        ref={containerRef}
        className={`relative bg-gray-100 dark:bg-gray-900 rounded-lg ${
          drawingMode ? 'cursor-crosshair' : 'cursor-default'
        }`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* 이미지 - 컨테이너에 꽉 채움 */}
        <img
          src={imageData}
          alt="도면"
          className="w-full select-none pointer-events-none"
          draggable={false}
        />

        {/* SVG 오버레이 - 이미지와 동일한 크기 (비율 무시하고 늘림) */}
        <svg
          className="absolute top-0 left-0 w-full h-full pointer-events-none"
          viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
          preserveAspectRatio="none"
        >
          {/* 기존 박스들 */}
          {existingBoxes.map((box, idx) => (
            <g key={idx}>
              <rect
                x={box.bbox.x1}
                y={box.bbox.y1}
                width={box.bbox.x2 - box.bbox.x1}
                height={box.bbox.y2 - box.bbox.y1}
                fill={box.color || '#22c55e'}
                fillOpacity={0.25}
                stroke={box.color || '#22c55e'}
                strokeWidth={4}
              />
              {box.label && (
                <text
                  x={box.bbox.x1 + 4}
                  y={box.bbox.y1 - 8}
                  fill={box.color || '#22c55e'}
                  fontSize="16"
                  fontWeight="bold"
                >
                  {box.label}
                </text>
              )}
            </g>
          ))}

          {/* 현재 그리는 중인 박스 */}
          {currentBox && (
            <rect
              x={currentBox.x1}
              y={currentBox.y1}
              width={currentBox.x2 - currentBox.x1}
              height={currentBox.y2 - currentBox.y1}
              fill="#3b82f6"
              fillOpacity={0.2}
              stroke="#3b82f6"
              strokeWidth={2}
              strokeDasharray="5,5"
            />
          )}

          {/* 그려진 박스 (확정 전) */}
          {drawnBox && !isDrawing && (
            <rect
              x={drawnBox.x1}
              y={drawnBox.y1}
              width={drawnBox.x2 - drawnBox.x1}
              height={drawnBox.y2 - drawnBox.y1}
              fill="#f59e0b"
              fillOpacity={0.3}
              stroke="#f59e0b"
              strokeWidth={3}
            />
          )}
        </svg>

        {/* 그리기 완료 시 확인/취소 버튼 */}
        {drawnBox && !isDrawing && (
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex flex-col items-center space-y-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3">
            {!selectedClass && (
              <div className="text-sm text-red-600 dark:text-red-400 font-semibold animate-pulse">
                ⚠️ 먼저 위에서 클래스를 선택하세요!
              </div>
            )}
            <div className="flex items-center space-x-2">
              <div className="text-sm text-gray-700 dark:text-gray-300 px-2">
                ({drawnBox.x1}, {drawnBox.y1}) - ({drawnBox.x2}, {drawnBox.y2})
                <span className="text-xs text-gray-500 ml-2">
                  {drawnBox.x2 - drawnBox.x1}×{drawnBox.y2 - drawnBox.y1}px
                </span>
              </div>
              <button
                onClick={handleConfirmBox}
                disabled={!selectedClass}
                className="flex items-center space-x-1 px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                title={selectedClass ? '이 박스 추가' : '먼저 클래스를 선택하세요'}
              >
                <Check className="w-4 h-4" />
                <span>추가</span>
              </button>
              <button
                onClick={handleCancelBox}
                className="flex items-center space-x-1 px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
              >
                <Trash2 className="w-4 h-4" />
                <span>취소</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 안내 메시지 */}
      {drawingMode && !drawnBox && (
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>사용 방법:</strong> 이미지 위에서 마우스를 클릭한 채로 드래그하여 바운딩 박스를 그리세요.
            그린 후 "추가" 버튼을 클릭하면 수작업 라벨로 추가됩니다.
          </p>
        </div>
      )}

      {drawnBox && !selectedClass && (
        <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3">
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            <strong>주의:</strong> 박스를 추가하려면 먼저 위의 클래스 선택 드롭다운에서 클래스를 선택하세요.
          </p>
        </div>
      )}
    </div>
  );
}
