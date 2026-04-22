/**
 * Offline / no-JS tests for the crisis surface.
 *
 * These run against the static export (the actual deployment artifact) with
 * JavaScript disabled in the browser. A crisis page that requires JS to show
 * hotlines is a safety defect — these tests ensure the static HTML alone is
 * sufficient.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Crisis page without JavaScript', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/`);
      });

      test('renders headline in static HTML', async ({ page }) => {
        const headline = page.locator('h1');
        await expect(headline).toBeVisible();
      });

      test('emergency tel link is present and clickable', async ({ page }) => {
        const link = page.locator('a[href^="tel:"]').first();
        await expect(link).toBeVisible();
      });

      test('every hotline has a number or sms link', async ({ page }) => {
        const hotlineItems = page.locator('ul li');
        const count = await hotlineItems.count();
        expect(count).toBeGreaterThan(0);
        for (let i = 0; i < count; i++) {
          const item = hotlineItems.nth(i);
          const tel = item.locator('a[href^="tel:"]');
          const sms = item.locator('a[href^="sms:"]');
          const hasTel = (await tel.count()) > 0;
          const hasSms = (await sms.count()) > 0;
          expect(hasTel || hasSms).toBe(true);
        }
      });

      test('RTL direction applied for ar and fa', async ({ page }) => {
        const wrapper = page.locator('div[dir]');
        const dir = await wrapper.getAttribute('dir');
        if (locale === 'ar' || locale === 'fa') {
          expect(dir).toBe('rtl');
        } else {
          expect(dir).toBe('ltr');
        }
      });
    });
  }
});

test.describe('Static export invariants', () => {
  test('root path provides link to /en/', async ({ page }) => {
    // The root page is a fallback for when the CDN edge redirect is not active
    // (e.g. local static serve). It must contain a visible link to /en/.
    await page.goto('/');
    const link = page.locator('a[href="/en/"]');
    await expect(link).toBeVisible();
    await expect(link).toContainText('crisis support');
  });

  test('no runtime errors in console (JS disabled, so console should be empty)', async ({ page }) => {
    const logs: string[] = [];
    page.on('console', (msg) => logs.push(msg.text()));
    await page.goto('/en/');
    // With JS disabled, the console should remain empty; any error-level log
    // from a <script> tag or inline handler would indicate a dependency on JS.
    const errors = logs.filter((l) => l.toLowerCase().includes('error'));
    expect(errors).toEqual([]);
  });
});
