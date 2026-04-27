'use client';
/**
 * E2E tests for the notifications preferences page (/[locale]/settings/notifications).
 *
 * Covers:
 * - Page heading renders
 * - Push toggle is present and toggleable (role="switch")
 * - Email toggle is present
 * - Nudge frequency <select> is present and has all three options
 * - Per-locale rendering (heading visible, dir, lang) for all 4 locales
 * - Invalid locale /de/settings/notifications → 404
 * - Section landmark aria-labelledby
 * - Axe accessibility scan
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

// ---------------------------------------------------------------------------
// Per-locale tests
// ---------------------------------------------------------------------------

test.describe('Notifications preferences page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/settings/notifications`);
      });

      test('renders page heading', async ({ page }) => {
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
    const response = await page.goto('/de/settings/notifications');
    expect(response?.status()).toBe(404);
  });
});

// ---------------------------------------------------------------------------
// Functional tests (en)
// ---------------------------------------------------------------------------

test.describe('Notifications preferences page — functional (en)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/settings/notifications');
  });

  test('renders h1', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });

  test('push toggle is present', async ({ page }) => {
    const toggle = page.locator('#toggle-push[role="switch"]');
    await expect(toggle).toBeVisible();
  });

  test('push toggle is toggleable', async ({ page }) => {
    const toggle = page.locator('#toggle-push[role="switch"]');
    const initialChecked = await toggle.getAttribute('aria-checked');
    await toggle.click();
    const newChecked = await toggle.getAttribute('aria-checked');
    expect(newChecked).not.toBe(initialChecked);
  });

  test('email toggle is present', async ({ page }) => {
    const toggle = page.locator('#toggle-email[role="switch"]');
    await expect(toggle).toBeVisible();
  });

  test('email toggle is toggleable', async ({ page }) => {
    const toggle = page.locator('#toggle-email[role="switch"]');
    const initialChecked = await toggle.getAttribute('aria-checked');
    await toggle.click();
    const newChecked = await toggle.getAttribute('aria-checked');
    expect(newChecked).not.toBe(initialChecked);
  });

  test('nudge frequency select is present', async ({ page }) => {
    const select = page.locator('#nudge-frequency');
    await expect(select).toBeVisible();
  });

  test('nudge frequency select has low option', async ({ page }) => {
    const option = page.locator('#nudge-frequency option[value="low"]');
    await expect(option).toBeAttached();
  });

  test('nudge frequency select has medium option', async ({ page }) => {
    const option = page.locator('#nudge-frequency option[value="medium"]');
    await expect(option).toBeAttached();
  });

  test('nudge frequency select has high option', async ({ page }) => {
    const option = page.locator('#nudge-frequency option[value="high"]');
    await expect(option).toBeAttached();
  });

  test('nudge frequency select defaults to medium', async ({ page }) => {
    const select = page.locator('#nudge-frequency');
    await expect(select).toHaveValue('medium');
  });

  test('nudge frequency select is changeable', async ({ page }) => {
    const select = page.locator('#nudge-frequency');
    await select.selectOption('high');
    await expect(select).toHaveValue('high');
  });

  test('breadcrumb back to settings is visible', async ({ page }) => {
    const backBtn = page.locator('nav[aria-label="Breadcrumb"] button');
    await expect(backBtn).toBeVisible();
  });

  test('nudge section has aria-labelledby landmark', async ({ page }) => {
    const section = page.locator('section[aria-labelledby="nudge-section-heading"]');
    await expect(section).toBeVisible();
  });

  test('nudge section heading text is visible', async ({ page }) => {
    const heading = page.locator('#nudge-section-heading');
    await expect(heading).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

test.describe('Notifications preferences page — accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/settings/notifications');
    await expect(page.locator('main')).toBeVisible();
  });

  test('page has exactly one h1', async ({ page }) => {
    await page.goto('/en/settings/notifications');
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
  });

  test('axe scan finds no violations on en notifications preferences', async ({ page }) => {
    await page.goto('/en/settings/notifications');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});
