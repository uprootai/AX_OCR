import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface ToleranceVisualizationProps {
  toleranceData: {
    manufacturability?: {
      score: number;
      difficulty: string;
    };
    predicted_tolerances?: {
      flatness?: number;
      cylindricity?: number;
      position?: number;
      perpendicularity?: number;
      concentricity?: number;
      runout?: number;
    };
    analysis?: Record<string, unknown>;
  };
  compact?: boolean;
}

export default function ToleranceVisualization({ toleranceData, compact = false }: ToleranceVisualizationProps) {
  const { manufacturability, predicted_tolerances, analysis } = toleranceData;

  const score = manufacturability?.score || 0;
  const difficulty = manufacturability?.difficulty || 'Unknown';

  // Get difficulty color
  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case 'easy':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'hard':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  // Get score color
  const getScoreColor = (s: number) => {
    if (s >= 0.8) return 'bg-green-500';
    if (s >= 0.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (compact) {
    return (
      <div className="space-y-3">
        {/* Manufacturability Score */}
        {manufacturability && (
          <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-orange-900 dark:text-orange-100">
                Manufacturing Score
              </span>
              <Badge className={getDifficultyColor(difficulty)}>
                {difficulty}
              </Badge>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getScoreColor(score)} transition-all duration-500`}
                  style={{ width: `${score * 100}%` }}
                />
              </div>
              <span className="text-sm font-bold text-orange-900 dark:text-orange-100">
                {(score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}

        {/* Predicted Tolerances */}
        {predicted_tolerances && Object.keys(predicted_tolerances).length > 0 && (
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <div className="text-xs font-semibold text-purple-900 dark:text-purple-100 mb-2">
              Predicted Tolerances
            </div>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(predicted_tolerances).map(([key, value]) => (
                value !== undefined && (
                  <div key={key} className="flex items-center justify-between text-xs">
                    <span className="text-purple-700 dark:text-purple-300 capitalize">{key}:</span>
                    <span className="font-mono font-semibold text-purple-900 dark:text-purple-100">
                      {typeof value === 'number' ? value.toFixed(4) : value}
                    </span>
                  </div>
                )
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <Card>
      <div className="p-6 space-y-6">
        <h3 className="text-lg font-semibold">Tolerance Analysis</h3>

        {/* Manufacturability */}
        {manufacturability && (
          <div className="space-y-4">
            <h4 className="font-medium text-sm text-muted-foreground">Manufacturability</h4>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-accent rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">Score</p>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getScoreColor(score)} transition-all duration-500`}
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <span className="text-xl font-bold">
                    {(score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="p-4 bg-accent rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">Difficulty</p>
                <Badge className={`text-lg ${getDifficultyColor(difficulty)}`}>
                  {difficulty}
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* Predicted Tolerances */}
        {predicted_tolerances && Object.keys(predicted_tolerances).length > 0 && (
          <div className="space-y-4">
            <h4 className="font-medium text-sm text-muted-foreground">Predicted Tolerances</h4>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(predicted_tolerances).map(([key, value]) => (
                value !== undefined && (
                  <div key={key} className="p-3 bg-background border rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1 capitalize">{key}</p>
                    <p className="font-mono font-semibold text-lg">
                      {typeof value === 'number' ? value.toFixed(4) : value}
                    </p>
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Additional Analysis */}
        {analysis && Object.keys(analysis).length > 0 && (
          <div className="space-y-4">
            <h4 className="font-medium text-sm text-muted-foreground">Analysis Details</h4>
            <div className="p-4 bg-accent rounded-lg">
              <div className="space-y-2">
                {Object.entries(analysis).slice(0, 10).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className="font-mono">{String(value).slice(0, 50)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
