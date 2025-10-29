import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import JSONViewer from './JSONViewer';
import { Clock, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';
import type { RequestTrace } from '../../types/api';

interface RequestInspectorProps {
  trace: RequestTrace;
}

export default function RequestInspector({ trace }: RequestInspectorProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'request' | 'response' | 'timeline'>(
    'overview'
  );

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'success';
    if (status >= 400 && status < 500) return 'warning';
    if (status >= 500) return 'error';
    return 'default';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-3">
            <span className="font-mono text-sm">{trace.method}</span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-normal text-muted-foreground">
              {trace.endpoint}
            </span>
          </CardTitle>
          <Badge variant={getStatusColor(trace.status)}>
            {trace.status >= 200 && trace.status < 300 ? (
              <CheckCircle className="h-3 w-3 mr-1" />
            ) : (
              <XCircle className="h-3 w-3 mr-1" />
            )}
            {trace.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'overview'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('request')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'request'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Request
          </button>
          <button
            onClick={() => setActiveTab('response')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'response'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Response
          </button>
          {trace.timeline && (
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'timeline'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Timeline
            </button>
          )}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-muted-foreground">Request ID</h4>
                <p className="font-mono text-sm">{trace.id}</p>
              </div>
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-muted-foreground">Timestamp</h4>
                <p className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  {format(trace.timestamp, 'yyyy-MM-dd HH:mm:ss.SSS')}
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-muted-foreground">Duration</h4>
                <p className="text-sm font-semibold">
                  {trace.duration}ms
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-muted-foreground">Status</h4>
                <Badge variant={getStatusColor(trace.status)}>{trace.status}</Badge>
              </div>
            </div>

            {trace.error && (
              <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
                <h4 className="font-semibold text-destructive mb-2">Error</h4>
                <p className="text-sm text-destructive">{trace.error.message}</p>
                {trace.error.details && (
                  <pre className="mt-2 text-xs text-destructive/80 overflow-auto">
                    {JSON.stringify(trace.error.details, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'request' && (
          <div>
            <JSONViewer
              data={trace.request}
              title="Request Data"
              defaultExpanded={true}
            />
          </div>
        )}

        {activeTab === 'response' && (
          <div>
            <JSONViewer
              data={trace.response}
              title="Response Data"
              defaultExpanded={true}
            />
          </div>
        )}

        {activeTab === 'timeline' && trace.timeline && (
          <div className="space-y-4">
            <h4 className="font-semibold mb-4">Request Timeline</h4>
            <div className="space-y-3">
              {trace.timeline.upload !== undefined && (
                <TimelineItem
                  label="File Upload"
                  duration={trace.timeline.upload}
                  percentage={(trace.timeline.upload / trace.duration) * 100}
                />
              )}
              {trace.timeline.edocr2 !== undefined && (
                <TimelineItem
                  label="eDOCr2 Processing"
                  duration={trace.timeline.edocr2}
                  percentage={(trace.timeline.edocr2 / trace.duration) * 100}
                />
              )}
              {trace.timeline.edgnet !== undefined && (
                <TimelineItem
                  label="EDGNet Processing"
                  duration={trace.timeline.edgnet}
                  percentage={(trace.timeline.edgnet / trace.duration) * 100}
                />
              )}
              {trace.timeline.skinmodel !== undefined && (
                <TimelineItem
                  label="Skin Model Processing"
                  duration={trace.timeline.skinmodel}
                  percentage={(trace.timeline.skinmodel / trace.duration) * 100}
                />
              )}
              {trace.timeline.response !== undefined && (
                <TimelineItem
                  label="Response Assembly"
                  duration={trace.timeline.response}
                  percentage={(trace.timeline.response / trace.duration) * 100}
                />
              )}
            </div>
            <div className="mt-6 pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="font-semibold">Total Duration</span>
                <span className="font-semibold text-lg">{trace.duration}ms</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface TimelineItemProps {
  label: string;
  duration: number;
  percentage: number;
}

function TimelineItem({ label, duration, percentage }: TimelineItemProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-muted-foreground">
          {duration}ms ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div className="h-2 bg-accent rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
