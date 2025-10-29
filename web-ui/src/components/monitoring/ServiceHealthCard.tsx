import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Activity, AlertCircle, CheckCircle, Clock, ExternalLink } from 'lucide-react';
import type { ServiceHealth } from '../../types/api';
import { formatDistanceToNow } from 'date-fns';

interface ServiceHealthCardProps {
  service: ServiceHealth;
  onTest?: () => void;
}

export default function ServiceHealthCard({ service, onTest }: ServiceHealthCardProps) {
  const getStatusColor = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500';
      case 'degraded':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5" />;
      case 'degraded':
        return <AlertCircle className="h-5 w-5" />;
      case 'error':
        return <AlertCircle className="h-5 w-5" />;
      default:
        return <Activity className="h-5 w-5" />;
    }
  };

  const getStatusBadge = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="success">Healthy</Badge>;
      case 'degraded':
        return <Badge variant="warning">Degraded</Badge>;
      case 'error':
        return <Badge variant="error">Error</Badge>;
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  const handleCardClick = () => {
    if (service.swaggerUrl) {
      window.open(service.swaggerUrl, '_blank');
    }
  };

  return (
    <Card
      className={`hover:shadow-md transition-all ${service.swaggerUrl ? 'cursor-pointer hover:border-primary' : ''}`}
      onClick={handleCardClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <div className={`mt-0.5 ${getStatusColor(service.status)}`}>
              {getStatusIcon(service.status)}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">{service.name}</h3>
                {service.swaggerUrl && (
                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
              <div className="flex items-center gap-2 mt-1">
                {getStatusBadge(service.status)}
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {service.latency}ms
                </span>
              </div>
              {service.swaggerUrl && (
                <p className="text-xs text-primary mt-2 flex items-center gap-1">
                  Click to view API documentation
                </p>
              )}
              <p className="text-xs text-muted-foreground mt-1">
                Last check: {formatDistanceToNow(service.lastCheck, { addSuffix: true })}
              </p>
              {service.errorCount !== undefined && service.errorCount > 0 && (
                <p className="text-xs text-red-500 mt-1">
                  Errors: {service.errorCount}
                </p>
              )}
            </div>
          </div>
          {onTest && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTest();
              }}
              className="text-sm text-primary hover:underline"
            >
              Test
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
