/**
 * E2E tests for the clinician portal.
 *
 * Verifies per-locale rendering and accessibility. Auth gating is tested
 * at the middleware level in unit tests.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Clinician home per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/`);
      });

      test('renders page title', async ({ page }) => {
        const heading = page.locator('h1');
        await expect(heading).toBeVisible();
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

test.describe('Clinician accessibility', () => {
  test('axe scan finds no violations on en page', async ({ page }) => {
    await page.goto('/en/');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});
