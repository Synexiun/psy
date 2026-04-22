/**
 * E2E tests for the crisis surface.
 *
 * These run against the Next.js dev server (fast iteration) and verify:
 * - The page renders for every supported locale
 * - Emergency and hotline contact links are present with correct protocols
 * - RTL layout is applied for Arabic and Persian
 * - The page is accessible (axe scan)
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Crisis page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/`);
      });

      test('renders headline', async ({ page }) => {
        const headline = page.locator('h1');
        await expect(headline).toBeVisible();
        const text = await headline.textContent();
        expect(text?.length).toBeGreaterThan(0);
      });

      test('has emergency call link with tel protocol', async ({ page }) => {
        const emergencyLink = page.locator('a[href^="tel:"]').first();
        await expect(emergencyLink).toBeVisible();
        const href = await emergencyLink.getAttribute('href');
        expect(href).toMatch(/^tel:[\d+]+$/);
      });

      test('has at least one hotline contact option', async ({ page }) => {
        const hotlineLinks = page.locator('ul li a[href^="tel:"], ul li a[href^="sms:"]');
        await expect(hotlineLinks.first()).toBeVisible();
        const count = await hotlineLinks.count();
        expect(count).toBeGreaterThan(0);
      });

      test('sets correct text direction', async ({ page }) => {
        const wrapper = page.locator('div[dir]');
        await expect(wrapper).toBeVisible();
        const dir = await wrapper.getAttribute('dir');
        if (locale === 'ar' || locale === 'fa') {
          expect(dir).toBe('rtl');
        } else {
          expect(dir).toBe('ltr');
        }
      });

      test('has lang attribute on wrapper', async ({ page }) => {
        const wrapper = page.locator(`div[lang="${locale}"]`);
        await expect(wrapper).toBeVisible();
      });

      test('footer shows last verified date', async ({ page }) => {
        const footer = page.locator('footer');
        await expect(footer).toBeVisible();
        const text = await footer.textContent();
        expect(text).toContain('Last verified');
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Accessibility', () => {
  test('axe scan finds no violations on en page', async ({ page }, testInfo) => {
    await page.goto('/en/');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
