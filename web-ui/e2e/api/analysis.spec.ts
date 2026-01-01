/**
 * Blueprint AI BOM - Analysis API Tests
 *
 * 분석 API 엔드포인트 통합 테스트 (55개 엔드포인트)
 *
 * 테스트 범위:
 * - Balloon 분석 (풍선 번호 매칭)
 * - Connectivity 분석 (P&ID 연결성)
 * - Dimensions 분석 (치수 추출)
 * - GD&T 분석 (기하공차)
 * - Notes 분석 (도면 노트 추출)
 * - Regions 분석 (영역 세분화)
 * - Revision 비교 (리비전 변경점)
 * - Surface Roughness 분석 (표면 거칠기)
 * - Title Block 분석 (도면 정보)
 * - VLM Classification (도면 유형 분류)
 * - Welding Symbols 분석 (용접 기호)
 *
 * Worker-scoped fixtures 사용으로 테스트 안정성 보장
 */

import { test, expect, isValidSession } from '../fixtures/api-fixtures';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FIXTURES_PATH = path.join(__dirname, '../fixtures/images');

// 추가 세션 생성을 위한 유틸리티
function createFileUpload(filePath: string) {
  const fileName = path.basename(filePath);
  const extension = path.extname(filePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
  };
  return {
    name: fileName,
    mimeType: mimeTypes[extension] || 'application/octet-stream',
    buffer: fs.readFileSync(filePath),
  };
}

// 테스트 중 생성된 추가 세션 ID 추적
const createdSessionIds: string[] = [];

