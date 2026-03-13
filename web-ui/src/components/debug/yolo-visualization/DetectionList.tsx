import { Button } from '../../ui/Button';
import { CLASS_DETAILS } from './types';
import type { BoundingBox } from './types';

interface DetectionListProps {
  filteredBoundingBoxes: BoundingBox[];
  totalDetections: number;
  filteredDetections: number;
  selectedDetection: number | null;
  onSymbolSelect?: (detection: BoundingBox | null, index: number | null) => void;
  onSymbolClick: (index: number) => void;
}

export function DetectionList({
  filteredBoundingBoxes,
  totalDetections,
  filteredDetections,
  selectedDetection,
  onSymbolSelect,
  onSymbolClick,
}: DetectionListProps) {
  const countLabel = filteredDetections === totalDetections
    ? `${totalDetections}개`
    : `${filteredDetections}/${totalDetections}개`;

  return (
    <>
      {/* Selected Detection Panel */}
      {selectedDetection !== null && filteredBoundingBoxes[selectedDetection] && (
        <div className="p-4 bg-primary/10 border border-primary/30 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-primary">선택된 객체</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSymbolClick(selectedDetection)}
              className="h-6 px-2"
            >
              선택 해제
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">클래스:</span>
              <span className="ml-2 font-medium">
                {CLASS_DETAILS[filteredBoundingBoxes[selectedDetection].className]?.korean ||
                  filteredBoundingBoxes[selectedDetection].className}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">신뢰도:</span>
              <span className="ml-2 font-medium">
                {(filteredBoundingBoxes[selectedDetection].confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">위치:</span>
              <span className="ml-2 font-mono text-xs">
                ({Math.round(filteredBoundingBoxes[selectedDetection].x)},
                {Math.round(filteredBoundingBoxes[selectedDetection].y)})
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">크기:</span>
              <span className="ml-2 font-mono text-xs">
                {Math.round(filteredBoundingBoxes[selectedDetection].width)}×
                {Math.round(filteredBoundingBoxes[selectedDetection].height)}
              </span>
            </div>
            {filteredBoundingBoxes[selectedDetection].extractedText && (
              <div className="col-span-2">
                <span className="text-muted-foreground">추출 텍스트:</span>
                <span className="ml-2 font-mono bg-accent/50 px-2 py-0.5 rounded">
                  {filteredBoundingBoxes[selectedDetection].extractedText}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Details List */}
      <div className="space-y-2">
        <h4 className="font-medium">
          검출된 객체 상세 ({countLabel})
          {onSymbolSelect && (
            <span className="text-xs text-muted-foreground ml-2">(클릭하여 선택)</span>
          )}
        </h4>
        <div className="max-h-64 overflow-y-auto space-y-1 text-sm">
          {filteredBoundingBoxes.map((box, index) => (
            <div
              key={index}
              onClick={() => onSymbolClick(index)}
              className={`flex items-center gap-2 p-2 rounded transition-colors cursor-pointer ${
                selectedDetection === index
                  ? 'bg-primary/20 border-2 border-primary'
                  : 'bg-accent/50 hover:bg-accent border-2 border-transparent'
              }`}
            >
              <div
                className="w-3 h-3 rounded flex-shrink-0"
                style={{ backgroundColor: box.color }}
              />
              <div className="flex-1">
                <span className="font-medium">{box.label}</span>
                {box.extractedText && (
                  <div className="text-xs text-muted-foreground mt-0.5">
                    텍스트: "{box.extractedText}"
                  </div>
                )}
              </div>
              <span className="text-muted-foreground text-xs whitespace-nowrap">
                위치: ({Math.round(box.x)}, {Math.round(box.y)})
              </span>
              <span className="text-muted-foreground text-xs whitespace-nowrap">
                크기: {Math.round(box.width)}×{Math.round(box.height)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
