import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import Toast from './ui/Toast';

// Toast 상태 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

interface Props {
  children: ReactNode;
  fallbackUI?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  toast: ToastState;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      toast: { show: false, message: '', type: 'info' },
    };
  }

  // Toast 표시 헬퍼
  showToast = (message: string, type: ToastState['type'] = 'info') => {
    this.setState({ toast: { show: true, message, type } });
  };

  // Toast 닫기
  hideToast = () => {
    this.setState(prev => ({ ...prev, toast: { ...prev.toast, show: false } }));
  };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 에러 로깅
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 에러 정보를 localStorage에 저장 (디버깅용)
    try {
      const errorLog = {
        timestamp: new Date().toISOString(),
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
      };

      const existingLogs = localStorage.getItem('errorLogs');
      const logs = existingLogs ? JSON.parse(existingLogs) : [];
      logs.push(errorLog);

      // 최근 10개만 유지
      if (logs.length > 10) {
        logs.shift();
      }

      localStorage.setItem('errorLogs', JSON.stringify(logs));
    } catch (e) {
      console.error('Failed to save error log:', e);
    }

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleCopyError = () => {
    const { error, errorInfo } = this.state;
    const errorText = `
오류 발생 시간: ${new Date().toLocaleString()}

오류 메시지:
${error?.message}

스택 트레이스:
${error?.stack}

컴포넌트 스택:
${errorInfo?.componentStack}
    `.trim();

    navigator.clipboard
      .writeText(errorText)
      .then(() => this.showToast('✓ 오류 정보가 클립보드에 복사되었습니다', 'success'))
      .catch(() => this.showToast('✗ 클립보드 복사에 실패했습니다', 'error'));
  };

  render() {
    if (this.state.hasError) {
      // 사용자 정의 fallback UI가 제공된 경우
      if (this.props.fallbackUI) {
        return this.props.fallbackUI;
      }

      // 기본 에러 UI
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-900">
          <Card className="max-w-2xl w-full">
            <div className="p-8 space-y-6">
              {/* 에러 아이콘 및 제목 */}
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <AlertCircle className="w-12 h-12 text-red-500" />
                </div>
                <div className="flex-1">
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    예상치 못한 오류가 발생했습니다
                  </h1>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    죄송합니다. 애플리케이션에서 오류가 발생했습니다. 아래 옵션을 선택해주세요.
                  </p>
                </div>
              </div>

              {/* 에러 메시지 */}
              <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-2">
                  오류 메시지:
                </h3>
                <p className="text-sm text-red-800 dark:text-red-200 font-mono break-all">
                  {this.state.error?.message}
                </p>
              </div>

              {/* 상세 오류 정보 (접을 수 있음) */}
              <details className="border border-gray-200 dark:border-gray-700 rounded-lg">
                <summary className="cursor-pointer p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <span className="text-sm font-medium">상세 오류 정보 보기</span>
                </summary>
                <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                  <div className="space-y-3">
                    <div>
                      <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                        스택 트레이스:
                      </h4>
                      <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                        {this.state.error?.stack}
                      </pre>
                    </div>
                    {this.state.errorInfo && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                          컴포넌트 스택:
                        </h4>
                        <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              </details>

              {/* 액션 버튼 */}
              <div className="flex items-center gap-3 pt-4">
                <Button onClick={this.handleReload} size="sm">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  페이지 새로고침
                </Button>
                <Button variant="outline" onClick={this.handleGoHome} size="sm">
                  <Home className="w-4 h-4 mr-2" />
                  홈으로 이동
                </Button>
                <Button variant="outline" onClick={this.handleCopyError} size="sm">
                  오류 정보 복사
                </Button>
              </div>

              {/* 지원 정보 */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  문제가 지속되면 페이지를 새로고침하거나, 브라우저 캐시를 삭제한 후 다시 시도해주세요.
                </p>
              </div>
            </div>
          </Card>

          {/* Toast 알림 */}
          {this.state.toast.show && (
            <Toast
              message={this.state.toast.message}
              type={this.state.toast.type}
              duration={this.state.toast.type === 'error' ? 15000 : 10000}
              onClose={this.hideToast}
            />
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
