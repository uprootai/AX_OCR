import { defineConfig, devices } from '@playwright/test';

const webUiPort = process.env.WEB_UI_PORT || '5174';
const bomUiPort = process.env.BOM_UI_PORT || '5021';
const webUiBaseUrl = process.env.WEB_UI_BASE_URL || `http://localhost:${webUiPort}`;
const bomUiOrigin = process.env.BOM_UI_ORIGIN || `http://localhost:${bomUiPort}`;
const artifactRoot = '../.gstack/reports/playwright';
const storageStatePath = process.env.PLAYWRIGHT_STORAGE_STATE;

/**
 * Playwright E2E Test Configuration
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 4,
  outputDir: `${artifactRoot}/test-results`,
  reporter: [
    ['list'],
    ['html', { outputFolder: `${artifactRoot}/html`, open: 'never' }],
  ],
  use: {
    baseURL: webUiBaseUrl,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    ...(storageStatePath ? { storageState: storageStatePath } : {}),
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Disable GPU to prevent crashes in WSL2/headless environments
        launchOptions: {
          args: [
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-software-rasterizer',
            '--no-sandbox',
          ],
        },
      },
    },
  ],

  webServer: [
    {
      command: `npm run dev -- --port ${webUiPort} --host 127.0.0.1`,
      url: webUiBaseUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
      env: {
        ...process.env,
        VITE_BLUEPRINT_AI_BOM_FRONTEND_URL: `${bomUiOrigin}/bom`,
      },
    },
    {
      command: `bash -lc 'cd ../blueprint-ai-bom/frontend && npm run dev -- --port ${bomUiPort} --host 127.0.0.1'`,
      url: `${bomUiOrigin}/bom/`,
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
      env: {
        ...process.env,
        VITE_API_URL: process.env.BOM_API_BASE_URL || 'http://localhost:5020',
      },
    },
  ],
});
