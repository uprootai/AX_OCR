import type { APIConfig } from '../../../store/apiConfigStore';

export function generateYAMLSpec(apiConfig: APIConfig, dockerServiceName: string, port: number): string {
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
}

export function generateNodeDefinition(apiConfig: APIConfig): string {
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
}

export function generateDockerCompose(apiConfig: APIConfig, dockerServiceName: string, port: number): string {
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
}

export function generateTestCode(apiConfig: APIConfig, port: number): string {
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
}
