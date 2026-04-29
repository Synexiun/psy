'use client';
/**
 * E2E tests for the authenticated user app dashboard.
 *
 * Covers: layout, streak widget, pattern cards, quick actions,
 * state indicator, mood sparkline, crisis CTA, i18n, RTL, a11y.
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
        const cta = page.locator(`a[href="/${locale}/crisis"]`).first();
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

      test('renders streak widgets', async ({ page }) => {
        await expect(page.getByRole('img', { name: /continuous streak/i })).toBeVisible();
        await expect(page.getByRole('img', { name: /resilience streak/i })).toBeVisible();
      });

      test('renders quick action grid', async ({ page }) => {
        const grid = page.locator('section[aria-labelledby="quick-actions"]');
        await expect(grid.getByRole('link', { name: /check in/i })).toBeVisible();
        await expect(grid.getByRole('link', { name: /coping tool/i })).toBeVisible();
        await expect(grid.getByRole('link', { name: /journal/i })).toBeVisible();
        await expect(grid.getByRole('link', { name: /crisis help/i })).toBeVisible();
      });

      test('renders state indicator badge', async ({ page }) => {
        const badge = page.getByRole('region', { name: /current state/i }).first();
        await expect(badge).toBeVisible();
      });

      test('renders mood sparkline', async ({ page }) => {
        const sparkline = page.locator('svg[role="img"][aria-label*="Mood trend"]').first();
        await expect(sparkline).toBeVisible();
      });

      test('renders dashboard hero section with data-testid', async ({ page }) => {
        const hero = page.locator('[data-testid="dashboard-hero"]');
        await expect(hero).toBeVisible();
      });

      test('renders pattern preview tiles (not PatternCard dismiss UI)', async ({ page }) => {
        const tiles = page.locator('[data-testid="pattern-preview-tile"]');
        // Stub data has 2 patterns — at least 1 should be visible.
        await expect(tiles.first()).toBeVisible();
      });

      test('renders "All patterns" link pointing to patterns page', async ({ page }) => {
        const link = page.locator(`a[href="/${locale}/patterns"]`);
        await expect(link).toBeVisible();
      });

      test('crisis link is present in quick actions', async ({ page }) => {
        const crisisLink = page
          .locator('section[aria-labelledby="quick-actions"]')
          .getByRole('link', { name: /crisis help/i });
        await expect(crisisLink).toBeVisible();
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
