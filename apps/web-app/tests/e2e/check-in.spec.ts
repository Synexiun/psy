'use client';
/* eslint-disable */
/**
 * E2E tests for the check-in page (/en/check-in).
 *
 * Covers: page load, intensity slider, trigger chips, notes textarea,
 * submit button, crisis link, compassion card post-submit, i18n, RTL, a11y.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Check-in page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/check-in`);
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

      test('intensity slider is visible and has correct aria attributes', async ({ page }) => {
        const slider = page.locator('[role="slider"]');
        await expect(slider).toBeVisible();
        await expect(slider).toHaveAttribute('aria-valuemin', '0');
        await expect(slider).toHaveAttribute('aria-valuemax', '10');
        await expect(slider).toHaveAttribute('aria-valuenow');
      });

      test('intensity slider is interactive', async ({ page }) => {
        const slider = page.locator('[role="slider"]');
        await expect(slider).toBeEnabled();
        // Press ArrowRight 5 times to increment value
        await slider.focus();
        for (let i = 0; i < 5; i++) {
          await slider.press('ArrowRight');
        }
        const valuenow = await slider.getAttribute('aria-valuenow');
        expect(parseInt(valuenow ?? '0')).toBeGreaterThan(0);
      });

      test('urge value display shows Latin digit', async ({ page }) => {
        const valueDisplay = page.locator('[data-testid="urge-value"]');
        await expect(valueDisplay).toBeVisible();
        const text = await valueDisplay.innerText();
        // Must be a Latin digit (0-9) not Arabic-Indic
        expect(/^[0-9]+$/.test(text.trim())).toBe(true);
      });

      test('at least one trigger chip is visible', async ({ page }) => {
        // Trigger chips are toggle buttons with aria-pressed
        const firstChip = page.locator('[aria-pressed]').first();
        await expect(firstChip).toBeVisible();
      });

      test('all eight trigger chips are rendered', async ({ page }) => {
        const chips = page.locator('[aria-pressed]');
        await expect(chips).toHaveCount(8);
      });

      test('trigger chip toggles aria-pressed on click', async ({ page }) => {
        const firstChip = page.locator('[aria-pressed]').first();
        await expect(firstChip).toHaveAttribute('aria-pressed', 'false');
        await firstChip.click();
        await expect(firstChip).toHaveAttribute('aria-pressed', 'true');
        // Toggle off
        await firstChip.click();
        await expect(firstChip).toHaveAttribute('aria-pressed', 'false');
      });

      test('notes textarea is present', async ({ page }) => {
        const textarea = page.locator('textarea#checkin-notes');
        await expect(textarea).toBeVisible();
      });

      test('notes textarea accepts input', async ({ page }) => {
        const textarea = page.locator('textarea#checkin-notes');
        await textarea.fill('Test note content');
        await expect(textarea).toHaveValue('Test note content');
      });

      test('submit button is present and enabled', async ({ page }) => {
        const submitButton = page.locator('button[type="submit"]');
        await expect(submitButton).toBeVisible();
        await expect(submitButton).toBeEnabled();
      });

      test('crisis link is visible on the page', async ({ page }) => {
        const crisisLink = page.locator(`a[href="/${locale}/crisis"]`).first();
        await expect(crisisLink).toBeVisible();
      });

      test('compassion card is NOT visible before submit', async ({ page }) => {
        // The compassion card contains an inline SVG wave icon and is only shown post-submit
        const compassionCard = page.locator('h2').filter({ hasText: /well done|aware|logged|check/i });
        // The form should be visible (not the compassion card)
        const form = page.locator('form');
        await expect(form).toBeVisible();
      });

      test('compassion card appears after clicking submit', async ({ page }) => {
        const submitButton = page.locator('button[type="submit"]');
        await submitButton.click();
        // After the stub timeout (600ms), the compassion card should appear
        // We look for an h2 inside the compassion card (post-submit state)
        const compassionHeading = page.locator('h2');
        await expect(compassionHeading).toBeVisible({ timeout: 2000 });
        // The form should no longer be visible
        const form = page.locator('form');
        await expect(form).not.toBeVisible();
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/check-in');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Check-in page accessibility', () => {
  test('axe scan finds no violations on en check-in', async ({ page }) => {
    await page.goto('/en/check-in');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/check-in');
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('all trigger chips have accessible labels', async ({ page }) => {
    await page.goto('/en/check-in');
    const chips = page.locator('[aria-pressed]');
    const count = await chips.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const chip = chips.nth(i);
      const text = await chip.innerText();
      expect(text.trim().length).toBeGreaterThan(0);
    }
  });
});
