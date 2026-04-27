'use client';
/**
 * E2E tests for the crisis page inside the authenticated app.
 *
 * The crisis path is public (no auth gate) per CLAUDE.md non-negotiable rule.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Crisis page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/crisis`);
      });

      test('renders crisis headline', async ({ page }) => {
        const headline = page.locator('h1');
        await expect(headline).toBeVisible();
      });

      test('has emergency tel link', async ({ page }) => {
        const link = page.locator('a[href^="tel:"]').first();
        await expect(link).toBeVisible();
      });

      test('has at least one hotline contact option', async ({ page }) => {
        const hotlines = page.locator('section[aria-labelledby="hotlines"] li');
        const count = await hotlines.count();
        expect(count).toBeGreaterThan(0);
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

test.describe('Crisis page accessibility', () => {
  test('axe scan finds no violations on en crisis page', async ({ page }) => {
    await page.goto('/en/crisis');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});

test.describe('Crisis page — JavaScript disabled', () => {
  test('tel: anchor renders and is visible without JavaScript', async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto('/en/crisis');
    const telLink = page.locator('a[href^="tel:"]').first();
    await expect(telLink).toBeVisible();
    await context.close();
  });

  test('h1 renders without JavaScript (server-rendered HTML)', async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto('/en/crisis');
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    await context.close();
  });

  test('emergency section renders without JavaScript', async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto('/en/crisis');
    const section = page.locator('section[aria-labelledby="emergency"]');
    await expect(section).toBeVisible();
    await context.close();
  });
});
