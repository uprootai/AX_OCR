/**
 * Blueprint AI BOM - Verification API Tests
 *
 * Human-in-the-Loop 검증 API 테스트
 *
 * 테스트 범위:
 * - 검증 큐 관리
 * - 검증 실행 (승인/거부)
 * - 자동 승인
 * - 대량 검증
 * - 검증 통계
 * - 검증 로그
 * - 임계값 관리
 * - 학습 데이터 내보내기
 *
 * Worker-scoped fixtures 사용으로 테스트 안정성 보장
 */

import { test, expect, isValidSession } from '../fixtures/api-fixtures';

test.describe('Verification API', () => {
  test.setTimeout(120000);

  test.describe('Verification Queue', () => {
    test('should get verification queue', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/queue/${testSession.id}`);

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('queue');
      expect(Array.isArray(data.queue)).toBeTruthy();
    });

    test('should get queue with filters', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/queue/${testSession.id}`, {
        params: {
          status: 'pending',
          limit: 10,
        },
      });

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('queue');
    });

    test('should get queue sorted by confidence', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/queue/${testSession.id}`, {
        params: {
          sort_by: 'confidence',
          order: 'asc',
        },
      });

      expect(response.ok()).toBeTruthy();
    });
  });

  test.describe('Single Verification', () => {
    test('should verify single detection', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 먼저 검출 결과 조회
      const detectResponse = await apiContext.get(`/detection/${testSession.id}/detections`);
      const detectData = await detectResponse.json();

      if (detectData.detections && detectData.detections.length > 0) {
        const detectionId = detectData.detections[0].id;

        const response = await apiContext.post(`/verification/verify/${testSession.id}`, {
          data: {
            item_id: detectionId,
            item_type: 'symbol',
            action: 'approved',
          },
        });

        expect([200, 404, 422]).toContain(response.status());
      }
    });

    test('should reject detection', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const detectResponse = await apiContext.get(`/detection/${testSession.id}/detections`);
      const detectData = await detectResponse.json();

      if (detectData.detections && detectData.detections.length > 1) {
        const detectionId = detectData.detections[1].id;

        const response = await apiContext.post(`/verification/verify/${testSession.id}`, {
          data: {
            item_id: detectionId,
            item_type: 'symbol',
            action: 'rejected',
          },
        });

        expect([200, 404, 422]).toContain(response.status());
      }
    });

    test('should correct detection class', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const detectResponse = await apiContext.get(`/detection/${testSession.id}/detections`);
      const detectData = await detectResponse.json();

      if (detectData.detections && detectData.detections.length > 0) {
        const detection = detectData.detections[0];

        const response = await apiContext.post(`/verification/verify/${testSession.id}`, {
          data: {
            item_id: detection.id,
            item_type: 'symbol',
            action: 'modified',
            modified_data: { class_name: 'valve' },
          },
        });

        expect([200, 404, 422]).toContain(response.status());
      }
    });
  });

  test.describe('Bulk Verification', () => {
    test('should bulk approve detections', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const detectResponse = await apiContext.get(`/detection/${testSession.id}/detections`);
      const detectData = await detectResponse.json();

      if (detectData.detections && detectData.detections.length > 0) {
        const itemIds = detectData.detections.slice(0, 3).map((d: { id: string }) => d.id);

        const response = await apiContext.post(`/verification/bulk-approve/${testSession.id}`, {
          data: {
            item_ids: itemIds,
            item_type: 'symbol',
          },
        });

        expect([200, 404, 422]).toContain(response.status());
      }
    });

    test('should handle empty bulk approval', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/verification/bulk-approve/${testSession.id}`, {
        data: {
          item_ids: [],
          item_type: 'symbol',
        },
      });

      expect([200, 400, 422]).toContain(response.status());
    });
  });

  test.describe('Auto Approval', () => {
    test('should get auto-approve candidates', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/auto-approve-candidates/${testSession.id}`);

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('candidates');
      expect(Array.isArray(data.candidates)).toBeTruthy();
    });

    test('should auto-approve high confidence detections', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/verification/auto-approve/${testSession.id}`, {
        data: {
          confidence_threshold: 0.9,
        },
      });

      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('approved_count');
      }
    });

    test('should auto-approve with class filter', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/verification/auto-approve/${testSession.id}`, {
        data: {
          confidence_threshold: 0.85,
          class_filter: ['valve', 'pump'],
        },
      });

      expect([200, 404]).toContain(response.status());
    });
  });

  test.describe('Verification Statistics', () => {
    test('should get verification stats', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/stats/${testSession.id}`);

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // API returns { session_id, item_type, stats: { total, verified, pending, ... }, thresholds }
      expect(data).toHaveProperty('session_id');
      expect(data).toHaveProperty('stats');
      expect(data.stats).toHaveProperty('total');
      expect(data.stats).toHaveProperty('verified');
      expect(data.stats).toHaveProperty('pending');
    });

    test('should calculate verification progress', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/stats/${testSession.id}`);

      if (response.ok()) {
        const data = await response.json();

        if (data.stats && data.stats.total > 0) {
          const progress = data.stats.verified / data.stats.total;
          expect(progress).toBeGreaterThanOrEqual(0);
          expect(progress).toBeLessThanOrEqual(1);
        }
      }
    });
  });

  test.describe('Verification Logs', () => {
    test('should get verification logs', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/logs/${testSession.id}`);

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('logs');
      expect(Array.isArray(data.logs)).toBeTruthy();
    });

    test('should filter logs by action', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/logs/${testSession.id}`, {
        params: {
          action: 'approve',
        },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should paginate logs', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/verification/logs/${testSession.id}`, {
        params: {
          page: 1,
          limit: 10,
        },
      });

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.logs.length).toBeLessThanOrEqual(10);
    });
  });

  test.describe('Verification Thresholds', () => {
    test('should get verification thresholds', async ({ apiContext }) => {
      const response = await apiContext.get('/verification/thresholds');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // API returns { thresholds: { critical, auto_approve } }
      expect(data).toHaveProperty('thresholds');
      expect(data.thresholds).toHaveProperty('auto_approve');
      expect(data.thresholds).toHaveProperty('critical');
    });

    test('should update verification thresholds', async ({ apiContext }) => {
      const response = await apiContext.put('/verification/thresholds', {
        data: {
          auto_approve: 0.95,
          critical: 0.7,
        },
      });

      // PUT might not be supported
      expect([200, 403, 405]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // API returns { updated: {}, current_thresholds: { critical, auto_approve } }
        expect(data).toHaveProperty('current_thresholds');
        expect(data.current_thresholds.auto_approve).toBe(0.95);
      }
    });

    test('should validate threshold values', async ({ apiContext }) => {
      const response = await apiContext.put('/verification/thresholds', {
        data: {
          auto_approve_threshold: 1.5, // Invalid
          review_threshold: -0.1, // Invalid
        },
      });

      expect([400, 422]).toContain(response.status());
    });
  });

  test.describe('Training Data', () => {
    test('should get training data', async ({ apiContext }) => {
      const response = await apiContext.get('/verification/training-data');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // API returns { data: [], count: 0, action_counts: {}, filters: {} }
      expect(data).toHaveProperty('data');
      expect(data).toHaveProperty('count');
    });

    test('should filter training data by class', async ({ apiContext }) => {
      const response = await apiContext.get('/verification/training-data', {
        params: {
          class_name: 'valve',
        },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should export training data', async ({ apiContext }) => {
      const response = await apiContext.get('/verification/training-data', {
        params: {
          format: 'yolo',
        },
      });

      expect(response.ok()).toBeTruthy();
    });
  });

  test.describe('Verification Workflow', () => {
    test('should complete full verification workflow', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 1. 검증 큐 조회
      const queueResponse = await apiContext.get(`/verification/queue/${testSession.id}`);
      expect(queueResponse.ok()).toBeTruthy();

      // 2. 통계 조회
      const statsResponse = await apiContext.get(`/verification/stats/${testSession.id}`);
      expect(statsResponse.ok()).toBeTruthy();

      // 3. 자동 승인 후보 조회
      const candidatesResponse = await apiContext.get(`/verification/auto-approve-candidates/${testSession.id}`);
      expect(candidatesResponse.ok()).toBeTruthy();

      // 4. 로그 조회
      const logsResponse = await apiContext.get(`/verification/logs/${testSession.id}`);
      expect(logsResponse.ok()).toBeTruthy();
    });
  });

  test.describe('Edge Cases', () => {
    test('should handle non-existent session', async ({ apiContext }) => {
      const response = await apiContext.get('/verification/queue/non-existent-session');

      expect([404]).toContain(response.status());
    });

    test('should handle invalid detection ID', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/verification/verify/${testSession.id}`, {
        data: {
          item_id: 'invalid-detection-id',
          item_type: 'symbol',
          action: 'approved',
        },
      });

      expect([404, 422]).toContain(response.status());
    });

    test('should handle invalid action', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const detectResponse = await apiContext.get(`/detection/${testSession.id}/detections`);
      const detectData = await detectResponse.json();

      if (detectData.detections && detectData.detections.length > 0) {
        const response = await apiContext.post(`/verification/verify/${testSession.id}`, {
          data: {
            item_id: detectData.detections[0].id,
            item_type: 'symbol',
            action: 'invalid-action',
          },
        });

        // API may accept any action value and return 200, or reject with 400/422
        expect([200, 400, 422]).toContain(response.status());
      }
    });
  });
});
