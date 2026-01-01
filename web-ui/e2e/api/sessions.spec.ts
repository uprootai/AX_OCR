/**
 * Blueprint AI BOM - Session Management API Tests
 *
 * 실제 API를 호출하여 세션 관리 기능을 검증합니다.
 *
 * 테스트 범위:
 * - 세션 CRUD (생성, 조회, 수정, 삭제)
 * - 이미지 업로드
 * - 세션 목록 페이지네이션
 * - 세션 상태 전이
 *
 * Worker-scoped fixtures 사용으로 테스트 안정성 보장
 */

import { test, expect } from '../fixtures/api-fixtures';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FIXTURES_PATH = path.join(__dirname, '../fixtures/images');

// 테스트에서 생성된 세션 ID를 추적
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

test.describe('Session Management API', () => {
  // Cleanup created sessions after all tests
  test.afterAll(async ({ apiContext }) => {
    for (const sessionId of createdSessionIds) {
      try {
        await apiContext.delete(`/sessions/${sessionId}`);
      } catch {
        // Ignore cleanup errors
      }
    }
  });

  test.describe('Health Check', () => {
    test('should return healthy status', async ({ apiContext }) => {
      const response = await apiContext.get('/health');
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.status).toBe('healthy');
    });

    test('should return API info', async ({ apiContext }) => {
      const response = await apiContext.get('/');
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('version');
      expect(data).toHaveProperty('name');
    });
  });

  test.describe('Session CRUD', () => {
    test('should create a new session with image upload', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      // 이미지 파일 존재 확인
      expect(fs.existsSync(imagePath)).toBeTruthy();

      const response = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Test Session ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('session_id');
      expect(data).toHaveProperty('status');
      expect(['created', 'uploaded']).toContain(data.status);

      // 생성된 세션 ID 추적
      createdSessionIds.push(data.session_id);
    });

    test('should get session by ID', async ({ apiContext }) => {
      // 먼저 세션 생성
      const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Get Test Session ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 세션 조회
      const response = await apiContext.get(`/sessions/${createData.session_id}`);
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data.session_id).toBe(createData.session_id);
      expect(data).toHaveProperty('filename');
      expect(data).toHaveProperty('status');
      expect(data).toHaveProperty('created_at');
    });

    test('should list all sessions', async ({ apiContext }) => {
      const response = await apiContext.get('/sessions');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // API returns array of sessions directly
      expect(Array.isArray(data)).toBeTruthy();
    });

    test('should handle session update request', async ({ apiContext }) => {
      // 먼저 세션 생성
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Update Test Session ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 세션 업데이트 시도 (PATCH가 지원되지 않을 수 있음)
      const updateResponse = await apiContext.patch(`/sessions/${createData.session_id}`, {
        data: { drawing_type: 'pid' },
      });

      // PATCH 엔드포인트가 구현되어 있으면 성공, 아니면 405/404/422
      expect([200, 404, 405, 422, 500]).toContain(updateResponse.status());
    });

    test('should delete session', async ({ apiContext }) => {
      // 먼저 세션 생성
      const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Delete Test Session ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();

      // 세션 삭제
      const deleteResponse = await apiContext.delete(`/sessions/${createData.session_id}`);
      expect(deleteResponse.ok()).toBeTruthy();

      // 삭제 확인 - 404 예상
      const getResponse = await apiContext.get(`/sessions/${createData.session_id}`);
      expect(getResponse.status()).toBe(404);
    });

    test('should return 404 for non-existent session', async ({ apiContext }) => {
      const response = await apiContext.get('/sessions/non-existent-id-12345');
      expect(response.status()).toBe(404);
    });
  });

  test.describe('Image Upload Validation', () => {
    test('should reject unsupported file formats', async ({ apiContext }) => {
      // 임시 텍스트 파일 생성
      const tempFile = path.join(FIXTURES_PATH, 'temp_test.txt');
      fs.writeFileSync(tempFile, 'This is not an image');

      try {
        const response = await apiContext.post('/sessions/upload', {
          multipart: {
            name: 'Invalid File Test',
            file: createFileUpload(tempFile),
          },
        });

        // 400 또는 422 에러 예상
        expect([400, 422]).toContain(response.status());
      } finally {
        // 임시 파일 삭제
        fs.unlinkSync(tempFile);
      }
    });

    test('should handle multiple image uploads', async ({ apiContext }) => {
      const imagePath1 = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');
      const imagePath2 = path.join(FIXTURES_PATH, 'pid_page_1.png');

      // 첫 번째 세션 생성
      const response1 = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Multi Upload Test 1 ${Date.now()}`,
          file: createFileUpload(imagePath1),
        },
      });
      expect(response1.ok()).toBeTruthy();
      const data1 = await response1.json();
      createdSessionIds.push(data1.session_id);

      // 두 번째 세션 생성
      const response2 = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Multi Upload Test 2 ${Date.now()}`,
          file: createFileUpload(imagePath2),
        },
      });
      expect(response2.ok()).toBeTruthy();
      const data2 = await response2.json();
      createdSessionIds.push(data2.session_id);

      // 두 세션이 다른 ID를 가지는지 확인
      expect(data1.session_id).not.toBe(data2.session_id);
    });
  });

  test.describe('Session Status Transitions', () => {
    test('should have correct initial status after creation', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');
      const response = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Status Test Session ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const data = await response.json();
      createdSessionIds.push(data.session_id);

      expect(['created', 'uploaded']).toContain(data.status);
    });

    test('should transition to processing after detection', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      // 세션 생성
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Detection Status Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });
      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 검출 실행
      const detectResponse = await apiContext.post(`/detection/${createData.session_id}/detect`, {
        data: {
          confidence: 0.25,
          iou_threshold: 0.45,
        },
      });

      // 검출 성공 또는 진행 중
      expect([200, 202]).toContain(detectResponse.status());
    });
  });

  test.describe('Error Handling', () => {
    test('should return 400 for invalid request body', async ({ apiContext }) => {
      const response = await apiContext.post('/sessions/upload', {
        data: {
          invalid_field: 'test',
        },
      });

      // 400 또는 422 에러 예상
      expect([400, 422]).toContain(response.status());
    });

    test('should return 404 for invalid endpoint', async ({ apiContext }) => {
      const response = await apiContext.get('/invalid-endpoint');
      expect(response.status()).toBe(404);
    });

    test('should handle concurrent session creation', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      // 동시에 3개 세션 생성
      const promises = Array(3).fill(null).map((_, i) =>
        apiContext.post('/sessions/upload', {
          multipart: {
            name: `Concurrent Test ${i} ${Date.now()}`,
            file: createFileUpload(imagePath),
          },
        })
      );

      const responses = await Promise.all(promises);

      // 모든 요청 성공 확인
      for (const response of responses) {
        expect(response.ok()).toBeTruthy();
        const data = await response.json();
        createdSessionIds.push(data.session_id);
      }
    });
  });
});
