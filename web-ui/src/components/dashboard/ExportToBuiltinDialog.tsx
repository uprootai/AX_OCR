import { useState } from 'react';
import { X, Copy, Check, FileCode, FileJson, Server, BookOpen, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import type { APIConfig } from '../../store/apiConfigStore';

interface ExportToBuiltinDialogProps {
  isOpen: boolean;
  onClose: () => void;
  apiConfig: APIConfig | null;
}

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

  // Docker 서비스 이름 생성 (id + -api)
  const dockerServiceName = `${apiConfig.id}-api`;

  // URL에서 포트 추출
  const port = apiConfig.port || 5020;

  // =====================
  // YAML 스펙 생성
  // =====================
  const generateYAMLSpec = () => {
    const params = apiConfig.parameters?.map(p => {
      let paramYaml = `  - name: ${p.name}
    type: ${p.type === 'select' ? 'string' : p.type}
    default: ${typeof p.default === 'string' ? `"${p.default}"` : p.default}
    description: ${p.description}
    uiType: ${p.type === 'select' ? 'select' : p.type === 'number' ? 'number' : p.type === 'boolean' ? 'checkbox' : 'text'}`;

      if (p.type === 'number' && p.min !== undefined) {
        paramYaml += `\n    min: ${p.min}`;
      }
      if (p.type === 'number' && p.max !== undefined) {
        paramYaml += `\n    max: ${p.max}`;
      }
      if (p.type === 'select' && p.options) {
        paramYaml += `\n    options:\n${p.options.map(o => `      - ${o}`).join('\n')}`;
      }
      return paramYaml;
    }).join('\n') || '';

    const inputs = apiConfig.inputs?.map(i =>
      `  - name: ${i.name}
    type: ${i.type}
    required: ${i.required ?? true}
    description: ${i.description}`
    ).join('\n') || `  - name: image
    type: Image
    required: true
    description: 입력 이미지`;

    const outputs = apiConfig.outputs?.map(o =>
      `  - name: ${o.name}
    type: ${o.type}
    description: ${o.description}`
    ).join('\n') || `  - name: results
    type: Result[]
    description: 처리 결과`;

    const inputMappings = apiConfig.inputMappings
      ? Object.entries(apiConfig.inputMappings).map(([k, v]) => `    ${k}: ${v}`).join('\n')
      : '    file: image';

    const outputMappings = apiConfig.outputMappings
      ? Object.entries(apiConfig.outputMappings).map(([k, v]) => `    ${k}: ${v}`).join('\n')
      : '    results: data.results';

    return `# ${apiConfig.displayName} API Specification
# 생성일: ${new Date().toISOString().split('T')[0]}
# 파일 위치: gateway-api/api_specs/${apiConfig.id}.yaml

apiVersion: v1
kind: APISpec

metadata:
  id: ${apiConfig.id}
  name: ${apiConfig.name}
  version: 1.0.0
  host: ${dockerServiceName}
  port: ${port}
  description: "${apiConfig.description}"
  author: AX Team
  tags:
    - ${apiConfig.category}

server:
  endpoint: ${apiConfig.endpoint || '/api/v1/process'}
  method: ${apiConfig.method || 'POST'}
  contentType: multipart/form-data
  timeout: 60
  healthEndpoint: /health

blueprintflow:
  category: ${apiConfig.category}
  color: "${apiConfig.color}"
  icon: FileText
  requiresImage: ${apiConfig.requiresImage ?? true}

inputs:
${inputs}

outputs:
${outputs}

parameters:
${params || '  []'}

mappings:
  input:
${inputMappings}
  output:
${outputMappings}

i18n:
  ko:
    label: ${apiConfig.displayName}
    description: "${apiConfig.description}"
  en:
    label: ${apiConfig.displayName}
    description: "${apiConfig.description}"
`;
  };

  // =====================
  // nodeDefinitions.ts 코드 생성
  // =====================
  const generateNodeDefinition = () => {
    const params = apiConfig.parameters?.map(p => {
      let paramCode = `      {
        name: '${p.name}',
        type: '${p.type}',
        default: ${typeof p.default === 'string' ? `'${p.default}'` : p.default},
        description: '${p.description}',`;

      if (p.type === 'number') {
        if (p.min !== undefined) paramCode += `\n        min: ${p.min},`;
        if (p.max !== undefined) paramCode += `\n        max: ${p.max},`;
        if (p.step !== undefined) paramCode += `\n        step: ${p.step},`;
      }
      if (p.type === 'select' && p.options) {
        paramCode += `\n        options: [${p.options.map(o => `'${o}'`).join(', ')}],`;
      }
      paramCode += '\n      }';
      return paramCode;
    }).join(',\n') || '';

    const inputs = apiConfig.inputs?.map(i =>
      `      { name: '${i.name}', type: '${i.type}', description: '${i.description}' }`
    ).join(',\n') || `      { name: 'image', type: 'Image', description: '📄 입력 이미지' }`;

    const outputs = apiConfig.outputs?.map(o =>
      `      { name: '${o.name}', type: '${o.type}', description: '${o.description}' }`
    ).join(',\n') || `      { name: 'results', type: 'Result[]', description: '📝 처리 결과' }`;

    return `  // =====================
  // ${apiConfig.displayName}
  // 파일 위치: web-ui/src/config/nodeDefinitions.ts
  // =====================
  ${apiConfig.id}: {
    type: '${apiConfig.id}',
    label: '${apiConfig.displayName}',
    category: '${apiConfig.category}',
    color: '${apiConfig.color}',
    icon: 'FileText',
    description: '${apiConfig.description}',

    inputs: [
${inputs},
    ],

    outputs: [
${outputs},
    ],

    parameters: [
${params}
    ],

    examples: [
      'ImageInput → ${apiConfig.displayName} → 결과 처리',
      'ESRGAN → ${apiConfig.displayName} → 고해상도 처리',
    ],

    usageTips: [
      '💡 visualize=true로 결과를 시각적으로 확인',
      '⭐ ESRGAN과 함께 사용하면 정확도가 향상됩니다',
    ],

    recommendedInputs: [
      { from: 'imageinput', field: 'image', reason: '이미지 입력' },
      { from: 'esrgan', field: 'image', reason: '업스케일된 이미지로 정확도 향상' },
    ],
  },`;
  };

  // =====================
  // Docker Compose 스니펫 생성
  // =====================
  const generateDockerCompose = () => {
    return `  # ${apiConfig.displayName}
  # 파일 위치: docker-compose.yml (services 섹션에 추가)
  ${dockerServiceName}:
    build:
      context: ./models/${dockerServiceName}
      dockerfile: Dockerfile
    container_name: ${dockerServiceName}
    ports:
      - "${port}:${port}"
    volumes:
      - ./models/${dockerServiceName}/uploads:/tmp/${apiConfig.id}/uploads
      - ./models/${dockerServiceName}/results:/tmp/${apiConfig.id}/results
    environment:
      - ${apiConfig.name.toUpperCase()}_PORT=${port}
      - PYTHONUNBUFFERED=1
    networks:
      - ax_poc_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3`;
  };

  // =====================
  // 테스트 코드 생성
  // =====================
  const generateTestCode = () => {
    return `# ${apiConfig.displayName} 통합 테스트
# 파일 위치: gateway-api/tests/test_${apiConfig.id}.py

import pytest
import httpx
import base64
from pathlib import Path

API_URL = "http://localhost:${port}"
GATEWAY_URL = "http://localhost:8000"
TEST_IMAGE = Path(__file__).parent / "fixtures" / "test_drawing.jpg"


class Test${apiConfig.name}Server:
    """API 서버 직접 테스트"""

    def test_health(self):
        r = httpx.get(f"{API_URL}/health", timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_process(self):
        with open(TEST_IMAGE, "rb") as f:
            r = httpx.post(
                f"{API_URL}/api/v1/process",
                files={"file": f},
                data={"visualize": "true"},
                timeout=60
            )
        assert r.status_code == 200
        assert r.json()["success"] is True


class TestBlueprintFlow:
    """BlueprintFlow 통합 테스트"""

    def test_workflow(self):
        with open(TEST_IMAGE, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        workflow = {
            "workflow": {
                "name": "Test ${apiConfig.displayName}",
                "nodes": [
                    {"id": "input1", "type": "imageinput", "position": {"x": 0, "y": 0}, "data": {}},
                    {"id": "api1", "type": "${apiConfig.id}", "position": {"x": 200, "y": 0},
                     "data": {"parameters": {"visualize": True}}}
                ],
                "edges": [{"id": "e1", "source": "input1", "target": "api1"}]
            },
            "image": image_b64
        }

        r = httpx.post(f"{GATEWAY_URL}/api/v1/blueprintflow/execute", json=workflow, timeout=120)
        assert r.status_code == 200
        assert r.json()["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])`;
  };

  const yamlSpec = generateYAMLSpec();
  const nodeDefinition = generateNodeDefinition();
  const dockerCompose = generateDockerCompose();
  const testCode = generateTestCode();

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
            {/* YAML 스펙 */}
            <div className="border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('yaml')}
                className="w-full flex items-center justify-between p-4 bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-2">
                  <FileJson className="w-5 h-5 text-yellow-600" />
                  <span className="font-semibold">1. YAML 스펙</span>
                  <code className="text-xs bg-muted px-2 py-0.5 rounded">
                    gateway-api/api_specs/{apiConfig.id}.yaml
                  </code>
                </div>
                {expandedSections.yaml ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>
              {expandedSections.yaml && (
                <div className="p-4 bg-gray-900 relative">
                  <button
                    onClick={() => copyToClipboard(yamlSpec, 'yaml')}
                    className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded"
                  >
                    {copiedSection === 'yaml' ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-300" />}
                  </button>
                  <pre className="text-sm text-gray-100 overflow-x-auto font-mono whitespace-pre">{yamlSpec}</pre>
                </div>
              )}
            </div>

            {/* nodeDefinitions.ts */}
            <div className="border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('nodedef')}
                className="w-full flex items-center justify-between p-4 bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold">2. 노드 정의</span>
                  <code className="text-xs bg-muted px-2 py-0.5 rounded">
                    web-ui/src/config/nodeDefinitions.ts
                  </code>
                </div>
                {expandedSections.nodedef ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>
              {expandedSections.nodedef && (
                <div className="p-4 bg-gray-900 relative">
                  <button
                    onClick={() => copyToClipboard(nodeDefinition, 'nodedef')}
                    className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded"
                  >
                    {copiedSection === 'nodedef' ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-300" />}
                  </button>
                  <pre className="text-sm text-gray-100 overflow-x-auto font-mono whitespace-pre">{nodeDefinition}</pre>
                </div>
              )}
            </div>

            {/* Docker Compose */}
            <div className="border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('docker')}
                className="w-full flex items-center justify-between p-4 bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Server className="w-5 h-5 text-cyan-600" />
                  <span className="font-semibold">3. Docker Compose</span>
                  <code className="text-xs bg-muted px-2 py-0.5 rounded">
                    docker-compose.yml
                  </code>
                </div>
                {expandedSections.docker ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>
              {expandedSections.docker && (
                <div className="p-4 bg-gray-900 relative">
                  <button
                    onClick={() => copyToClipboard(dockerCompose, 'docker')}
                    className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded"
                  >
                    {copiedSection === 'docker' ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-300" />}
                  </button>
                  <pre className="text-sm text-gray-100 overflow-x-auto font-mono whitespace-pre">{dockerCompose}</pre>
                </div>
              )}
            </div>

            {/* 테스트 코드 */}
            <div className="border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('test')}
                className="w-full flex items-center justify-between p-4 bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-green-600" />
                  <span className="font-semibold">4. 테스트 코드</span>
                  <code className="text-xs bg-muted px-2 py-0.5 rounded">
                    gateway-api/tests/test_{apiConfig.id}.py
                  </code>
                </div>
                {expandedSections.test ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>
              {expandedSections.test && (
                <div className="p-4 bg-gray-900 relative">
                  <button
                    onClick={() => copyToClipboard(testCode, 'test')}
                    className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded"
                  >
                    {copiedSection === 'test' ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-300" />}
                  </button>
                  <pre className="text-sm text-gray-100 overflow-x-auto font-mono whitespace-pre">{testCode}</pre>
                </div>
              )}
            </div>
          </div>

          {/* 문서 링크 */}
          <div className="mt-6 p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold flex items-center gap-2 mb-3">
              <BookOpen className="w-5 h-5" />
              상세 가이드
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <a
                href="/docs"
                target="_blank"
                className="flex items-center gap-2 p-2 bg-background hover:bg-muted rounded border transition-colors"
              >
                <span className="text-sm">📘 API 추가 완벽 가이드</span>
                <ExternalLink className="w-4 h-4 ml-auto" />
              </a>
              <a
                href="/docs"
                target="_blank"
                className="flex items-center gap-2 p-2 bg-background hover:bg-muted rounded border transition-colors"
              >
                <span className="text-sm">📋 YAML 스펙 레퍼런스</span>
                <ExternalLink className="w-4 h-4 ml-auto" />
              </a>
              <a
                href="/docs"
                target="_blank"
                className="flex items-center gap-2 p-2 bg-background hover:bg-muted rounded border transition-colors"
              >
                <span className="text-sm">🧩 노드 정의 레퍼런스</span>
                <ExternalLink className="w-4 h-4 ml-auto" />
              </a>
              <a
                href="/docs"
                target="_blank"
                className="flex items-center gap-2 p-2 bg-background hover:bg-muted rounded border transition-colors"
              >
                <span className="text-sm">🧪 테스트 가이드</span>
                <ExternalLink className="w-4 h-4 ml-auto" />
              </a>
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
