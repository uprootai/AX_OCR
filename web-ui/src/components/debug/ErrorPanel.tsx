import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import {
  AlertCircle,
  XCircle,
  AlertTriangle,
  Info,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useState } from 'react';
import type { APIError } from '../../types/api';

interface ErrorPanelProps {
  error: APIError;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export default function ErrorPanel({ error, onRetry, onDismiss }: ErrorPanelProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const getSeverityConfig = (code: string | undefined) => {
    if (!code) {
      return {
        icon: <AlertCircle className="h-5 w-5" />,
        color: 'text-blue-500',
        bg: 'bg-blue-50 dark:bg-blue-950',
        border: 'border-blue-200 dark:border-blue-800',
        badge: 'default' as const,
        label: 'Error',
      };
    }
    if (code.startsWith('5')) {
      return {
        icon: <XCircle className="h-5 w-5" />,
        color: 'text-red-500',
        bg: 'bg-red-50 dark:bg-red-950',
        border: 'border-red-200 dark:border-red-800',
        badge: 'error' as const,
        label: 'Server Error',
      };
    }
    if (code.startsWith('4')) {
      return {
        icon: <AlertTriangle className="h-5 w-5" />,
        color: 'text-yellow-500',
        bg: 'bg-yellow-50 dark:bg-yellow-950',
        border: 'border-yellow-200 dark:border-yellow-800',
        badge: 'warning' as const,
        label: 'Client Error',
      };
    }
    return {
      icon: <AlertCircle className="h-5 w-5" />,
      color: 'text-blue-500',
      bg: 'bg-blue-50 dark:bg-blue-950',
      border: 'border-blue-200 dark:border-blue-800',
      badge: 'default' as const,
      label: 'Error',
    };
  };

  const config = getSeverityConfig(error.code);

  const getSuggestions = (error: APIError): string[] => {
    const suggestions: string[] = [];

    if (error.code === '500') {
      suggestions.push('서버 내부 오류입니다. 잠시 후 다시 시도해주세요.');
      suggestions.push('문제가 지속되면 서버 로그를 확인하세요.');
    } else if (error.code === '404') {
      suggestions.push('요청한 리소스를 찾을 수 없습니다.');
      suggestions.push('API 엔드포인트 URL을 확인하세요.');
    } else if (error.code === '400') {
      suggestions.push('요청 데이터 형식을 확인하세요.');
      suggestions.push('필수 파라미터가 누락되었을 수 있습니다.');
    } else if (error.code === '401') {
      suggestions.push('인증이 필요합니다.');
      suggestions.push('API 키 또는 토큰을 확인하세요.');
    } else if (error.code === '403') {
      suggestions.push('접근 권한이 없습니다.');
      suggestions.push('권한 설정을 확인하세요.');
    } else if (error.code === 'NETWORK_ERROR') {
      suggestions.push('네트워크 연결을 확인하세요.');
      suggestions.push('API 서버가 실행 중인지 확인하세요.');
      suggestions.push('방화벽 또는 CORS 설정을 확인하세요.');
    } else if (error.code === 'TIMEOUT') {
      suggestions.push('요청 시간이 초과되었습니다.');
      suggestions.push('대용량 파일의 경우 처리 시간이 오래 걸릴 수 있습니다.');
      suggestions.push('타임아웃 설정을 늘리거나 파일 크기를 줄여보세요.');
    }

    return suggestions;
  };

  const handleCopy = () => {
    const errorInfo = {
      code: error.code,
      message: error.message,
      details: error.details,
      timestamp: new Date().toISOString(),
    };
    navigator.clipboard.writeText(JSON.stringify(errorInfo, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const suggestions = getSuggestions(error);

  return (
    <Card className={`${config.bg} ${config.border} border-2`}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className={config.color}>{config.icon}</div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <CardTitle className="text-lg">{config.label}</CardTitle>
                <Badge variant={config.badge}>{error.code}</Badge>
              </div>
              <p className="text-sm font-medium mt-1">{error.message}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleCopy}>
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
            {onDismiss && (
              <Button variant="ghost" size="sm" onClick={onDismiss}>
                <XCircle className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Info className="h-4 w-4" />
              해결 방법
            </div>
            <ul className="space-y-1.5 ml-6">
              {suggestions.map((suggestion, index) => (
                <li key={index} className="text-sm list-disc">
                  {suggestion}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Error Details */}
        {error.details && (
          <div>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-2 text-sm font-semibold hover:underline"
            >
              {showDetails ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              상세 정보
            </button>
            {showDetails && (
              <div className="mt-2 p-3 bg-background/50 rounded border">
                <pre className="text-xs overflow-auto">
                  {typeof error.details === 'string'
                    ? error.details
                    : JSON.stringify(error.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        {onRetry && (
          <div className="pt-2">
            <Button variant="outline" size="sm" onClick={onRetry}>
              다시 시도
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
