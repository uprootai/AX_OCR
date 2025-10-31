import { useQuery } from '@tanstack/react-query';
import { checkAllServices } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { useEffect } from 'react';
import ServiceHealthCard from './ServiceHealthCard';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { RefreshCw } from 'lucide-react';

export default function APIStatusMonitor() {
  const { services, updateServiceHealth } = useMonitoringStore();

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['health-check'],
    queryFn: checkAllServices,
    refetchInterval: 30000, // 30초마다 자동 갱신
  });

  useEffect(() => {
    if (data) {
      // Gateway
      if (data.gateway) {
        updateServiceHealth('gateway', {
          name: 'Gateway API',
          status: 'healthy',
          latency: Math.random() * 50, // 임시
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:8000/docs',
        });
      }

      // eDOCr v1
      if (data.edocr2_v1) {
        updateServiceHealth('edocr2_v1', {
          name: 'eDOCr v1 - Fast',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5001/docs',
        });
      }

      // eDOCr v2
      if (data.edocr2_v2) {
        updateServiceHealth('edocr2_v2', {
          name: 'eDOCr v2 - Advanced',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5002/docs',
        });
      }

      // EDGNet
      if (data.edgnet) {
        updateServiceHealth('edgnet', {
          name: 'EDGNet API',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5012/docs',
        });
      }

      // Skin Model
      if (data.skinmodel) {
        updateServiceHealth('skinmodel', {
          name: 'Skin Model API',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5003/docs',
        });
      }
    }
  }, [data, updateServiceHealth]);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-center text-muted-foreground">Loading API status...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>API Health Status</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid md:grid-cols-2 gap-4">
          {services.gateway && (
            <ServiceHealthCard service={services.gateway} />
          )}
          {services.edocr2_v1 && (
            <ServiceHealthCard service={services.edocr2_v1} />
          )}
          {services.edocr2_v2 && (
            <ServiceHealthCard service={services.edocr2_v2} />
          )}
          {services.edgnet && (
            <ServiceHealthCard service={services.edgnet} />
          )}
          {services.skinmodel && (
            <ServiceHealthCard service={services.skinmodel} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
