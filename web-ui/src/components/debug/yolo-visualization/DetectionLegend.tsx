import { CLASS_CATEGORIES, CLASS_COLORS, CLASS_DETAILS } from './types';

interface DetectionLegendProps {
  filteredClassCounts: Record<string, number>;
}

export function DetectionLegend({ filteredClassCounts }: DetectionLegendProps) {
  if (Object.keys(filteredClassCounts).length === 0) return null;

  return (
    <div className="space-y-3 p-4 bg-accent/30 rounded-lg border">
      <h4 className="font-semibold text-sm">검출 클래스 범례</h4>

      {/* Dimensions Category */}
      {CLASS_CATEGORIES.dimensions.some(cls => filteredClassCounts[cls]) && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">📏 치수 (Dimensions)</p>
          <div className="grid grid-cols-2 gap-2">
            {CLASS_CATEGORIES.dimensions.map((className) => {
              const count = filteredClassCounts[className];
              if (!count) return null;
              const details = CLASS_DETAILS[className];
              return (
                <div key={className} className="flex items-center gap-2 text-xs">
                  <div
                    className="w-4 h-4 rounded flex-shrink-0"
                    style={{ backgroundColor: CLASS_COLORS[className] }}
                  />
                  <span className="flex-1">
                    <span className="font-medium">{details.korean}</span>
                    <span className="text-muted-foreground"> ({details.english}, {details.abbr})</span>
                    <span className="text-blue-600 ml-1">· {count}개</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* GD&T Category */}
      {CLASS_CATEGORIES.gdt.some(cls => filteredClassCounts[cls]) && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">🎯 GD&T (Geometric Dimensioning & Tolerancing)</p>
          <div className="grid grid-cols-2 gap-2">
            {CLASS_CATEGORIES.gdt.map((className) => {
              const count = filteredClassCounts[className];
              if (!count) return null;
              const details = CLASS_DETAILS[className];
              return (
                <div key={className} className="flex items-center gap-2 text-xs">
                  <div
                    className="w-4 h-4 rounded flex-shrink-0"
                    style={{ backgroundColor: CLASS_COLORS[className] }}
                  />
                  <span className="flex-1">
                    <span className="font-medium">{details.korean}</span>
                    <span className="text-muted-foreground"> ({details.english}, {details.abbr})</span>
                    <span className="text-green-600 ml-1">· {count}개</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Other Category */}
      {CLASS_CATEGORIES.other.some(cls => filteredClassCounts[cls]) && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">🔧 기타 (Other)</p>
          <div className="grid grid-cols-2 gap-2">
            {CLASS_CATEGORIES.other.map((className) => {
              const count = filteredClassCounts[className];
              if (!count) return null;
              const details = CLASS_DETAILS[className];
              return (
                <div key={className} className="flex items-center gap-2 text-xs">
                  <div
                    className="w-4 h-4 rounded flex-shrink-0"
                    style={{ backgroundColor: CLASS_COLORS[className] }}
                  />
                  <span className="flex-1">
                    <span className="font-medium">{details.korean}</span>
                    <span className="text-muted-foreground"> ({details.english}, {details.abbr})</span>
                    <span className="text-orange-600 ml-1">· {count}개</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
