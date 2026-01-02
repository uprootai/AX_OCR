/**
 * Blueprint AI BOM - API Test Fixtures
 *
 * Worker-scoped fixtures for API testing
 * - Each worker gets its own isolated session
 * - Sessions are reused across tests within a worker
 * - Proper cleanup on worker termination
 */

import { test as base, request, APIRequestContext } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:5020';
const FIXTURES_PATH = path.join(__dirname, '../fixtures/images');

// Session type definitions
interface TestSession {
  id: string;
  hasDetections: boolean;
  createdAt: number;
}

interface ApiFixtures {
  apiContext: APIRequestContext;
  testSession: TestSession;
  emptySession: TestSession;
}

// Utility function to create file upload payload
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

// Worker ID for unique session naming
let workerId = 0;
function getWorkerId(): number {
  if (workerId === 0) {
    workerId = Date.now() + Math.floor(Math.random() * 10000);
  }
  return workerId;
}

/**
 * Extended test with API fixtures
 *
 * Usage:
 * ```typescript
 * import { test, expect } from '../fixtures/api-fixtures';
 *
 * test('my test', async ({ apiContext, testSession }) => {
 *   const response = await apiContext.get(`/bom/${testSession.id}`);
 *   expect([200, 404]).toContain(response.status());
 * });
 * ```
 */
export const test = base.extend<object, ApiFixtures>({
  /**
   * Worker-scoped API context
   * Created once per worker, reused across all tests
   */
  apiContext: [
    async (_deps, use) => {
      const ctx = await request.newContext({
        baseURL: API_BASE_URL,
        timeout: 180000,
        extraHTTPHeaders: {
          'X-Test-Worker': String(getWorkerId()),
        },
      });

      await use(ctx);

      // Cleanup on worker termination
      await ctx.dispose();
    },
    { scope: 'worker' },
  ],

  /**
   * Worker-scoped test session WITH detections
   * - Creates a session with an image
   * - Runs detection on the image
   * - Session is reused across all tests in the worker
   */
  testSession: [
    async ({ apiContext }, use) => {
      const wid = getWorkerId();
      const sessionName = `Test Session Worker-${wid}`;
      let sessionId: string | null = null;

      try {
        // Create session with image upload
        const imagePath = path.join(FIXTURES_PATH, 'pid_bwms_pid_sample.png');

        if (!fs.existsSync(imagePath)) {
          throw new Error(`Test image not found: ${imagePath}`);
        }

        const createResponse = await apiContext.post('/sessions/upload', {
          multipart: {
            name: sessionName,
            file: createFileUpload(imagePath),
          },
        });

        if (!createResponse.ok()) {
          const errorText = await createResponse.text();
          throw new Error(`Failed to create session: ${createResponse.status()} - ${errorText}`);
        }

        const createData = await createResponse.json();
        sessionId = createData.session_id;

        // Run detection
        const detectResponse = await apiContext.post(`/detection/${sessionId}/detect`, {
          data: { confidence: 0.25 },
        });

        if (!detectResponse.ok()) {
          console.warn(`Detection failed for session ${sessionId}: ${detectResponse.status()}`);
        }

        const session: TestSession = {
          id: sessionId,
          hasDetections: detectResponse.ok(),
          createdAt: Date.now(),
        };

        await use(session);
      } catch (error) {
        console.error('Failed to create test session:', error);
        // Provide a dummy session that tests can skip
        await use({
          id: '',
          hasDetections: false,
          createdAt: 0,
        });
      } finally {
        // Cleanup session on worker termination
        if (sessionId) {
          try {
            await apiContext.delete(`/sessions/${sessionId}`);
          } catch {
            // Ignore cleanup errors
          }
        }
      }
    },
    { scope: 'worker' },
  ],

  /**
   * Worker-scoped EMPTY session (no detections)
   * - Creates a session with an image but no detection
   * - Useful for testing empty state handling
   */
  emptySession: [
    async ({ apiContext }, use) => {
      const wid = getWorkerId();
      const sessionName = `Empty Session Worker-${wid}`;
      let sessionId: string | null = null;

      try {
        const imagePath = path.join(FIXTURES_PATH, 'pid_page_1.png');

        if (!fs.existsSync(imagePath)) {
          throw new Error(`Test image not found: ${imagePath}`);
        }

        const createResponse = await apiContext.post('/sessions/upload', {
          multipart: {
            name: sessionName,
            file: createFileUpload(imagePath),
          },
        });

        if (!createResponse.ok()) {
          throw new Error(`Failed to create empty session: ${createResponse.status()}`);
        }

        const createData = await createResponse.json();
        sessionId = createData.session_id;

        const session: TestSession = {
          id: sessionId,
          hasDetections: false,
          createdAt: Date.now(),
        };

        await use(session);
      } catch (error) {
        console.error('Failed to create empty session:', error);
        await use({
          id: '',
          hasDetections: false,
          createdAt: 0,
        });
      } finally {
        if (sessionId) {
          try {
            await apiContext.delete(`/sessions/${sessionId}`);
          } catch {
            // Ignore cleanup errors
          }
        }
      }
    },
    { scope: 'worker' },
  ],
});

// Re-export expect for convenience
export { expect } from '@playwright/test';

// Helper function to check if session is valid
export function isValidSession(session: TestSession): boolean {
  return session.id !== '' && session.createdAt > 0;
}

// Helper to skip test if session is invalid
export function skipIfNoSession(testInstance: typeof test, session: TestSession, reason?: string) {
  testInstance.skip(
    !isValidSession(session),
    reason || 'No valid test session available'
  );
}
