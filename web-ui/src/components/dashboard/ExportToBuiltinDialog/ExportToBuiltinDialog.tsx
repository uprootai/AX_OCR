import { useState } from 'react';
import { X, FileCode, FileJson, Server, BookOpen, ExternalLink } from 'lucide-react';
import { Button } from '../../ui/Button';
import { Card } from '../../ui/Card';
import { CodeSection } from './CodeSection';
import {
  generateYAMLSpec,
  generateNodeDefinition,
  generateDockerCompose,
  generateTestCode,
} from './generators';
import type { ExportToBuiltinDialogProps } from './types';

/**
 * Custom API → Built-in API 내보내기 다이얼로그
 *
 * Custom API로 테스트 완료 후, Built-in API로 프로덕션화하기 위한
 * 필요한 파일들의 코드를 생성하고 가이드를 제공합니다.
 */
export default function ExportToBuiltinDialog({ isOpen, onClose, apiConfig }: ExportToBuiltinDialogProps) {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    yaml: true,
    nodedef: true,
    docker: false,
    test: false,
  });

  if (!isOpen || !apiConfig) return null;

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const copyToClipboard = async (text: string, section: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedSection(section);
      setTimeout(() => setCopiedSection(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const dockerServiceName = `${apiConfig.id}-api`;
  const port = apiConfig.port || 5020;

  const yamlSpec = generateYAMLSpec(apiConfig, dockerServiceName, port);
  const nodeDefinition = generateNodeDefinition(apiConfig);
  const dockerCompose = generateDockerCompose(apiConfig, dockerServiceName, port);
  const testCode = generateTestCode(apiConfig, port);

  const sections = [
    {
      key: 'yaml',
      title: '1. YAML 스펙',
      filePath: `gateway-api/api_specs/${apiConfig.id}.yaml`,
      icon: <FileJson className="w-5 h-5 text-yellow-600" />,
      content: yamlSpec,
    },
    {
      key: 'nodedef',
      title: '2. 노드 정의',
      filePath: 'web-ui/src/config/nodeDefinitions.ts',
      icon: <FileCode className="w-5 h-5 text-blue-600" />,
      content: nodeDefinition,
    },
    {
      key: 'docker',
      title: '3. Docker Compose',
      filePath: 'docker-compose.yml',
      icon: <Server className="w-5 h-5 text-cyan-600" />,
      content: dockerCompose,
    },
    {
      key: 'test',
      title: '4. 테스트 코드',
      filePath: `gateway-api/tests/test_${apiConfig.id}.py`,
      icon: <FileCode className="w-5 h-5 text-green-600" />,
      content: testCode,
    },
  ];

  const guideLinks = [
    { label: '📘 API 추가 완벽 가이드' },
    { label: '📋 YAML 스펙 레퍼런스' },
    { label: '🧩 노드 정의 레퍼런스' },
    { label: '🧪 테스트 가이드' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <FileCode className="w-6 h-6 text-primary" />
                Built-in API로 내보내기
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                <span className="font-mono bg-muted px-1 rounded">{apiConfig.id}</span>를 프로덕션 API로 전환합니다
              </p>
            </div>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* 안내 메시지 */}
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
            <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">📋 프로덕션화 단계</h3>
            <ol className="text-sm text-blue-700 dark:text-blue-300 space-y-1 list-decimal list-inside">
              <li>아래 코드를 각 파일에 복사</li>
              <li>Gateway API 재시작: <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">docker-compose restart gateway-api</code></li>
              <li>테스트 실행: <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">pytest tests/test_{apiConfig.id}.py -v</code></li>
              <li>Custom API 비활성화 (Dashboard에서 토글 OFF)</li>
            </ol>
          </div>

          {/* 코드 섹션들 */}
          <div className="space-y-4">
            {sections.map(section => (
              <CodeSection
                key={section.key}
                sectionKey={section.key}
                title={section.title}
                filePath={section.filePath}
                icon={section.icon}
                content={section.content}
                isExpanded={expandedSections[section.key] ?? false}
                isCopied={copiedSection === section.key}
                onToggle={toggleSection}
                onCopy={copyToClipboard}
              />
            ))}
          </div>

          {/* 문서 링크 */}
          <div className="mt-6 p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold flex items-center gap-2 mb-3">
              <BookOpen className="w-5 h-5" />
              상세 가이드
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {guideLinks.map(link => (
                <a
                  key={link.label}
                  href="/docs/docs"
                  target="_blank"
                  className="flex items-center gap-2 p-2 bg-background hover:bg-muted rounded border transition-colors"
                >
                  <span className="text-sm">{link.label}</span>
                  <ExternalLink className="w-4 h-4 ml-auto" />
                </a>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
            <Button variant="outline" onClick={onClose}>
              닫기
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
