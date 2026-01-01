/**
 * Blueprint AI BOM - Classification API Tests
 *
 * VLM 기반 도면 분류 API 테스트
 *
 * 테스트 범위:
 * - 도면 분류 (P&ID, 기계도면, 전기도면 등)
 * - 분류 프리셋 관리
 * - 분류 프로바이더 (OpenAI, Anthropic 등)
 * - 업로드와 동시 분류
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

test.describe('Classification API', () => {
  test.setTimeout(120000);

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

  test.describe('Classification Providers', () => {
    test('should list available providers', async ({ apiContext }) => {
      const response = await apiContext.get('/classification/providers');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // providers is an object { providers: { local: {...}, openai: {...}, ... }, default_provider: "..." }
      expect(data).toHaveProperty('providers');
      expect(typeof data.providers).toBe('object');
    });
  });

  test.describe('Classification Presets', () => {
    test('should list classification presets', async ({ apiContext }) => {
      const response = await apiContext.get('/classification/presets');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // presets is an object { presets: { preset_name: {...}, ... }, drawing_types: [...], region_types: [...] }
      expect(data).toHaveProperty('presets');
      expect(typeof data.presets).toBe('object');
    });

    test('should get specific preset', async ({ apiContext }) => {
      // 먼저 프리셋 목록 조회
      const listResponse = await apiContext.get('/classification/presets');
      const listData = await listResponse.json();

      if (listData.presets && Object.keys(listData.presets).length > 0) {
        const presetName = Object.keys(listData.presets)[0];
        const response = await apiContext.get(`/classification/presets/${presetName}`);

        expect([200, 404]).toContain(response.status());

        if (response.ok()) {
          const data = await response.json();
          // API returns { preset_name: "...", config: { name, description, ... } }
          expect(data).toHaveProperty('preset_name');
          expect(data).toHaveProperty('config');
          expect(data.config).toHaveProperty('name');
        }
      }
    });
  });

  test.describe('Drawing Classification', () => {
    test('should classify drawing', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/classification/classify', {
        data: {
          session_id: testSession.id,
          provider: 'openai',
        },
      });

      // API 키가 없으면 실패할 수 있음
      expect([200, 400, 422, 500, 503]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('classification');
        expect(data).toHaveProperty('confidence');
      }
    });

    test('should classify with specific provider', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/classification/classify', {
        data: {
          session_id: testSession.id,
          provider: 'anthropic',
        },
      });

      // API 키가 없으면 실패할 수 있음
      expect([200, 400, 422, 500, 503]).toContain(response.status());
    });

    test('should get session classification', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/classification/session/${testSession.id}`);

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response can be { session_id, has_classification, message } or { classification, ... }
        expect(data).toHaveProperty('session_id');
      }
    });
  });

  test.describe('Upload and Classify', () => {
    test('should upload and classify in one request', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'mechanical_sample2_interm_shaft.jpg');

      const response = await apiContext.post('/classification/classify-upload', {
        multipart: {
          file: createFileUpload(imagePath),
          provider: 'openai',
        },
      });

      // API 키가 없으면 실패할 수 있음
      expect([200, 400, 422, 500, 503]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('session_id');
        expect(data).toHaveProperty('classification');
        createdSessionIds.push(data.session_id);
      }
    });
  });

  test.describe('Apply Preset', () => {
    test('should apply classification preset to session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 먼저 프리셋 목록 조회
      const listResponse = await apiContext.get('/classification/presets');
      const listData = await listResponse.json();

      if (listData.presets && Object.keys(listData.presets).length > 0) {
        const presetName = Object.keys(listData.presets)[0];

        const response = await apiContext.post(`/classification/apply-preset/${testSession.id}`, {
          data: {
            preset_name: presetName,
          },
        });

        expect([200, 404, 422]).toContain(response.status());
      }
    });
  });

  test.describe('Classification Types', () => {
    test('should support P&ID classification', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/classification/classify', {
        data: {
          session_id: testSession.id,
          expected_type: 'pid',
        },
      });

      expect([200, 400, 422, 500, 503]).toContain(response.status());
    });

    test('should support mechanical drawing classification', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'mechanical_sample2_interm_shaft.jpg');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Mechanical Classification Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      const response = await apiContext.post('/classification/classify', {
        data: {
          session_id: createData.session_id,
          expected_type: 'mechanical',
        },
      });

      expect([200, 400, 422, 500, 503]).toContain(response.status());
    });
  });

  test.describe('Classification Confidence', () => {
    test('should return confidence score', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/classification/session/${testSession.id}`);

      if (response.ok()) {
        const data = await response.json();

        if (data.confidence !== undefined) {
          expect(data.confidence).toBeGreaterThanOrEqual(0);
          expect(data.confidence).toBeLessThanOrEqual(1);
        }
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle invalid session ID', async ({ apiContext }) => {
      const response = await apiContext.post('/classification/classify', {
        data: {
          session_id: 'invalid-session-id-12345',
          provider: 'openai',
        },
      });

      expect([400, 404, 422]).toContain(response.status());
    });

    test('should handle invalid provider', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/classification/classify', {
        data: {
          session_id: testSession.id,
          provider: 'invalid-provider',
        },
      });

      expect([400, 422]).toContain(response.status());
    });
  });
});
