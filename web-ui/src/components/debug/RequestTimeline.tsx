import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Clock, CheckCircle, XCircle, AlertCircle, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { RequestTrace } from '../../types/api';

interface RequestTimelineProps {
  traces: RequestTrace[];
  onSelectTrace?: (trace: RequestTrace) => void;
  onClearTraces?: () => void;
  maxItems?: number;
}

export default function RequestTimeline({
  traces,
  onSelectTrace,
  onClearTraces,
  maxItems = 20,
}: RequestTimelineProps) {
  const displayedTraces = traces.slice(-maxItems).reverse();

  const getStatusIcon = (status: number) => {
    if (status >= 200 && status < 300) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    if (status >= 400 && status < 500) {
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
    if (status >= 500) {
      return <XCircle className="h-4 w-4 text-red-500" />;
    }
    return <Clock className="h-4 w-4 text-gray-500" />;
  };

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'success';
    if (status >= 400 && status < 500) return 'warning';
    if (status >= 500) return 'error';
    return 'default';
  };

  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100';
      case 'POST':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100';
      case 'PUT':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100';
      case 'DELETE':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100';
    }
  };

  const getDurationColor = (duration: number) => {
    if (duration < 1000) return 'text-green-600 dark:text-green-400';
    if (duration < 3000) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  if (displayedTraces.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Request Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No requests yet</p>
            <p className="text-sm mt-2">
              API requests will appear here as you make them
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Request Timeline</CardTitle>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">
              {displayedTraces.length} of {traces.length} requests
            </span>
            {onClearTraces && (
              <Button variant="outline" size="sm" onClick={onClearTraces}>
                <Trash2 className="h-4 w-4 mr-2" />
                Clear
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {displayedTraces.map((trace) => (
            <div
              key={trace.id}
              onClick={() => onSelectTrace?.(trace)}
              className={`p-4 rounded-lg border transition-all ${
                onSelectTrace
                  ? 'cursor-pointer hover:border-primary hover:shadow-md'
                  : ''
              } ${trace.error ? 'bg-destructive/5 border-destructive/20' : 'hover:bg-accent/50'}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  {getStatusIcon(trace.status)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getMethodColor(
                          trace.method
                        )}`}
                      >
                        {trace.method}
                      </span>
                      <Badge variant={getStatusColor(trace.status)} className="text-xs">
                        {trace.status}
                      </Badge>
                    </div>
                    <p className="font-mono text-sm truncate mb-1">{trace.endpoint}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDistanceToNow(trace.timestamp, { addSuffix: true })}
                      </span>
                      <span className={`font-semibold ${getDurationColor(trace.duration)}`}>
                        {trace.duration}ms
                      </span>
                    </div>
                    {trace.error && (
                      <p className="text-xs text-destructive mt-2 truncate">
                        Error: {trace.error.message}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {traces.length > maxItems && (
          <div className="mt-4 pt-4 border-t text-center text-sm text-muted-foreground">
            Showing last {maxItems} requests. {traces.length - maxItems} older requests hidden.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
