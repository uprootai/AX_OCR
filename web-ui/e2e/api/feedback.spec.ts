/**
 * Blueprint AI BOM - Feedback API Tests
 *
 * 학습 데이터 피드백 및 내보내기 API 테스트
 *
 * 테스트 범위:
 * - 피드백 건강 체크
 * - 세션별 피드백 조회
 * - 피드백 통계
 * - YOLO 학습 데이터 내보내기
 * - 내보내기 이력 조회
 *
 * Worker-scoped fixtures 사용으로 테스트 안정성 보장
 */

import { test, expect, isValidSession } from '../fixtures/api-fixtures';

test.describe('Feedback API', () => {
  test.setTimeout(120000);

  test.describe('Health Check', () => {
    test('should return feedback service health', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/health');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('status');
    });
  });

  test.describe('Feedback Sessions', () => {
    test('should list feedback sessions', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/sessions');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('sessions');
      expect(Array.isArray(data.sessions)).toBeTruthy();
    });

    test('should filter sessions by verification status', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/sessions', {
        params: {
          status: 'verified',
        },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should paginate sessions', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/sessions', {
        params: {
          page: 1,
          limit: 10,
        },
      });

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.sessions.length).toBeLessThanOrEqual(10);
    });
  });

  test.describe('Feedback Statistics', () => {
    test('should get feedback stats', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/stats');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // Response: { total_sessions, total_detections, approved_count, rejected_count, ... }
      expect(data).toHaveProperty('total_sessions');
      expect(data).toHaveProperty('total_detections');
      expect(data).toHaveProperty('approved_count');
    });

    test('should get stats by class', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/stats', {
        params: {
          group_by: 'class',
        },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should get stats by date range', async ({ apiContext }) => {
      const today = new Date().toISOString().split('T')[0];
      const response = await apiContext.get('/feedback/stats', {
        params: {
          start_date: today,
          end_date: today,
        },
      });

      expect(response.ok()).toBeTruthy();
    });
  });

  test.describe('YOLO Export', () => {
    test('should export YOLO training data', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/feedback/export/yolo', {
        data: {
          session_ids: [testSession.id],
          format: 'yolov8',
        },
      });

      // 404 when no verified sessions found
      expect([200, 202, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('export_id');
      }
    });

    test('should export with class filter', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/feedback/export/yolo', {
        data: {
          session_ids: [testSession.id],
          classes: ['valve', 'pump', 'tank'],
          format: 'yolov8',
        },
      });

      // 404 when no verified sessions found
      expect([200, 202, 404]).toContain(response.status());
    });

    test('should export with train/val split', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/feedback/export/yolo', {
        data: {
          session_ids: [testSession.id],
          train_ratio: 0.8,
          val_ratio: 0.2,
          format: 'yolov8',
        },
      });

      // 404 when no verified sessions found
      expect([200, 202, 404]).toContain(response.status());
    });

    test('should export all verified sessions', async ({ apiContext }) => {
      const response = await apiContext.post('/feedback/export/yolo', {
        data: {
          verified_only: true,
          format: 'yolov8',
        },
      });

      // 404 when no verified sessions found
      expect([200, 202, 404]).toContain(response.status());
    });
  });

  test.describe('Export History', () => {
    test('should list export history', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/exports');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('exports');
      expect(Array.isArray(data.exports)).toBeTruthy();
    });

    test('should filter exports by status', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/exports', {
        params: {
          status: 'completed',
        },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should get recent exports', async ({ apiContext }) => {
      const response = await apiContext.get('/feedback/exports', {
        params: {
          limit: 5,
          order: 'desc',
        },
      });

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.exports.length).toBeLessThanOrEqual(5);
    });
  });

  test.describe('Export Validation', () => {
    test('should validate export format', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post('/feedback/export/yolo', {
        data: {
          session_ids: [testSession.id],
          format: 'invalid-format',
        },
      });

      // 404 when no verified sessions, 422 for validation error
      expect([400, 404, 422]).toContain(response.status());
    });

    test('should handle empty session list', async ({ apiContext }) => {
      const response = await apiContext.post('/feedback/export/yolo', {
        data: {
          session_ids: [],
          format: 'yolov8',
        },
      });

      // 404 when no verified sessions, 422 for validation error
      expect([400, 404, 422]).toContain(response.status());
    });

    test('should handle invalid session ID', async ({ apiContext }) => {
      const response = await apiContext.post('/feedback/export/yolo', {
        data: {
          session_ids: ['invalid-session-id'],
          format: 'yolov8',
        },
      });

      expect([400, 404, 422]).toContain(response.status());
    });
  });
});
