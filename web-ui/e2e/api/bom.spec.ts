/**
 * Blueprint AI BOM - BOM Generation API Tests
 *
 * BOM(Bill of Materials) 생성 및 내보내기 API 테스트
 *
 * 테스트 범위:
 * - BOM 조회
 * - BOM 생성
 * - BOM 요약
 * - BOM 내보내기 (Excel, PDF)
 * - BOM 다운로드
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

test.describe('BOM API', () => {
  // Increase timeout for setup with detection
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

  test.describe('BOM Retrieval', () => {
    test('should get BOM for session', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.get(`/bom/${testSession.id}`);

      // BOM이 아직 생성되지 않았으면 404
      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('bom');
      }
    });

    test('should get BOM summary', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.get(`/bom/${testSession.id}/summary`);

      // BOM이 아직 생성되지 않았으면 404
      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('total_items');
      }
    });
  });

  test.describe('BOM Generation', () => {
    test('should generate BOM from detections', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.post(`/bom/${testSession.id}/generate`, {
        data: {
          include_dimensions: true,
          include_notes: true,
          format: 'structured',
        },
      });

      // 400 for bad request, 404 when no approved detections, 422 for validation errors
      expect([200, 202, 400, 404, 422]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('bom');
      }
    });

    test('should generate BOM with custom options', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.post(`/bom/${testSession.id}/generate`, {
        data: {
          include_dimensions: false,
          include_notes: false,
          group_by: 'class',
        },
      });

      // 400 for bad request, 404 when no approved detections, 422 for validation errors
      expect([200, 202, 400, 404, 422]).toContain(response.status());
    });
  });

  test.describe('BOM Export', () => {
    test('should export BOM to Excel', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.post(`/bom/${testSession.id}/export`, {
        data: {
          format: 'excel',
          template: 'default',
        },
      });

      // 404 when no BOM generated yet, 422 for validation errors
      expect([200, 202, 404, 422]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('download_url');
      }
    });

    test('should export BOM to PDF', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.post(`/bom/${testSession.id}/export`, {
        data: {
          format: 'pdf',
          include_images: true,
        },
      });

      // 404 when no BOM generated yet, 422 for validation errors
      expect([200, 202, 404, 422]).toContain(response.status());
    });

    test('should export BOM to CSV', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.post(`/bom/${testSession.id}/export`, {
        data: {
          format: 'csv',
        },
      });

      // 404 when no BOM generated yet, 422 for validation errors
      expect([200, 202, 404, 422]).toContain(response.status());
    });

    test('should export BOM to JSON', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.post(`/bom/${testSession.id}/export`, {
        data: {
          format: 'json',
        },
      });

      // 404 when no BOM generated yet, 422 for validation errors
      expect([200, 202, 404, 422]).toContain(response.status());
    });
  });

  test.describe('BOM Download', () => {
    test('should download BOM file', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.get(`/bom/${testSession.id}/download`);

      // 파일이 생성되지 않았으면 404
      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const contentType = response.headers()['content-type'];
        // Excel, PDF, CSV 등의 파일 형식
        expect(contentType).toBeTruthy();
      }
    });

    test('should download BOM in specific format', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      const response = await apiContext.get(`/bom/${testSession.id}/download`, {
        params: { format: 'excel' },
      });

      expect([200, 404]).toContain(response.status());
    });
  });

  test.describe('BOM Validation', () => {
    test('should validate BOM completeness', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      // 먼저 BOM 조회
      const bomResponse = await apiContext.get(`/bom/${testSession.id}`);
      const bomData = await bomResponse.json();

      if (bomData.bom && bomData.bom.items) {
        // BOM 항목이 있는 경우 유효성 검사
        for (const item of bomData.bom.items) {
          expect(item).toHaveProperty('id');
          // class_name 또는 class 중 하나가 있어야 함
          expect(item.class_name || item.class || item.name).toBeTruthy();
        }
      }
    });

    test('should handle empty BOM', async ({ apiContext }) => {
      // 빈 세션 생성
      const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Empty BOM Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      // 검출 없이 BOM 조회 - 404 is expected for empty session
      const response = await apiContext.get(`/bom/${createData.session_id}`);

      // Empty BOM may return 200 with empty data or 404
      expect([200, 404]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        // 빈 BOM도 유효한 응답이어야 함
        expect(data).toHaveProperty('bom');
      }
    });
  });

  test.describe('BOM Update', () => {
    test('should update BOM item', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No test session available');
      // 먼저 BOM 조회
      const bomResponse = await apiContext.get(`/bom/${testSession.id}`);
      const bomData = await bomResponse.json();

      if (bomData.bom && bomData.bom.items && bomData.bom.items.length > 0) {
        const itemId = bomData.bom.items[0].id;

        const response = await apiContext.patch(`/bom/${testSession.id}/items/${itemId}`, {
          data: {
            quantity: 5,
            notes: 'Updated via API test',
          },
        });

        // 업데이트 지원 여부에 따라
        expect([200, 404, 405]).toContain(response.status());
      }
    });
  });
});
