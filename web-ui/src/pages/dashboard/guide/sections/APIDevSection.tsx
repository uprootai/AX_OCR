import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { Wrench } from 'lucide-react';

interface APIDevSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function APIDevSection({ sectionRef }: APIDevSectionProps) {
  const infoExample = `{
  "id": "myapi",
  "name": "MyAPI",
  "version": "1.0.0",
  "category": "ocr",
  "description": "My Custom API",
  "icon": "ScanText",
  "color": "#8b5cf6",
  "parameters": [
    { "name": "visualize", "type": "boolean", "default": true }
  ]
}`;

  return (
    <section
      id="apidev"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card className="border-2 border-indigo-300 dark:border-indigo-700">
        <CardHeader className="bg-indigo-50 dark:bg-indigo-900/20">
          <CardTitle className="flex items-center text-indigo-900 dark:text-indigo-100">
            <Wrench className="w-5 h-5 mr-2" />
            API Development Guide
            <Badge className="ml-3 bg-indigo-600">Developer</Badge>
          </CardTitle>
          <p className="text-sm text-indigo-800 dark:text-indigo-200 mt-2">
            Custom API to Built-in API unified integration workflow
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Core Principle */}
            <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded">
              <h4 className="font-bold text-amber-900 dark:text-amber-100 mb-2">Core Principle: "One Flow, One Path"</h4>
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Custom API and Built-in API are <strong>not separate options</strong>. All APIs go through the same path to production.
              </p>
              <div className="mt-2 flex items-center gap-2 text-xs text-amber-700 dark:text-amber-300">
                <code className="bg-amber-100 dark:bg-amber-900 px-2 py-1 rounded">Custom API = Test/Validate phase</code>
                <span>-&gt;</span>
                <code className="bg-amber-100 dark:bg-amber-900 px-2 py-1 rounded">Built-in API = Production phase</code>
              </div>
            </div>

            {/* 5-Step Process */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">5-Step Integration Process</h3>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded text-center">
                  <div className="text-2xl mb-1">[1]</div>
                  <div className="text-sm font-medium text-blue-900 dark:text-blue-100">Implement API Server</div>
                  <div className="text-xs text-blue-700 dark:text-blue-300">/api/v1/info required!</div>
                </div>
                <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded text-center">
                  <div className="text-2xl mb-1">[2]</div>
                  <div className="text-sm font-medium text-green-900 dark:text-green-100">Run Docker</div>
                  <div className="text-xs text-green-700 dark:text-green-300">docker-compose up</div>
                </div>
                <div className="p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded text-center">
                  <div className="text-2xl mb-1">[3]</div>
                  <div className="text-sm font-medium text-purple-900 dark:text-purple-100">Register in Dashboard</div>
                  <div className="text-xs text-purple-700 dark:text-purple-300">Enter URL -&gt; Auto discover</div>
                </div>
                <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded text-center">
                  <div className="text-2xl mb-1">[4]</div>
                  <div className="text-sm font-medium text-orange-900 dark:text-orange-100">Export</div>
                  <div className="text-xs text-orange-700 dark:text-orange-300">Auto-generate code</div>
                </div>
                <div className="p-3 bg-pink-50 dark:bg-pink-900/20 border border-pink-200 dark:border-pink-800 rounded text-center">
                  <div className="text-2xl mb-1">[5]</div>
                  <div className="text-sm font-medium text-pink-900 dark:text-pink-100">Production Ready</div>
                  <div className="text-xs text-pink-700 dark:text-pink-300">Custom API OFF</div>
                </div>
              </div>
            </div>

            {/* Required Endpoints */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Required Endpoints</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                  <code className="text-sm font-mono text-green-600 dark:text-green-400">GET /health</code>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Basic health check</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                  <code className="text-sm font-mono text-green-600 dark:text-green-400">GET /api/v1/health</code>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">API version health check</p>
                </div>
                <div className="p-3 bg-indigo-50 dark:bg-indigo-900/30 rounded border border-indigo-300 dark:border-indigo-700">
                  <code className="text-sm font-mono text-indigo-600 dark:text-indigo-400">GET /api/v1/info</code>
                  <Badge className="ml-2 bg-indigo-600 text-xs">Required</Badge>
                  <p className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">Metadata for auto-discovery</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                  <code className="text-sm font-mono text-green-600 dark:text-green-400">POST /api/v1/process</code>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Actual processing logic</p>
                </div>
              </div>
            </div>

            {/* /api/v1/info Response Example */}
            <div className="bg-gray-900 dark:bg-gray-950 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">GET /api/v1/info response example</span>
                <span className="text-xs text-green-400">JSON</span>
              </div>
              <pre className="text-xs text-green-400 overflow-x-auto"><code>{infoExample}</code></pre>
            </div>

            {/* Export Feature */}
            <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded-lg">
              <h4 className="font-semibold text-cyan-900 dark:text-cyan-100 mb-2 flex items-center">
                <span className="mr-2">[Export]</span> Export Button -&gt; Auto Generated Code
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                  <div className="font-medium text-cyan-800 dark:text-cyan-200">YAML Spec</div>
                  <code className="text-cyan-600 dark:text-cyan-400">api_specs/{'{id}'}.yaml</code>
                </div>
                <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                  <div className="font-medium text-cyan-800 dark:text-cyan-200">Node Definition</div>
                  <code className="text-cyan-600 dark:text-cyan-400">nodeDefinitions.ts</code>
                </div>
                <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                  <div className="font-medium text-cyan-800 dark:text-cyan-200">Docker</div>
                  <code className="text-cyan-600 dark:text-cyan-400">docker-compose.yml</code>
                </div>
                <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded text-center">
                  <div className="font-medium text-cyan-800 dark:text-cyan-200">Test</div>
                  <code className="text-cyan-600 dark:text-cyan-400">test_{'{id}'}.py</code>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
