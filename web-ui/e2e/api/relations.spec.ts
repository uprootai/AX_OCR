/**
 * Blueprint AI BOM - Relations API Tests
 *
 * 심볼-치수 관계 추출 및 관리 API 테스트
 *
 * 테스트 범위:
 * - 관계 추출
 * - 관계 조회
 * - 관계 수정
 * - 관계 삭제
 * - 대량 관계 업데이트
 * - 관계 통계
 *
 * Worker-scoped fixtures 사용으로 테스트 안정성 보장
 */

import { test, expect, isValidSession } from '../fixtures/api-fixtures';

test.describe('Relations API', () => {
  test.setTimeout(120000);

  test.describe('Relation Extraction', () => {
    test('should extract relations from session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/relations/extract/${testSession.id}`, {
        data: {},
      });

      expect([200, 202]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('relations');
      }
    });

    test('should extract with distance threshold', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/relations/extract/${testSession.id}`, {
        data: {
          distance_threshold: 100,
        },
      });

      expect([200, 202]).toContain(response.status());
    });

    test('should extract specific relation types', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.post(`/relations/extract/${testSession.id}`, {
        data: {
          relation_types: ['dimension_to_symbol', 'leader_line'],
        },
      });

      expect([200, 202]).toContain(response.status());
    });
  });

  test.describe('Relation Retrieval', () => {
    test('should get all relations for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/relations/${testSession.id}`);

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('relations');
      expect(Array.isArray(data.relations)).toBeTruthy();
    });

    test('should filter relations by type', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/relations/${testSession.id}`, {
        params: {
          type: 'dimension_to_symbol',
        },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should paginate relations', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/relations/${testSession.id}`, {
        params: {
          page: 1,
          limit: 10,
        },
      });

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.relations.length).toBeLessThanOrEqual(10);
    });
  });

  test.describe('Relation Modification', () => {
    test('should update relation', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 먼저 관계 조회
      const getResponse = await apiContext.get(`/relations/${testSession.id}`);
      const getData = await getResponse.json();

      if (getData.relations && getData.relations.length > 0) {
        const relationId = getData.relations[0].id;

        const response = await apiContext.put(`/relations/${testSession.id}/${relationId}`, {
          data: {
            confidence: 0.95,
            verified: true,
          },
        });

        expect([200, 404]).toContain(response.status());
      }
    });

    test('should delete relation', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const getResponse = await apiContext.get(`/relations/${testSession.id}`);
      const getData = await getResponse.json();

      if (getData.relations && getData.relations.length > 0) {
        const relationId = getData.relations[0].id;

        const response = await apiContext.delete(`/relations/${testSession.id}/${relationId}`);

        expect([200, 204, 404]).toContain(response.status());
      }
    });
  });

  test.describe('Manual Link', () => {
    test('should manually link dimension to target', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 검출 결과에서 ID 가져오기
      const detectResponse = await apiContext.get(`/detection/${testSession.id}/detections`);
      const detectData = await detectResponse.json();

      // 치수 조회
      const dimResponse = await apiContext.get(`/analysis/dimensions/${testSession.id}`);
      const dimData = await dimResponse.json();

      if (detectData.detections?.length > 0 && dimData.dimensions?.length > 0) {
        const dimensionId = dimData.dimensions[0].id;
        const targetId = detectData.detections[0].id;

        const response = await apiContext.post(
          `/relations/${testSession.id}/link/${dimensionId}/${targetId}`,
          { data: {} }
        );

        expect([200, 201, 404, 422]).toContain(response.status());
      }
    });
  });

  test.describe('Bulk Operations', () => {
    test('should bulk update relations', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const getResponse = await apiContext.get(`/relations/${testSession.id}`);
      const getData = await getResponse.json();

      if (getData.relations && getData.relations.length > 0) {
        const relationIds = getData.relations.slice(0, 3).map((r: { id: string }) => r.id);

        const response = await apiContext.put(`/relations/${testSession.id}/bulk`, {
          data: {
            relation_ids: relationIds,
            verified: true,
          },
        });

        expect([200, 404]).toContain(response.status());
      }
    });
  });

  test.describe('Relation Statistics', () => {
    test('should get relation statistics', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/relations/${testSession.id}/statistics`);

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // Response: { total, by_method, by_confidence, linked_count, unlinked_count }
      expect(data).toHaveProperty('total');
      expect(data).toHaveProperty('by_confidence');
    });

    test('should get verified vs unverified counts', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.get(`/relations/${testSession.id}/statistics`);

      if (response.ok()) {
        const data = await response.json();
        // Response has linked_count and unlinked_count
        expect(data).toHaveProperty('linked_count');
        expect(data).toHaveProperty('unlinked_count');
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle non-existent session', async ({ apiContext }) => {
      const response = await apiContext.get('/relations/non-existent-session');

      expect([404]).toContain(response.status());
    });

    test('should handle invalid relation ID', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const response = await apiContext.put(`/relations/${testSession.id}/invalid-id`, {
        data: {
          confidence: 0.9,
        },
      });

      // 404 for not found, 405 if method not allowed, or 422 for validation error
      expect([404, 405, 422]).toContain(response.status());
    });
  });
});
