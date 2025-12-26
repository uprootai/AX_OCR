/**
 * ImageModal - 이미지 확대 모달
 * 도면 이미지를 크게 보여주는 모달 컴포넌트
 */

import { useEffect, useRef } from 'react';
import type { Detection } from '../../../types';

interface ImageModalProps {
  imageData: string;
  imageSize: { width: number; height: number };
  detections: Detection[];
  onClose: () => void;
}

export function ImageModal({
  imageData,
  imageSize,
  detections,
  onClose,
}: ImageModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      // Full size with max viewport constraints
      const maxWidth = window.innerWidth * 0.9;
      const maxHeight = window.innerHeight * 0.85;
      const scaleW = maxWidth / imageSize.width;
      const scaleH = maxHeight / imageSize.height;
      const scale = Math.min(1, scaleW, scaleH);

      canvas.width = imageSize.width * scale;
      canvas.height = imageSize.height * scale;

      // Draw image
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Draw bounding boxes for approved/modified/manual detections
      const finalDetections = detections.filter(d =>
        d.verification_status === 'approved' ||
        d.verification_status === 'modified' ||
        d.verification_status === 'manual'
      );

      finalDetections.forEach((detection, idx) => {
        const { x1, y1, x2, y2 } = detection.bbox;
        const sx1 = x1 * scale;
        const sy1 = y1 * scale;
        const sx2 = x2 * scale;
        const sy2 = y2 * scale;

        // Determine color based on status
        let color = '#22c55e'; // green for approved
        if (detection.modified_class_name && detection.modified_class_name !== detection.class_name) {
          color = '#f97316'; // orange for modified
        } else if (detection.verification_status === 'manual') {
          color = '#a855f7'; // purple for manual
        }

        // Draw box
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

        // Draw label
        const className = detection.modified_class_name || detection.class_name;
        const label = `${idx + 1}. ${className}`;
        ctx.font = 'bold 14px sans-serif';
        const textWidth = ctx.measureText(label).width;
        ctx.fillStyle = color;
        ctx.fillRect(sx1, sy1 - 22, textWidth + 10, 22);
        ctx.fillStyle = 'white';
        ctx.fillText(label, sx1 + 5, sy1 - 6);
      });
    };
    img.src = imageData;
  }, [imageData, imageSize, detections]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={onClose}
    >
      <div className="relative max-w-[95vw] max-h-[95vh]" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={onClose}
          className="absolute -top-10 right-0 text-white hover:text-gray-300 text-xl"
        >
          ✕ 닫기
        </button>
        <canvas
          ref={canvasRef}
          className="rounded-lg shadow-2xl"
        />
      </div>
    </div>
  );
}
