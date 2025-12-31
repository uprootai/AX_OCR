import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { TestTube2 } from 'lucide-react';

interface TestingSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function TestingSection({ sectionRef }: TestingSectionProps) {
  const pytestExample = `import pytest
import httpx

API_URL = "http://localhost:5020"

def test_health():
    r = httpx.get(f"{API_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_info():
    r = httpx.get(f"{API_URL}/api/v1/info")
    assert r.status_code == 200
    info = r.json()
    assert "id" in info
    assert "category" in info

def test_process():
    with open("test.jpg", "rb") as f:
        r = httpx.post(
            f"{API_URL}/api/v1/process",
            files={"file": f}
        )
    assert r.status_code == 200
    assert r.json()["success"] is True`;

  return (
    <section
      id="testing"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card className="border-2 border-rose-300 dark:border-rose-700">
        <CardHeader className="bg-rose-50 dark:bg-rose-900/20">
          <CardTitle className="flex items-center text-rose-900 dark:text-rose-100">
            <TestTube2 className="w-5 h-5 mr-2" />
            API Validation Test Guide
            <Badge className="ml-3 bg-rose-600">QA</Badge>
          </CardTitle>
          <p className="text-sm text-rose-800 dark:text-rose-200 mt-2">
            Custom API testing - validation checklist before Built-in conversion
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Test Phases */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">3-Phase Test Process</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <h4 className="font-bold text-blue-900 dark:text-blue-100 mb-2">Phase 1: API Server Test</h4>
                  <ul className="text-xs space-y-1 text-blue-800 dark:text-blue-200">
                    <li>[OK] /health endpoint response</li>
                    <li>[OK] /api/v1/info metadata returned</li>
                    <li>[OK] /api/v1/process basic processing</li>
                    <li>[OK] Error case handling</li>
                  </ul>
                </div>
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <h4 className="font-bold text-green-900 dark:text-green-100 mb-2">Phase 2: UI Integration Test</h4>
                  <ul className="text-xs space-y-1 text-green-800 dark:text-green-200">
                    <li>[OK] API discovered in Dashboard</li>
                    <li>[OK] BlueprintFlow node displayed</li>
                    <li>[OK] Parameter UI works correctly</li>
                    <li>[OK] Workflow execution succeeds</li>
                  </ul>
                </div>
                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                  <h4 className="font-bold text-purple-900 dark:text-purple-100 mb-2">Phase 3: Production Validation</h4>
                  <ul className="text-xs space-y-1 text-purple-800 dark:text-purple-200">
                    <li>[OK] YAML spec validation</li>
                    <li>[OK] pytest tests pass</li>
                    <li>[OK] Custom/Built-in switch confirmed</li>
                    <li>[OK] Existing workflow compatibility</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* curl Tests */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Bash Test Commands</h3>
              <div className="space-y-3">
                <div className="bg-gray-900 dark:bg-gray-950 p-3 rounded-lg">
                  <div className="text-xs text-gray-400 mb-1"># 1. Health check</div>
                  <code className="text-xs text-green-400">curl http://localhost:5020/health</code>
                </div>
                <div className="bg-gray-900 dark:bg-gray-950 p-3 rounded-lg">
                  <div className="text-xs text-gray-400 mb-1"># 2. API info check</div>
                  <code className="text-xs text-green-400">curl http://localhost:5020/api/v1/info | jq</code>
                </div>
                <div className="bg-gray-900 dark:bg-gray-950 p-3 rounded-lg">
                  <div className="text-xs text-gray-400 mb-1"># 3. Image processing test</div>
                  <code className="text-xs text-green-400">curl -X POST http://localhost:5020/api/v1/process \<br/>  -F "file=@test.jpg" -F "visualize=true"</code>
                </div>
              </div>
            </div>

            {/* pytest Tests */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">pytest Automated Tests</h3>
              <div className="bg-gray-900 dark:bg-gray-950 p-4 rounded-lg">
                <div className="text-xs text-gray-400 mb-2"># gateway-api/tests/test_myapi.py</div>
                <pre className="text-xs text-green-400 overflow-x-auto"><code>{pytestExample}</code></pre>
              </div>
              <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                <code>cd gateway-api && pytest tests/test_myapi.py -v</code>
              </div>
            </div>

            {/* Checklist */}
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-3">Final Checklist Before Built-in Conversion</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h5 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">API Server</h5>
                  <ul className="space-y-1 text-yellow-700 dark:text-yellow-300 text-xs">
                    <li>[ ] All endpoints respond correctly</li>
                    <li>[ ] Error cases handled</li>
                    <li>[ ] Overlay image generated</li>
                    <li>[ ] No timeout (within 60s)</li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">BlueprintFlow Integration</h5>
                  <ul className="space-y-1 text-yellow-700 dark:text-yellow-300 text-xs">
                    <li>[ ] Displayed in node palette</li>
                    <li>[ ] Can connect to other nodes</li>
                    <li>[ ] Works correctly in parallel execution</li>
                    <li>[ ] Result data format is correct</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