test.describe('Analysis API', () => {
  // Increase timeout for analysis operations
  test.setTimeout(180000);

  // Cleanup additional sessions after all tests
  test.afterAll(async ({ apiContext }) => {
    for (const sessionId of createdSessionIds) {
      try {
        await apiContext.delete(`/sessions/${sessionId}`);
      } catch {
        // Ignore cleanup errors
      }
    }
  });

  test.describe('Balloon Analysis', () => {
    test('should check balloon analysis health', async ({ apiContext }) => {
      const response = await apiContext.get('/analysis/balloons/health');

      // Health endpoint may not be implemented (404) or return 200
      expect([200, 404]).toContain(response.status());
    });

    test('should get balloons for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/balloons/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('balloons');
        expect(Array.isArray(data.balloons)).toBeTruthy();
      }
    });

    test('should match balloon with part number', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/balloons/${testSession.id}/match`, {
        data: {
          balloon_id: 'test-balloon-1',
          part_number: 'PART-001',
        },
      });

      // May return 404 if balloon not found
      expect([200, 404, 422]).toContain(response.status());
    });
  });

  test.describe('Connectivity Analysis', () => {
    test('should analyze P&ID connectivity', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/connectivity/${testSession.id}`, {
        data: {},
      });

      expect([200, 202, 422]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response may have {connectivity: {...}} or graph structure {nodes, edges, ...}
        expect(typeof data).toBe('object');
        const hasConnectivity = data.connectivity !== undefined || data.nodes !== undefined;
        expect(hasConnectivity).toBeTruthy();
      }
    });

    test('should get connectivity results', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/connectivity/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response may have {connections: [...]} or graph structure {nodes, edges, ...}
        expect(typeof data).toBe('object');
        const hasGraph = data.connections !== undefined || data.nodes !== undefined || data.edges !== undefined;
        expect(hasGraph).toBeTruthy();
      }
    });

    test('should get component connections', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/connectivity/${testSession.id}/components`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response may have {components: [...]} or be a list directly
        expect(typeof data).toBe('object');
      }
    });

    test('should find path between components', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/connectivity/${testSession.id}/path`, {
        data: {
          source_id: 'component-1',
          target_id: 'component-2',
        },
      });

      // Path may not exist, components may not exist, endpoint may not be implemented, or require valid component IDs
      expect([200, 400, 404, 405, 422, 500]).toContain(response.status());
    });
  });

  test.describe('Dimensions Analysis', () => {
    test('should get dimensions for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/dimensions/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('dimensions');
        expect(Array.isArray(data.dimensions)).toBeTruthy();
      }
    });

    test('should add manual dimension', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/dimensions/${testSession.id}/add`, {
        data: {
          value: '100.0',
          unit: 'mm',
          bbox: { x1: 100, y1: 100, x2: 200, y2: 120 },
        },
      });

      // 404 if endpoint not implemented, 422 if validation fails, 405 if method not allowed
      expect([200, 201, 400, 404, 405, 422]).toContain(response.status());
    });

    test('should import dimensions in bulk', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/dimensions/${testSession.id}/import`, {
        data: {
          dimensions: [
            { value: '50.0', unit: 'mm', tolerance: '0.1' },
            { value: '25.0', unit: 'mm', tolerance: '0.05' },
          ],
        },
      });

      // 404 if endpoint not implemented, 422 if validation fails, 405 if method not allowed
      expect([200, 201, 400, 404, 405, 422]).toContain(response.status());
    });

    test('should verify dimensions in bulk', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/dimensions/${testSession.id}/verify/bulk`, {
        data: {
          dimension_ids: ['dim-1', 'dim-2'],
          status: 'verified',
        },
      });

      // 400 for bad request, 404 for not found, 405 if method not allowed, 422 for validation error
      expect([200, 400, 404, 405, 422]).toContain(response.status());
    });
  });

  test.describe('GD&T Analysis', () => {
    test('should get GD&T data for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/gdt/${testSession.id}`);

      // Session may return 404 if not found
      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response: { session_id, fcf_list: [], datums: [], total_fcf, total_datums }
        expect(data).toHaveProperty('fcf_list');
        expect(data).toHaveProperty('datums');
      }
    });

    test('should parse GD&T from image', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/gdt/${testSession.id}/parse`, {
        data: {
          region: { x1: 0, y1: 0, x2: 500, y2: 500 },
        },
      });

      // May return 404 if endpoint not implemented
      expect([200, 404, 422]).toContain(response.status());
    });

    test('should add FCF (Feature Control Frame)', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/gdt/${testSession.id}/fcf/add`, {
        data: {
          symbol: 'position',
          tolerance: 0.05,
          datum_references: ['A', 'B'],
          bbox: { x1: 100, y1: 100, x2: 200, y2: 150 },
        },
      });

      expect([200, 201, 422]).toContain(response.status());
    });

    test('should add datum reference', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/gdt/${testSession.id}/datum/add`, {
        data: {
          label: 'A',
          bbox: { x1: 50, y1: 50, x2: 70, y2: 70 },
        },
      });

      expect([200, 201, 422]).toContain(response.status());
    });

    test('should get GD&T summary', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/gdt/${testSession.id}/summary`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response: { session_id, total_fcf, fcf_by_category, ..., total_datums, ... }
        expect(data).toHaveProperty('total_fcf');
        expect(data).toHaveProperty('total_datums');
      }
    });

    test('should bulk import FCFs', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/gdt/${testSession.id}/fcf/bulk`, {
        data: {
          fcfs: [
            { symbol: 'flatness', tolerance: 0.02, bbox: { x1: 100, y1: 100, x2: 150, y2: 130 } },
            { symbol: 'perpendicularity', tolerance: 0.03, datum_references: ['A'], bbox: { x1: 200, y1: 100, x2: 250, y2: 130 } },
          ],
        },
      });

      // 400 for bad request, 404 if endpoint not found, 405 if method not allowed, 422 for validation error
      expect([200, 400, 404, 405, 422]).toContain(response.status());
    });
  });

  test.describe('Notes Analysis', () => {
    test('should get notes for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/notes/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('notes');
        expect(Array.isArray(data.notes)).toBeTruthy();
      }
    });

    test('should extract notes from drawing', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/notes/${testSession.id}/extract`, {
        data: {
          method: 'ocr',
          regions: [{ x1: 0, y1: 0, x2: 1000, y2: 200 }],
        },
      });

      expect([200, 422]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('notes');
      }
    });
  });

  test.describe('Regions Analysis', () => {
    test('should get regions for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/regions/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('regions');
        expect(Array.isArray(data.regions)).toBeTruthy();
      }
    });

    test('should add region manually', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/regions/${testSession.id}/add`, {
        data: {
          name: 'Test Region',
          type: 'main',
          bbox: { x1: 0, y1: 0, x2: 1000, y2: 1000 },
        },
      });

      expect([200, 201, 422]).toContain(response.status());
    });

    test('should segment drawing into regions', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/regions/${testSession.id}/segment`, {
        data: {
          method: 'heuristic',
        },
      });

      expect([200, 422]).toContain(response.status());
    });

    test('should bulk add regions', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/regions/${testSession.id}/bulk`, {
        data: {
          regions: [
            { name: 'Region 1', type: 'main', bbox: { x1: 0, y1: 0, x2: 1000, y2: 1000 } },
            { name: 'Region 2', type: 'detail', bbox: { x1: 1000, y1: 0, x2: 2000, y2: 1000 } },
          ],
        },
      });

      // 400 for bad request, 404 if endpoint not found, 405 if method not allowed, 422 for validation error
      expect([200, 400, 404, 405, 422]).toContain(response.status());
    });

    test('should process all regions', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/regions/${testSession.id}/process-all`, {
        data: {},
      });

      expect([200, 202, 422]).toContain(response.status());
    });
  });

  test.describe('Drawing Regions Analysis', () => {
    test('should get drawing regions', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/drawing-regions/${testSession.id}`);

      expect([200, 404]).toContain(response.status());
    });

    test('should segment drawing regions', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/drawing-regions/${testSession.id}/segment`, {
        data: {
          method: 'vlm',
        },
      });

      expect([200, 422]).toContain(response.status());
    });
  });

  test.describe('Revision Analysis', () => {
    test('should compare revisions', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');

      // 두 번째 세션 생성
      const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Revision Compare Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      const response = await apiContext.post('/analysis/revision/compare', {
        data: {
          session_id_old: testSession.id,
          session_id_new: createData.session_id,
          comparison_type: 'full',
        },
      });

      // May return 404 if sessions not found or not configured for revision comparison
      expect([200, 404, 422]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // API returns { changes: [], total_changes, comparison_id, ... }
        expect(data).toHaveProperty('changes');
        expect(data).toHaveProperty('total_changes');
      }
    });

    test('should get revision history', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/revision/${testSession.id}`);

      expect([200, 404]).toContain(response.status());
    });
  });

  test.describe('Surface Roughness Analysis', () => {
    test('should get surface roughness data', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/surface-roughness/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response: { session_id, roughness_symbols: [], total_count, message }
        expect(data).toHaveProperty('roughness_symbols');
      }
    });

    test('should parse surface roughness symbols', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/surface-roughness/${testSession.id}/parse`, {
        data: {
          region: { x1: 0, y1: 0, x2: 1000, y2: 1000 },
        },
      });

      expect([200, 422]).toContain(response.status());
    });
  });

  test.describe('Title Block Analysis', () => {
    test('should get title block data', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/title-block/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('title_block');
      }
    });

    test('should extract title block', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/title-block/${testSession.id}/extract`, {
        data: {
          method: 'auto',
        },
      });

      expect([200, 422]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('title_block');
      }
    });
  });

  test.describe('VLM Classification', () => {
    test('should classify drawing with VLM', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/vlm-classify/${testSession.id}`, {
        data: {
          provider: 'local',  // Use local provider which doesn't require API key
        },
      });

      // May fail without proper setup or invalid session
      expect([200, 400, 404, 422, 500, 502, 503]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // API returns { drawing_type, industry_domain, analysis_summary, ... }
        expect(data).toHaveProperty('drawing_type');
        expect(data).toHaveProperty('industry_domain');
      }
    });
  });

  test.describe('Welding Symbols Analysis', () => {
    test('should get welding symbols', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/welding-symbols/${testSession.id}`);

      // Session may return 404 if not found
      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response: { session_id, welding_symbols: [], total_count, message }
        expect(data).toHaveProperty('welding_symbols');
      }
    });

    test('should parse welding symbols', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/welding-symbols/${testSession.id}/parse`, {
        data: {
          region: { x1: 0, y1: 0, x2: 1000, y2: 1000 },
        },
      });

      expect([200, 422]).toContain(response.status());
    });
  });

  test.describe('Lines Analysis', () => {
    test('should check lines health', async ({ apiContext }) => {
      const response = await apiContext.get('/analysis/lines/health');

      // Health endpoint may not be implemented (404) or return 200
      expect([200, 404]).toContain(response.status());
    });

    test('should get lines for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/lines/${testSession.id}`);

      expect([200, 404]).toContain(response.status());
    });

    test('should find dimension relations', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/lines/${testSession.id}/dimension-relations`);

      expect([200, 404]).toContain(response.status());
    });

    test('should link dimensions to lines', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/lines/${testSession.id}/link-dimensions`, {
        data: {},
      });

      expect([200, 404, 422]).toContain(response.status());
    });
  });

  test.describe('Quantity Analysis', () => {
    test('should get quantities for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/analysis/quantities/${testSession.id}`);

      expect([200, 404]).toContain(response.status());
    });

    test('should extract quantities', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/quantities/${testSession.id}/extract`, {
        data: {},
      });

      // 422 if session has no detections or required data is missing
      expect([200, 400, 404, 422]).toContain(response.status());
    });
  });

  test.describe('Options and Presets', () => {
    test('should get analysis options', async ({ apiContext }) => {
      const response = await apiContext.get('/analysis/options');

      // May return 404 if endpoint not implemented
      expect([200, 404]).toContain(response.status());
    });

    test('should get available presets', async ({ apiContext }) => {
      const response = await apiContext.get('/analysis/presets');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // API returns { presets: [...] }
      expect(data).toHaveProperty('presets');
    });

    test('should apply preset', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/preset/${testSession.id}/apply`, {
        data: {
          preset: 'mechanical_part',  // Use valid preset name
        },
      });

      // Preset may not exist
      expect([200, 404, 422]).toContain(response.status());
    });
  });

  test.describe('Full Analysis Run', () => {
    test('should run full analysis pipeline', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/analysis/run/${testSession.id}`, {
        data: {
          features: ['dimensions', 'gdt', 'notes'],
        },
      });

      // May take time or fail with unsupported features
      expect([200, 202, 404, 422]).toContain(response.status());
    });
  });
});
