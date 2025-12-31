import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { Terminal } from 'lucide-react';

interface SpecRefSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function SpecRefSection({ sectionRef }: SpecRefSectionProps) {
  const yamlExample = `apiVersion: v1
kind: APISpec

metadata:
  id: myapi
  name: MyAPI
  version: 1.0.0
  host: myapi-api      # Docker service name
  port: 5020

server:
  endpoint: /api/v1/process
  method: POST
  contentType: multipart/form-data

blueprintflow:
  category: ocr
  color: "#8b5cf6"
  icon: ScanText
  requiresImage: true

parameters:
  - name: visualize
    type: boolean
    default: true
    description: Enable visualization
    uiType: checkbox`;

  const yamlFields = [
    { field: 'apiVersion', desc: 'v1 fixed', color: 'blue' },
    { field: 'kind', desc: 'APISpec fixed', color: 'blue' },
    { field: 'metadata', desc: 'id, name, host, port', color: 'green' },
    { field: 'server', desc: 'endpoint, method, timeout', color: 'green' },
    { field: 'blueprintflow', desc: 'category, color, icon', color: 'purple' },
    { field: 'inputs', desc: 'Input definitions', color: 'orange' },
    { field: 'outputs', desc: 'Output definitions', color: 'orange' },
    { field: 'parameters', desc: 'Parameter definitions', color: 'pink' },
  ];

  const categories = [
    { cat: 'input', color: 'blue', desc: 'Input nodes' },
    { cat: 'detection', color: 'cyan', desc: 'Object detection' },
    { cat: 'ocr', color: 'green', desc: 'Text recognition' },
    { cat: 'segmentation', color: 'purple', desc: 'Segmentation' },
    { cat: 'preprocessing', color: 'yellow', desc: 'Preprocessing' },
    { cat: 'analysis', color: 'pink', desc: 'Analysis' },
    { cat: 'knowledge', color: 'violet', desc: 'Knowledge engine' },
    { cat: 'ai', color: 'indigo', desc: 'AI/LLM' },
    { cat: 'control', color: 'gray', desc: 'Control nodes' },
  ];

  const parameterTypes = [
    { type: 'string', ui: 'text, select, textarea', example: '"default"' },
    { type: 'number', ui: 'number, slider', example: '0.5' },
    { type: 'integer', ui: 'number', example: '10' },
    { type: 'boolean', ui: 'checkbox, switch', example: 'true' },
  ];

  return (
    <section
      id="specref"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card className="border-2 border-emerald-300 dark:border-emerald-700">
        <CardHeader className="bg-emerald-50 dark:bg-emerald-900/20">
          <CardTitle className="flex items-center text-emerald-900 dark:text-emerald-100">
            <Terminal className="w-5 h-5 mr-2" />
            API Spec YAML Reference
            <Badge className="ml-3 bg-emerald-600">v1</Badge>
          </CardTitle>
          <p className="text-sm text-emerald-800 dark:text-emerald-200 mt-2">
            gateway-api/api_specs/*.yaml file authoring guide
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* YAML Structure */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">YAML Spec Structure</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                {yamlFields.map((item) => (
                  <div key={item.field} className={`p-2 bg-${item.color}-50 dark:bg-${item.color}-900/20 rounded border border-${item.color}-200 dark:border-${item.color}-800`}>
                    <code className="text-xs font-mono">{item.field}</code>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Category List */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Available Categories</h3>
              <div className="flex flex-wrap gap-2">
                {categories.map((item) => (
                  <span key={item.cat} className={`px-3 py-1 text-xs rounded-full bg-${item.color}-100 dark:bg-${item.color}-900/30 text-${item.color}-800 dark:text-${item.color}-200 border border-${item.color}-300 dark:border-${item.color}-700`}>
                    <strong>{item.cat}</strong> - {item.desc}
                  </span>
                ))}
              </div>
            </div>

            {/* Icon List */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Available Icons</h3>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded text-xs">
                <code className="text-gray-700 dark:text-gray-300">
                  Image, Box, ScanText, Layers, Sparkles, FileText, Brain, Zap, GitBranch, RefreshCw, Merge, Eye, Server, Database, Search, Settings, Upload, Download, Play, Pause
                </code>
              </div>
            </div>

            {/* Parameter Types */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Parameter Types</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {parameterTypes.map((item) => (
                  <div key={item.type} className="p-2 bg-gray-50 dark:bg-gray-800 rounded border">
                    <code className="text-sm font-bold text-purple-600 dark:text-purple-400">{item.type}</code>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">UI: {item.ui}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Example: {item.example}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* YAML Example */}
            <div className="bg-gray-900 dark:bg-gray-950 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">api_specs/myapi.yaml example</span>
                <span className="text-xs text-yellow-400">YAML</span>
              </div>
              <pre className="text-xs text-green-400 overflow-x-auto"><code>{yamlExample}</code></pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
