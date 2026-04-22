/**
 * E2E tests for the authenticated user app dashboard.
 *
 * These test the public-facing parts of the dashboard (crisis CTA, i18n,
 * layout). Auth-gated content is tested at the middleware level in unit tests.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Dashboard per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/`);
      });

      test('renders welcome title', async ({ page }) => {
        const heading = page.locator('h1');
        await expect(heading).toBeVisible();
      });

      test('crisis CTA links to crisis page', async ({ page }) => {
        const cta = page.locator(`a[href="/${locale}/crisis"]`);
        await expect(cta).toBeVisible();
      });

      test('sets correct text direction on html', async ({ page }) => {
        const html = page.locator('html');
        const dir = await html.getAttribute('dir');
        if (locale === 'ar' || locale === 'fa') {
          expect(dir).toBe('rtl');
        } else {
          expect(dir).toBe('ltr');
        }
      });

      test('sets lang attribute on html', async ({ page }) => {
        const html = page.locator('html');
        const lang = await html.getAttribute('lang');
        expect(lang).toBe(locale);
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Dashboard accessibility', () => {
  test('axe scan finds no violations on en dashboard', async ({ page }) => {
    await page.goto('/en/');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});
