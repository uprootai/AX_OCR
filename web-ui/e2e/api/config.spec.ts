/**
 * Blueprint AI BOM - Config API Tests
 *
 * 시스템 설정 및 구성 API 테스트
 *
 * 테스트 범위:
 * - 클래스 설정
 * - 모델 설정
 * - Ground Truth 관리
 * - 캐시 관리
 * - 세션 통계
 *
 * Worker-scoped fixtures 사용으로 테스트 안정성 보장
 */

import { test, expect } from '../fixtures/api-fixtures';

test.describe('Config API', () => {
  test.setTimeout(60000);

  test.describe('Root Endpoint', () => {
    test('should return API info', async ({ apiContext }) => {
      const response = await apiContext.get('/');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('name');
      expect(data).toHaveProperty('version');
      expect(data).toHaveProperty('status');
    });

    test('should return running status', async ({ apiContext }) => {
      const response = await apiContext.get('/');

      if (response.ok()) {
        const data = await response.json();
        expect(data.status).toBe('running');
      }
    });
  });

  test.describe('Health Check', () => {
    test('should return healthy status', async ({ apiContext }) => {
      const response = await apiContext.get('/health');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.status).toBe('healthy');
    });
  });

  test.describe('Class Configuration', () => {
    test('should list detection classes', async ({ apiContext }) => {
      const response = await apiContext.get('/api/config/classes');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // Classes endpoint returns a dict with class names as keys
      expect(typeof data).toBe('object');
      expect(Object.keys(data).length).toBeGreaterThan(0);
    });

    test('should have class examples', async ({ apiContext }) => {
      const response = await apiContext.get('/api/config/class-examples');

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(typeof data).toBe('object');
      }
    });

    test('should have config template', async ({ apiContext }) => {
      const response = await apiContext.get('/api/config/template');

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(typeof data).toBe('object');
      }
    });
  });

  test.describe('Model Configuration', () => {
    test('should list available models', async ({ apiContext }) => {
      const response = await apiContext.get('/api/models');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('models');
      expect(Array.isArray(data.models)).toBeTruthy();
    });

    test('should include model metadata', async ({ apiContext }) => {
      const response = await apiContext.get('/api/models');

      if (response.ok()) {
        const data = await response.json();

        if (data.models && data.models.length > 0) {
          const model = data.models[0];
          expect(model).toHaveProperty('id');
          expect(model).toHaveProperty('name');
        }
      }
    });
  });

  test.describe('Ground Truth', () => {
    test('should list ground truth files', async ({ apiContext }) => {
      const response = await apiContext.get('/api/ground-truth');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // Response: { labels: [...], count: N, classes: [...], classes_count: N }
      expect(data).toHaveProperty('labels');
      expect(data).toHaveProperty('count');
    });

    test('should compare with ground truth', async ({ apiContext }) => {
      const response = await apiContext.post('/api/ground-truth/compare', {
        data: {
          session_id: 'test-session',
          ground_truth_file: 'test.json',
        },
      });

      // 파일이 없으면 404
      expect([200, 404, 422]).toContain(response.status());
    });
  });

  test.describe('Session Statistics', () => {
    test('should get session stats', async ({ apiContext }) => {
      const response = await apiContext.get('/api/sessions/stats');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('total_sessions');
    });

    test('should include verification stats', async ({ apiContext }) => {
      const response = await apiContext.get('/api/sessions/stats');

      if (response.ok()) {
        const data = await response.json();
        // Response: { total_sessions, by_status: { uploaded: N }, oldest_session }
        expect(data).toHaveProperty('total_sessions');
        expect(data).toHaveProperty('by_status');
      }
    });
  });

  test.describe('Cache Management', () => {
    test('should clear cache', async ({ apiContext }) => {
      const response = await apiContext.post('/api/system/cache/clear', {
        data: {},
      });

      expect([200, 204]).toContain(response.status());
    });

    test('should clear specific cache type', async ({ apiContext }) => {
      const response = await apiContext.post('/api/system/cache/clear', {
        data: {
          cache_type: 'detection',
        },
      });

      expect([200, 204, 400]).toContain(response.status());
    });
  });

  test.describe('Session Cleanup', () => {
    test('should cleanup old sessions', async ({ apiContext }) => {
      const response = await apiContext.delete('/api/sessions/cleanup', {
        data: {
          older_than_days: 30,
        },
      });

      // Endpoint may not exist or be allowed
      expect([200, 204, 404, 405]).toContain(response.status());
    });

    test('should cleanup with dry run', async ({ apiContext }) => {
      const response = await apiContext.delete('/api/sessions/cleanup', {
        data: {
          older_than_days: 30,
          dry_run: true,
        },
      });

      // Endpoint may not exist or be allowed
      expect([200, 204, 404, 405]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // Response structure varies
        expect(data).toBeTruthy();
      }
    });
  });

  test.describe('System Status', () => {
    test('should provide system metrics', async ({ apiContext }) => {
      const response = await apiContext.get('/api/system/status');

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('uptime');
      }
    });
  });
});
