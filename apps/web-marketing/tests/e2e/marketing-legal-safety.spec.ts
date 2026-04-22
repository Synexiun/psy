/**
 * E2E tests for marketing legal and safety pages.
 *
 * Covers privacy policy and safety resources across all supported locales.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Privacy page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/privacy`);
      });

      test('renders privacy headline', async ({ page }) => {
        const headline = page.locator('h1');
        await expect(headline).toBeVisible();
      });

      test('renders privacy body text', async ({ page }) => {
        const body = page.locator('main p');
        await expect(body).toBeVisible();
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
});

test.describe('Safety page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/safety`);
      });

      test('renders safety headline', async ({ page }) => {
        const headline = page.locator('h1');
        await expect(headline).toBeVisible();
      });

      test('renders safety body text', async ({ page }) => {
        const body = page.locator('main p');
        await expect(body).toBeVisible();
      });

      test('has crisis link', async ({ page }) => {
        const link = page.locator('a[href="/crisis"]');
        await expect(link).toBeVisible();
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
});

test.describe('Legal and safety accessibility', () => {
  test('axe scan finds no violations on privacy page', async ({ page }) => {
    await page.goto('/en/privacy');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test('axe scan finds no violations on safety page', async ({ page }) => {
    await page.goto('/en/safety');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});
