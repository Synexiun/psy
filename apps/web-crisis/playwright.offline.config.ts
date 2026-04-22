import { defineConfig, devices } from '@playwright/test';

/**
 * Offline test configuration.
 *
 * These tests verify that the crisis surface renders correctly when:
 * - JavaScript is disabled (deterministic static HTML)
 * - The app is served from the static export (`output: 'export'`)
 *
 * This is the deployment shape: S3/CloudFront serving pre-built HTML.
 */
export default defineConfig({
  testDir: 'tests/offline',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['list'], ['junit', { outputFile: 'tests/offline/junit.xml' }]] : 'list',
  use: {
    baseURL: 'http://localhost:3051',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    javaScriptEnabled: false,
  },
  projects: [
    { name: 'chromium-offline', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chrome-offline', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: 'pnpm build && npx serve out -p 3051',
    url: 'http://localhost:3051',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
