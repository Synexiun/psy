'use client';
/**
 * E2E tests for the companion screen (/en/companion).
 *
 * Covers: page load, CompassionTemplate visible, three next-step links present,
 * crisis link present, heading, i18n/RTL, a11y.
 *
 * LLM-prohibition is covered by the Vitest unit test (clinical-contracts.test.ts),
 * not E2E.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Companion page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/companion`);
      });

      test('renders page heading', async ({ page }) => {
        await expect(page.locator('h1')).toBeVisible();
      });

      test('sets correct text direction on html', async ({ page }) => {
        const dir = await page.locator('html').getAttribute('dir');
        if (locale === 'ar' || locale === 'fa') {
          expect(dir).toBe('rtl');
        } else {
          expect(dir).toBe('ltr');
        }
      });

      test('sets lang attribute on html', async ({ page }) => {
        expect(await page.locator('html').getAttribute('lang')).toBe(locale);
      });

      test('CompassionTemplate is visible', async ({ page }) => {
        const template = page.locator('[data-testid="compassion-template"]');
        await expect(template).toBeVisible();
      });

      test('check-in next step link is visible', async ({ page }) => {
        const link = page.locator('[data-testid="companion-next-step-checkin"]');
        await expect(link).toBeVisible();
      });

      test('read next step link is visible', async ({ page }) => {
        const link = page.locator('[data-testid="companion-next-step-read"]');
        await expect(link).toBeVisible();
      });

      test('crisis support link is visible', async ({ page }) => {
        const link = page.locator('[data-testid="companion-next-step-crisis"]');
        await expect(link).toBeVisible();
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/companion');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Companion page accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/companion');
    await expect(page.locator('main')).toBeVisible();
  });

  test('page heading is an h1', async ({ page }) => {
    await page.goto('/en/companion');
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    expect(await h1.count()).toBe(1);
  });

  test('next steps section has aria-labelledby landmark', async ({ page }) => {
    await page.goto('/en/companion');
    const section = page.locator('section[aria-labelledby="companion-next-steps-heading"]');
    await expect(section).toBeVisible();
  });
});
