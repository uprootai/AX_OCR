import { useQuery } from '@tanstack/react-query';
import { checkAllServicesIncludingCustom } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { useAPIConfigStore } from '../../store/apiConfigStore';
import { useEffect } from 'react';
import ServiceHealthCard from './ServiceHealthCard';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { RefreshCw } from 'lucide-react';

export default function APIStatusMonitor() {
  const { services, updateServiceHealth } = useMonitoringStore();
  const { customAPIs } = useAPIConfigStore();

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['health-check', customAPIs.length], // customAPIs 변경 시 재fetch
    queryFn: checkAllServicesIncludingCustom,
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

      // VL API
      if (data.vl) {
        updateServiceHealth('vl', {
          name: 'VL API',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5004/docs',
        });
      }

      // YOLO API
      if (data.yolo) {
        updateServiceHealth('yolo', {
          name: 'YOLOv11 API',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5005/docs',
        });
      }

      // PaddleOCR API
      if (data.paddleocr) {
        updateServiceHealth('paddleocr', {
          name: 'PaddleOCR API',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5006/docs',
        });
      }

      // ==================== New Services (PPT Gap Implementation) ====================

      // Knowledge API (Neo4j + GraphRAG + VectorRAG)
      if (data.knowledge) {
        updateServiceHealth('knowledge', {
          name: 'Knowledge API',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5007/docs',
        });
      }

      // Tesseract OCR API
      if (data.tesseract) {
        updateServiceHealth('tesseract', {
          name: 'Tesseract OCR',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5008/docs',
        });
      }

      // TrOCR API
      if (data.trocr) {
        updateServiceHealth('trocr', {
          name: 'TrOCR API',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5009/docs',
        });
      }

      // ESRGAN API
      if (data.esrgan) {
        updateServiceHealth('esrgan', {
          name: 'ESRGAN Upscaler',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5010/docs',
        });
      }

      // OCR Ensemble API
      if (data.ocr_ensemble) {
        updateServiceHealth('ocr_ensemble', {
          name: 'OCR Ensemble',
          status: 'healthy',
          latency: Math.random() * 50,
          lastCheck: new Date(),
          swaggerUrl: 'http://localhost:5011/docs',
        });
      }

      // 커스텀 API 동적 처리
      customAPIs.forEach((api) => {
        if (data[api.id]) {
          updateServiceHealth(api.id, {
            name: api.displayName,
            status: 'healthy',
            latency: Math.random() * 50,
            lastCheck: new Date(),
            swaggerUrl: `${api.baseUrl}/docs`,
          });
        } else {
          updateServiceHealth(api.id, {
            name: api.displayName,
            status: 'error',
            latency: 0,
            lastCheck: new Date(),
            errorMessage: 'Service unavailable',
          });
        }
      });
    }
  }, [data, updateServiceHealth, customAPIs]);

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
          {/* 기본 API 서비스 */}
          {services.gateway && (
            <ServiceHealthCard service={services.gateway} />
          )}
          {services.yolo && (
            <ServiceHealthCard service={services.yolo} />
          )}
          {services.edocr2_v1 && (
            <ServiceHealthCard service={services.edocr2_v1} />
          )}
          {services.edocr2_v2 && (
            <ServiceHealthCard service={services.edocr2_v2} />
          )}
          {services.paddleocr && (
            <ServiceHealthCard service={services.paddleocr} />
          )}
          {services.edgnet && (
            <ServiceHealthCard service={services.edgnet} />
          )}
          {services.skinmodel && (
            <ServiceHealthCard service={services.skinmodel} />
          )}
          {services.vl && (
            <ServiceHealthCard service={services.vl} />
          )}

          {/* New Services (PPT Gap Implementation) */}
          {services.knowledge && (
            <ServiceHealthCard service={services.knowledge} />
          )}
          {services.tesseract && (
            <ServiceHealthCard service={services.tesseract} />
          )}
          {services.trocr && (
            <ServiceHealthCard service={services.trocr} />
          )}
          {services.esrgan && (
            <ServiceHealthCard service={services.esrgan} />
          )}
          {services.ocr_ensemble && (
            <ServiceHealthCard service={services.ocr_ensemble} />
          )}

          {/* 커스텀 API 동적 렌더링 */}
          {customAPIs.map((api) => {
            const service = services[api.id];
            if (!service) return null;
            return <ServiceHealthCard key={api.id} service={service} />;
          })}
        </div>
      </CardContent>
    </Card>
  );
}
