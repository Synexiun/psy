/**
 * E2E tests for the public marketing surface.
 *
 * Verifies that every locale renders the hero, crisis CTA, and navigation
 * links correctly. No auth gate — these are public pages.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Marketing home page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/`);
      });

      test('renders hero headline', async ({ page }) => {
        const headline = page.locator('h1#hero');
        await expect(headline).toBeVisible();
      });

      test('renders app name badge', async ({ page }) => {
        const badge = page.locator('text=Discipline OS').first();
        await expect(badge).toBeVisible();
      });

      test('has primary CTA link', async ({ page }) => {
        const cta = page.locator('a[href="#download"]');
        await expect(cta).toBeVisible();
      });

      test('has secondary CTA link', async ({ page }) => {
        const cta = page.locator('a[href="#how-it-works"]');
        await expect(cta).toBeVisible();
      });

      test('crisis section is visible with link to /crisis', async ({ page }) => {
        const crisisSection = page.locator('section[aria-labelledby="crisis-promise"]');
        await expect(crisisSection).toBeVisible();
        const crisisLink = crisisSection.locator('a[href="/crisis"]');
        await expect(crisisLink).toBeVisible();
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

test.describe('Marketing home accessibility', () => {
  test('axe scan finds no violations on en page', async ({ page }) => {
    await page.goto('/en/');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});
