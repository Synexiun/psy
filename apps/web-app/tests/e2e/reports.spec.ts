'use client';
/**
 * E2E tests for the reports pages.
 * Covers: landing (period list, RCIDelta visible), detail (PHQ-9/GAD-7 cards,
 * clinical-number format, FHIR export button, breadcrumb, crisis link),
 * PHI audit fires on mount, i18n, RTL, a11y.
 */

import { expect, test } from '@playwright/test';

// Arabic-Indic digit range: U+0660–U+0669; Persian: U+06F0–U+06F9
const ARABIC_INDIC_DIGITS_PATTERN = /[٠-٩۰-۹]/;

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Reports landing per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/reports`);
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

      test('report period cards are rendered (stub has 2 periods)', async ({ page }) => {
        const cards = page.locator('[data-testid^="report-period-"]');
        await expect(cards).toHaveCount(2);
      });

      test('RCIDelta is visible on period cards', async ({ page }) => {
        const delta = page.locator('[data-testid="rci-delta"]').first();
        await expect(delta).toBeVisible();
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/reports');
    expect(response?.status()).toBe(404);
  });

  test('PHI audit fires on /reports mount (POST to /api/audit/phi-read)', async ({ page }) => {
    const auditRequests: string[] = [];
    await page.route('**/api/audit/phi-read', (route) => {
      auditRequests.push(route.request().url());
      void route.fulfill({ status: 200, body: JSON.stringify({ ok: true }) });
    });
    await page.goto('/en/reports');
    await page.waitForTimeout(500);
    expect(auditRequests.length).toBeGreaterThanOrEqual(1);
  });
});

test.describe('Reports landing accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/reports');
    await expect(page.locator('main')).toBeVisible();
  });

  test('page heading is an h1', async ({ page }) => {
    await page.goto('/en/reports');
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    expect(await h1.count()).toBe(1);
  });

  test('period list has section landmark', async ({ page }) => {
    await page.goto('/en/reports');
    const section = page.locator('section[aria-labelledby="report-periods-heading"]');
    await expect(section).toBeVisible();
  });
});

test.describe('Report detail page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/reports/2026-q1');
  });

  test('renders report heading (period label)', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });

  test('renders breadcrumb back to reports', async ({ page }) => {
    const backBtn = page.locator('nav[aria-label="Breadcrumb"] button');
    await expect(backBtn).toBeVisible();
  });

  test('PHQ-9 card is visible', async ({ page }) => {
    // h2 contains text "PHQ-9"
    await expect(page.locator('text=PHQ-9').first()).toBeVisible();
  });

  test('GAD-7 card is visible', async ({ page }) => {
    await expect(page.locator('text=GAD-7').first()).toBeVisible();
  });

  test('RCIDelta is visible on PHQ-9 card', async ({ page }) => {
    const delta = page.locator('[data-testid="rci-delta"]').first();
    await expect(delta).toBeVisible();
  });

  test('clinical scores use Latin digits (Rule #9 — no Arabic-Indic digits)', async ({ page }) => {
    await page.goto('/ar/reports/2026-q1');
    const scores = page.locator('.clinical-number');
    const count = await scores.count();
    for (let i = 0; i < count; i++) {
      const text = await scores.nth(i).textContent();
      if (text) expect(ARABIC_INDIC_DIGITS_PATTERN.test(text)).toBe(false);
    }
  });

  test('FHIR export button is visible', async ({ page }) => {
    const btn = page.locator('[data-testid="fhir-export-btn"]');
    await expect(btn).toBeVisible();
  });

  test('crisis link is visible', async ({ page }) => {
    const crisisLink = page.locator('a[href="/en/crisis"]').first();
    await expect(crisisLink).toBeVisible();
  });

  test('export section has aria-labelledby landmark', async ({ page }) => {
    const section = page.locator('section[aria-labelledby="fhir-export-heading"]');
    await expect(section).toBeVisible();
  });

  test('PHI audit fires on detail mount', async ({ page }) => {
    const auditRequests: string[] = [];
    await page.route('**/api/audit/phi-read', (route) => {
      auditRequests.push(route.request().url());
      void route.fulfill({ status: 200, body: JSON.stringify({ ok: true }) });
    });
    await page.goto('/en/reports/2026-q1');
    await page.waitForTimeout(500);
    expect(auditRequests.length).toBeGreaterThanOrEqual(1);
  });
});
