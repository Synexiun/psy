'use client';
/**
 * E2E smoke tests for settings pages.
 * Key coverage: appearance sub-page theme toggle round-trip + locale switch round-trip.
 */

import { expect, test } from '@playwright/test';

const APP_VERSION = '1.0.0-beta';

// ---------------------------------------------------------------------------
// Settings shell
// ---------------------------------------------------------------------------

test.describe('Settings shell', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/settings');
  });

  test('renders h1', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });

  test('has nav rows for Account, Notifications, Appearance, Privacy', async ({ page }) => {
    await expect(page.getByRole('button', { name: /account/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /notifications/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /appearance/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /privacy/i })).toBeVisible();
  });

  test('has main landmark', async ({ page }) => {
    await expect(page.locator('main')).toBeVisible();
  });

  test('has exactly one h1', async ({ page }) => {
    const headings = page.locator('h1');
    await expect(headings).toHaveCount(1);
  });

  test('About version is visible', async ({ page }) => {
    await expect(page.getByText(APP_VERSION)).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Settings appearance sub-page
// ---------------------------------------------------------------------------

test.describe('Settings appearance sub-page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/settings/appearance');
  });

  test('renders h1', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });

  test('theme toggle dark button is present', async ({ page }) => {
    await expect(page.locator('[data-testid="theme-dark-btn"]')).toBeVisible();
  });

  test('theme toggle light button is present', async ({ page }) => {
    await expect(page.locator('[data-testid="theme-light-btn"]')).toBeVisible();
  });

  test('theme toggle round-trip: click light, verify data-theme changes', async ({ page }) => {
    const html = page.locator('html');
    await page.locator('[data-testid="theme-light-btn"]').click();
    // After click, data-theme should be 'light'
    await expect(html).toHaveAttribute('data-theme', 'light');
  });

  test('locale switch round-trip: click fr, verify navigation to /fr/settings/appearance', async ({ page }) => {
    await page.locator('[data-testid="locale-fr-btn"]').click();
    await page.waitForURL('**/fr/settings/appearance');
    expect(page.url()).toContain('/fr/settings/appearance');
  });

  test('locale buttons are present for all 4 locales', async ({ page }) => {
    for (const locale of ['en', 'fr', 'ar', 'fa']) {
      await expect(page.locator(`[data-testid="locale-${locale}-btn"]`)).toBeVisible();
    }
  });

  test('breadcrumb back to settings is visible', async ({ page }) => {
    await expect(page.locator('nav[aria-label="Breadcrumb"] button')).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Settings sub-pages smoke
// ---------------------------------------------------------------------------

test.describe('Settings sub-pages smoke', () => {
  for (const sub of ['account', 'notifications', 'privacy']) {
    test(`${sub} sub-page renders h1`, async ({ page }) => {
      await page.goto(`/en/settings/${sub}`);
      await expect(page.locator('h1')).toBeVisible();
    });

    test(`${sub} sub-page has breadcrumb`, async ({ page }) => {
      await page.goto(`/en/settings/${sub}`);
      await expect(page.locator('nav[aria-label="Breadcrumb"] button')).toBeVisible();
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/settings');
    expect(response?.status()).toBe(404);
  });
});
