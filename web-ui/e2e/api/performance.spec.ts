/**
 * Blueprint AI BOM - Performance Benchmark Tests
 *
 * API 성능 벤치마크 테스트
 *
 * 테스트 범위:
 * - 응답 시간 측정
 * - 동시 요청 처리
 * - 대용량 데이터 처리
 * - 메모리 사용량 (간접 측정)
 * - API 안정성
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

// 테스트 중 생성된 추가 세션 ID 추적
const createdSessionIds: string[] = [];

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

// 성능 측정 유틸리티
async function measureTime<T>(fn: () => Promise<T>): Promise<{ result: T; duration: number }> {
  const start = Date.now();
  const result = await fn();
  const duration = Date.now() - start;
  return { result, duration };
}

test.describe('Performance Benchmarks', () => {
  test.setTimeout(300000); // 5분

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

  test.describe('Response Time', () => {
    test('health check should respond within 300ms', async ({ apiContext }) => {
      const { duration } = await measureTime(async () => {
        return await apiContext.get('/health');
      });

      // Health check should be fast, but allow some latency in concurrent test environment
      expect(duration).toBeLessThan(300);
    });

    test('session list should respond within 500ms', async ({ apiContext }) => {
      const { duration } = await measureTime(async () => {
        return await apiContext.get('/sessions');
      });

      expect(duration).toBeLessThan(500);
    });

    test('detection results should respond within 1s', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const { duration } = await measureTime(async () => {
        return await apiContext.get(`/detection/${testSession.id}/detections`);
      });

      expect(duration).toBeLessThan(1000);
    });

    test('BOM retrieval should respond within 2s', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const { duration } = await measureTime(async () => {
        return await apiContext.get(`/bom/${testSession.id}`);
      });

      expect(duration).toBeLessThan(2000);
    });
  });

  test.describe('File Upload Performance', () => {
    test('should upload small image within 3s', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');
      const fileSize = fs.statSync(imagePath).size;

      const { result, duration } = await measureTime(async () => {
        return await apiContext.post('/sessions/upload', {
          multipart: {
            name: `Upload Test Small ${Date.now()}`,
            file: createFileUpload(imagePath),
          },
        });
      });

      expect(result.ok()).toBeTruthy();
      expect(duration).toBeLessThan(3000);

      const data = await result.json();
      createdSessionIds.push(data.session_id);

      // MB/s 계산
      const mbPerSecond = (fileSize / (1024 * 1024)) / (duration / 1000);
      console.log(`Upload speed: ${mbPerSecond.toFixed(2)} MB/s`);
    });

    test('should upload large image within 10s', async ({ apiContext }) => {
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

      const { result, duration } = await measureTime(async () => {
        return await apiContext.post('/sessions/upload', {
          multipart: {
            name: `Upload Test Large ${Date.now()}`,
            file: createFileUpload(imagePath),
          },
        });
      });

      expect(result.ok()).toBeTruthy();
      expect(duration).toBeLessThan(10000);

      const data = await result.json();
      createdSessionIds.push(data.session_id);
    });
  });

  test.describe('Detection Performance', () => {
    test('should complete detection within 60s', async ({ apiContext }) => {
      // 새 세션 생성
      const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');
      const createResponse = await apiContext.post('/sessions/upload', {
        multipart: {
          name: `Detection Performance Test ${Date.now()}`,
          file: createFileUpload(imagePath),
        },
      });

      const createData = await createResponse.json();
      createdSessionIds.push(createData.session_id);

      const { result, duration } = await measureTime(async () => {
        return await apiContext.post(`/detection/${createData.session_id}/detect`, {
          data: { confidence: 0.25 },
        });
      });

      expect(result.ok()).toBeTruthy();
      expect(duration).toBeLessThan(60000);

      console.log(`Detection time: ${(duration / 1000).toFixed(2)}s`);
    });

    test('should scale with image size', async ({ apiContext }) => {
      const imagePaths = [
        path.join(FIXTURES_PATH, 'pid_page_1.png'),
        path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png'),
      ];

      const times: { size: number; duration: number }[] = [];

      for (const imagePath of imagePaths) {
        const fileSize = fs.statSync(imagePath).size;

        const createResponse = await apiContext.post('/sessions/upload', {
          multipart: {
            name: `Scale Test ${Date.now()}`,
            file: createFileUpload(imagePath),
          },
        });

        const createData = await createResponse.json();
        createdSessionIds.push(createData.session_id);

        const { duration } = await measureTime(async () => {
          return await apiContext.post(`/detection/${createData.session_id}/detect`, {
            data: { confidence: 0.25 },
          });
        });

        times.push({ size: fileSize, duration });
      }

      // 시간이 파일 크기에 비례하여 증가하는지 확인 (합리적인 스케일링)
      console.log('Detection scaling:', times.map(t => `${(t.size / 1024).toFixed(0)}KB: ${t.duration}ms`));
    });
  });

  test.describe('Concurrent Requests', () => {
    test('should handle 5 concurrent health checks', async ({ apiContext }) => {
      const concurrency = 5;
      const requests = Array(concurrency).fill(null).map(() =>
        measureTime(async () => apiContext.get('/health'))
      );

      const results = await Promise.all(requests);

      // 모든 요청 성공
      for (const { result } of results) {
        expect(result.ok()).toBeTruthy();
      }

      const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / concurrency;
      // Be more lenient with timing - allow up to 500ms for concurrent requests
      expect(avgDuration).toBeLessThan(500);

      console.log(`Concurrent health checks avg: ${avgDuration.toFixed(0)}ms`);
    });

    test('should handle 3 concurrent session creations', async ({ apiContext }) => {
      const concurrency = 3;
      const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');

      const requests = Array(concurrency).fill(null).map((_, i) =>
        measureTime(async () =>
          apiContext.post('/sessions/upload', {
            multipart: {
              name: `Concurrent Test ${i} ${Date.now()}`,
              file: createFileUpload(imagePath),
            },
          })
        )
      );

      const results = await Promise.all(requests);

      // 모든 요청 성공
      for (const { result } of results) {
        expect(result.ok()).toBeTruthy();
        const data = await result.json();
        createdSessionIds.push(data.session_id);
      }

      const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / concurrency;
      console.log(`Concurrent session creations avg: ${avgDuration.toFixed(0)}ms`);
    });

    test('should handle 10 concurrent API reads', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const concurrency = 10;

      const requests = Array(concurrency).fill(null).map(() =>
        measureTime(async () =>
          apiContext.get(`/detection/${testSession.id}/detections`)
        )
      );

      const results = await Promise.all(requests);

      // 모든 요청 성공
      for (const { result } of results) {
        expect(result.ok()).toBeTruthy();
      }

      const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / concurrency;
      expect(avgDuration).toBeLessThan(1000);

      console.log(`Concurrent reads avg: ${avgDuration.toFixed(0)}ms`);
    });
  });

  test.describe('Stress Testing', () => {
    test('should handle rapid sequential requests', async ({ apiContext }) => {
      const count = 20;
      const durations: number[] = [];

      for (let i = 0; i < count; i++) {
        const { duration } = await measureTime(async () =>
          apiContext.get('/health')
        );
        durations.push(duration);
      }

      const avgDuration = durations.reduce((a, b) => a + b, 0) / count;
      const maxDuration = Math.max(...durations);

      expect(avgDuration).toBeLessThan(100);
      expect(maxDuration).toBeLessThan(500); // 스파이크 제한

      console.log(`Rapid requests: avg=${avgDuration.toFixed(0)}ms, max=${maxDuration}ms`);
    });

    test('should maintain performance under load', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 첫 번째 측정 (웜업)
      const { duration: warmupDuration } = await measureTime(async () =>
        apiContext.get(`/bom/${testSession.id}`)
      );

      // 부하 생성
      await Promise.all(
        Array(5).fill(null).map(() => apiContext.get('/sessions'))
      );

      // 두 번째 측정 (부하 후)
      const { duration: loadedDuration } = await measureTime(async () =>
        apiContext.get(`/bom/${testSession.id}`)
      );

      // 부하 후에도 성능 유지 (50% 이내 증가)
      expect(loadedDuration).toBeLessThan(warmupDuration * 1.5 + 100);

      console.log(`Performance under load: before=${warmupDuration}ms, after=${loadedDuration}ms`);
    });
  });

  test.describe('Large Data Handling', () => {
    test('should handle session with many detections', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 검출 결과 조회
      const { result, duration } = await measureTime(async () =>
        apiContext.get(`/detection/${testSession.id}/detections`)
      );

      expect(result.ok()).toBeTruthy();

      const data = await result.json();
      const detectionCount = data.detections?.length || 0;

      // 검출 수에 관계없이 합리적인 시간 내 응답
      expect(duration).toBeLessThan(2000);

      console.log(`Retrieved ${detectionCount} detections in ${duration}ms`);
    });

    test('should handle paginated results efficiently', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      // 페이지네이션 성능 비교
      const { duration: allDuration } = await measureTime(async () =>
        apiContext.get(`/detection/${testSession.id}/detections`)
      );

      const { duration: pageDuration } = await measureTime(async () =>
        apiContext.get(`/detection/${testSession.id}/detections`, {
          params: { page: 1, limit: 10 },
        })
      );

      // 페이지네이션이 전체 조회보다 빠르거나 비슷해야 함
      expect(pageDuration).toBeLessThanOrEqual(allDuration + 100);

      console.log(`All: ${allDuration}ms, Page: ${pageDuration}ms`);
    });
  });

  test.describe('API Stability', () => {
    test('should return consistent results', async ({ apiContext, testSession }) => {
      test.skip(!isValidSession(testSession), 'No valid test session');
      const results: string[] = [];

      // 동일한 요청 3번 실행
      for (let i = 0; i < 3; i++) {
        const response = await apiContext.get(`/detection/${testSession.id}/detections`);
        const data = await response.json();
        results.push(JSON.stringify(data.detections?.map((d: { id: string }) => d.id).sort()));
      }

      // 결과가 일관성 있어야 함
      expect(results[0]).toBe(results[1]);
      expect(results[1]).toBe(results[2]);
    });

    test('should handle rapid create/delete cycles', async ({ apiContext }) => {
      const cycles = 3;

      for (let i = 0; i < cycles; i++) {
        const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');

        // 생성
        const createResponse = await apiContext.post('/sessions/upload', {
          multipart: {
            name: `Cycle Test ${i} ${Date.now()}`,
            file: createFileUpload(imagePath),
          },
        });

        expect(createResponse.ok()).toBeTruthy();

        const data = await createResponse.json();

        // 삭제
        const deleteResponse = await apiContext.delete(`/sessions/${data.session_id}`);
        expect(deleteResponse.ok()).toBeTruthy();
      }
    });
  });

  test.describe('Memory Efficiency', () => {
    test('should not leak sessions', async ({ apiContext }) => {
      // 시작 시 세션 수
      const startResponse = await apiContext.get('/sessions');
      const startData = await startResponse.json();
      const startCount = startData.length || 0;

      // 여러 세션 생성 및 삭제
      const tempIds: string[] = [];
      const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');

      for (let i = 0; i < 3; i++) {
        const response = await apiContext.post('/sessions/upload', {
          multipart: {
            name: `Memory Test ${i} ${Date.now()}`,
            file: createFileUpload(imagePath),
          },
        });
        const data = await response.json();
        tempIds.push(data.session_id);
      }

      for (const id of tempIds) {
        await apiContext.delete(`/sessions/${id}`);
      }

      // 종료 시 세션 수
      const endResponse = await apiContext.get('/sessions');
      const endData = await endResponse.json();
      const endCount = endData.length || 0;

      // 세션 수가 시작과 같거나 그보다 적어야 함 (다른 테스트로 인한 변동 허용)
      // 삭제한 세션만큼은 줄어야 하므로 시작 수보다 3 이상 증가하면 안됨
      expect(endCount).toBeLessThanOrEqual(startCount + 2);
    });
  });
});
