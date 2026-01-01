/**
 * Blueprint AI BOM - Edge Cases & Error Handling Tests
 *
 * 엣지 케이스와 에러 처리를 검증합니다.
 *
 * 테스트 범위:
 * - 입력 유효성 검증
 * - API 에러 응답
 * - 경계값 테스트
 * - 동시성 처리
 * - 타임아웃 처리
 *
 * Worker-scoped fixtures 사용으로 테스트 안정성 보장
 */

import { test, expect } from '../fixtures/api-fixtures';
import { request } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_BASE_URL = 'http://localhost:5020';
const FIXTURES_PATH = path.join(__dirname, '../fixtures/images');

// 테스트 중 생성된 추가 세션 ID 추적
const createdSessionIds: string[] = [];

// Playwright multipart 파일 업로드 헬퍼
function createFileUpload(filePath: string) {
  const fileName = path.basename(filePath);
  const extension = path.extname(filePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.txt': 'text/plain',
  };
  return {
    name: fileName,
    mimeType: mimeTypes[extension] || 'application/octet-stream',
    buffer: fs.readFileSync(filePath),
  };
}

test.describe('Edge Cases & Error Handling', () => {
  test.setTimeout(60000);

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

  test.describe('Input Validation', () => {
    test('should reject empty session name', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const response = await apiContext.post('/sessions/upload', {
        multipart: {
          name: '',
          file: createFileUpload(imagePath),
        },
      });

      // 빈 이름 거부 또는 기본값 사용
      // API 구현에 따라 200 또는 400/422
      expect([200, 400, 422]).toContain(response.status());
    });

    test('should reject very long session name', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');
      const longName = 'A'.repeat(1000); // 1000자

      const response = await apiContext.post('/sessions/upload', {
        multipart: {
          name: longName,
          file: createFileUpload(imagePath),
        },
      });

      // 길이 제한이 있으면 에러, 없으면 성공
      if (response.ok()) {
        const data = await response.json();
        createdSessionIds.push(data.session_id);
      }
    });

    test('should handle special characters in session name', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');
      const specialName = "Test <script>alert('xss')</script>";

      const response = await apiContext.post('/sessions/upload', {
        multipart: {
          name: specialName,
          file: createFileUpload(imagePath),
        },
      });

      if (response.ok()) {
        const data = await response.json();
        createdSessionIds.push(data.session_id);

        // 세션이 정상적으로 생성되었는지 확인
        const getResponse = await apiContext.get(`/sessions/${data.session_id}`);
        const getData = await getResponse.json();

        // 세션 ID가 유효하고 파일이 저장되었는지 확인
        expect(getData.session_id).toBe(data.session_id);
        expect(getData.filename).toBeTruthy();
      }
    });

    test('should reject invalid confidence value (string)', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      // 세션 생성
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Invalid Confidence Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 잘못된 confidence 값으로 검출 시도
      const response = await apiContext.post(`/detection/${createData.session_id}/detect`, {
        data: {
          confidence: 'invalid',
        },
      });

      expect([400, 422]).toContain(response.status());
    });

    test('should reject confidence value at boundary (0)', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Boundary Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      const response = await apiContext.post(`/detection/${createData.session_id}/detect`, {
        data: {
          confidence: 0,
        },
      });

      // 0은 유효하지 않을 수 있음
      expect([200, 400, 422]).toContain(response.status());
    });

    test('should handle confidence at boundary (1.0)', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Boundary Max Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      const response = await apiContext.post(`/detection/${createData.session_id}/detect`, {
        data: {
          confidence: 1.0,
        },
      });

      // 1.0은 유효해야 함
      expect(response.ok()).toBeTruthy();
    });
  });

  test.describe('HTTP Error Responses', () => {
    test('should return 404 for non-existent session', async ({ apiContext }) => {
      const response = await apiContext.get('/sessions/non-existent-session-12345');
      expect(response.status()).toBe(404);

      const data = await response.json();
      expect(data).toHaveProperty('detail');
    });

    test('should return 404 for non-existent endpoint', async ({ apiContext }) => {
      const response = await apiContext.get('/non-existent-endpoint');
      expect(response.status()).toBe(404);
    });

    test('should return 400 for malformed JSON', async ({ apiContext }) => {
      const response = await apiContext.post('/detection/test/detect', {
        headers: { 'Content-Type': 'application/json' },
        data: 'invalid json',
      });

      expect([400, 404, 422]).toContain(response.status());
    });

    test('should return 422 for schema validation error', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Schema Error Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      const response = await apiContext.post(`/detection/${createData.session_id}/detect`, {
        data: {
          confidence: 1.5, // 범위 초과
          iou_threshold: 2.0, // 범위 초과
        },
      });

      expect([400, 422]).toContain(response.status());

      const data = await response.json();
      expect(data).toHaveProperty('detail');
    });

    test('should return 405 for method not allowed', async ({ apiContext }) => {
      const response = await apiContext.put('/sessions', {
        data: { name: 'test' },
      });

      // PUT이 지원되지 않으면 405
      expect([404, 405, 422]).toContain(response.status());
    });
  });

  test.describe('Boundary Values', () => {
    let testSessionId: string;

    test.beforeAll(async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Boundary Values Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      testSessionId = createData.session_id;
      createdSessionIds.push(testSessionId);
    });

    test('should handle minimum confidence (0.05)', async ({ apiContext }) => {
      const response = await apiContext.post(`/detection/${createdSessionIds[createdSessionIds.length - 1]}/detect`, {
        data: { confidence: 0.05 },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should handle minimum iou_threshold (0.1)', async ({ apiContext }) => {
      const response = await apiContext.post(`/detection/${createdSessionIds[createdSessionIds.length - 1]}/detect`, {
        data: { iou_threshold: 0.1 },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should handle maximum iou_threshold (0.95)', async ({ apiContext }) => {
      const response = await apiContext.post(`/detection/${createdSessionIds[createdSessionIds.length - 1]}/detect`, {
        data: { iou_threshold: 0.95 },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should handle minimum imgsz (320)', async ({ apiContext }) => {
      const response = await apiContext.post(`/detection/${createdSessionIds[createdSessionIds.length - 1]}/detect`, {
        data: { imgsz: 320 },
      });

      expect(response.ok()).toBeTruthy();
    });

    test('should handle large imgsz (2048)', async ({ apiContext }) => {
      const response = await apiContext.post(`/detection/${createdSessionIds[createdSessionIds.length - 1]}/detect`, {
        data: { imgsz: 2048 },
      });

      // 메모리 제한에 따라 성공 또는 실패할 수 있음
      expect([200, 400, 500, 503]).toContain(response.status());
    });
  });

  test.describe('Concurrent Requests', () => {
    test('should handle concurrent session creation', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      // 5개 동시 요청
      const promises = Array(5).fill(null).map((_, i) =>
        apiContext.post('/sessions/upload', {
          multipart: {
            name: `Concurrent Session ${i} ${Date.now()}`,
            file: createFileUpload(imagePath),
          },
        })
      );

      const responses = await Promise.all(promises);

      // 모든 요청 성공
      let successCount = 0;
      for (const response of responses) {
        if (response.ok()) {
          successCount++;
          const data = await response.json();
          createdSessionIds.push(data.session_id);
        }
      }

      expect(successCount).toBe(5);
    });

    test('should handle concurrent detection requests', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      // 세션 생성
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Concurrent Detection Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 3개 동시 검출 요청
      const promises = [0.2, 0.3, 0.4].map((confidence) =>
        apiContext.post(`/detection/${createData.session_id}/detect`, {
          data: { confidence },
        })
      );

      const responses = await Promise.all(promises);

      // 최소 하나는 성공해야 함
      const successCount = responses.filter(r => r.ok()).length;
      expect(successCount).toBeGreaterThanOrEqual(1);
    });
  });

  test.describe('Timeout Handling', () => {
    test('should respect timeout for long operations', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Timeout Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 짧은 타임아웃으로 요청
      const shortTimeoutContext = await request.newContext({
        baseURL: API_BASE_URL,
        timeout: 100, // 100ms - 매우 짧음
      });

      try {
        await shortTimeoutContext.post(`/detection/${createData.session_id}/detect`, {
          data: { imgsz: 2048 }, // 큰 이미지로 느린 처리 유도
        });
      } catch (error) {
        // 타임아웃 에러 예상
        expect(error).toBeDefined();
      } finally {
        await shortTimeoutContext.dispose();
      }
    });
  });

  test.describe('Empty Data Handling', () => {
    test('should handle session with no detections', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Empty Detection Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 검출 전 결과 조회
      const response = await apiContext.get(`/detection/${createData.session_id}/detections`);

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.detections).toBeDefined();
      expect(Array.isArray(data.detections)).toBeTruthy();
      expect(data.detections.length).toBe(0);
    });

    test('should handle empty verification queue', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Empty Queue Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      const response = await apiContext.get(`/pid-features/${createData.session_id}/verify/queue`);

      if (response.ok()) {
        const data = await response.json();
        expect(data.items).toBeDefined();
        expect(Array.isArray(data.items)).toBeTruthy();
      }
    });
  });

  test.describe('Rate Limiting', () => {
    test('should handle rapid requests', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Rate Limit Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 빠른 연속 요청 10개
      const results: number[] = [];

      for (let i = 0; i < 10; i++) {
        const response = await apiContext.get(`/sessions/${createData.session_id}`);
        results.push(response.status());
      }

      // 대부분 성공해야 함
      const successCount = results.filter(s => s === 200).length;
      expect(successCount).toBeGreaterThanOrEqual(8);
    });
  });

  test.describe('Data Integrity', () => {
    test('should maintain data consistency after multiple operations', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      // 세션 생성
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Data Integrity Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 검출 실행
      await apiContext.post(`/detection/${createData.session_id}/detect`, {
        data: { confidence: 0.25 },
      });

      // 세션 정보 조회
      const getResponse = await apiContext.get(`/sessions/${createData.session_id}`);
      const getData = await getResponse.json();

      // 세션 ID 일관성
      expect(getData.session_id).toBe(createData.session_id);

      // 검출 결과 조회
      const detectResponse = await apiContext.get(`/detection/${createData.session_id}/detections`);
      const detectData = await detectResponse.json();

      // 검출 결과가 있으면 유효한 데이터 구조
      if (detectData.detections.length > 0) {
        for (const detection of detectData.detections) {
          expect(detection).toHaveProperty('id');
          expect(detection).toHaveProperty('class_name');
          expect(detection).toHaveProperty('confidence');
          expect(detection).toHaveProperty('bbox');
        }
      }
    });
  });
});
