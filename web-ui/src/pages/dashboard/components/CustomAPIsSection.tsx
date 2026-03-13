import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Plus, Download, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { type APIConfig } from '../../../store/apiConfigStore';

interface CustomAPIsSectionProps {
  customAPIs: APIConfig[];
  onToggle: (id: string) => void;
  onExport: (api: APIConfig) => void;
  onRemove: (id: string, displayName: string) => void;
}

export function CustomAPIsSection({ customAPIs, onToggle, onExport, onRemove }: CustomAPIsSectionProps) {
  if (customAPIs.length === 0) return null;

  return (
    <Card id="section-custom-apis" className="scroll-mt-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Custom APIs ({customAPIs.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {customAPIs.map((api) => (
            <div
              key={api.id}
              className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                api.enabled ? 'bg-background' : 'bg-muted/50 opacity-60'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                  style={{ backgroundColor: api.color + '20', color: api.color }}
                >
                  {api.icon}
                </div>
                <div>
                  <div className="font-semibold flex items-center gap-2">
                    {api.displayName}
                    <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{api.id}</code>
                  </div>
                  <div className="text-sm text-muted-foreground">{api.description}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {api.baseUrl} • {api.category}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {/* Toggle */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onToggle(api.id)}
                  title={api.enabled ? '비활성화' : '활성화'}
                >
                  {api.enabled ? (
                    <ToggleRight className="w-5 h-5 text-green-500" />
                  ) : (
                    <ToggleLeft className="w-5 h-5 text-muted-foreground" />
                  )}
                </Button>

                {/* Export to Built-in */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onExport(api)}
                  title="Built-in API로 내보내기"
                  className="gap-1"
                >
                  <Download className="w-4 h-4" />
                  내보내기
                </Button>

                {/* Delete */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemove(api.id, api.displayName)}
                  title="삭제"
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* 가이드 메시지 */}
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>💡 워크플로우:</strong> Custom API로 테스트 → <strong>내보내기</strong> 버튼으로 Built-in API 코드 생성 → 파일 저장 → Custom API 비활성화
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
