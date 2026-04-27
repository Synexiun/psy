'use client';
/**
 * E2E tests for the patterns pages.
 * Covers: landing (InsightCard rendered, dismiss interaction, detail link),
 * detail (breadcrumb, metadata card, crisis link), PHI audit, i18n, RTL, a11y.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Patterns landing per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/patterns`);
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

      test('insight cards are rendered (stub has 2 active patterns)', async ({ page }) => {
        const items = page.locator('[data-testid^="pattern-item-"]');
        await expect(items).toHaveCount(2);
      });

      test('insight card bodies are visible', async ({ page }) => {
        const bodies = page.locator('[data-testid="insight-body"]');
        await expect(bodies.first()).toBeVisible();
      });

      test('detail links are rendered', async ({ page }) => {
        const links = page.locator('[data-testid^="pattern-detail-link-"]');
        await expect(links.first()).toBeVisible();
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/patterns');
    expect(response?.status()).toBe(404);
  });

  test('PHI audit fires on /patterns mount (POST to /api/audit/phi-read)', async ({ page }) => {
    const auditRequests: string[] = [];
    await page.route('**/api/audit/phi-read', (route) => {
      auditRequests.push(route.request().url());
      void route.fulfill({ status: 200, body: JSON.stringify({ ok: true }) });
    });
    await page.goto('/en/patterns');
    await page.waitForTimeout(500);
    expect(auditRequests.length).toBeGreaterThanOrEqual(1);
  });

  test('dismiss button removes an insight card from the list', async ({ page }) => {
    await page.goto('/en/patterns');
    // Wait for insight cards to render
    await expect(page.locator('[data-testid="insight-headline"]').first()).toBeVisible();
    const initialCount = await page.locator('[data-testid="insight-headline"]').count();
    // Click dismiss on the first card (aria-label="Dismiss" on the InsightCard X button)
    await page.locator('[aria-label="Dismiss"]').first().click();
    // Card should be gone (InsightCard renders null on dismiss)
    const newCount = await page.locator('[data-testid="insight-headline"]').count();
    expect(newCount).toBe(initialCount - 1);
  });
});

test.describe('Patterns landing accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/patterns');
    await expect(page.locator('main')).toBeVisible();
  });

  test('page heading is an h1', async ({ page }) => {
    await page.goto('/en/patterns');
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    expect(await h1.count()).toBe(1);
  });

  test('active patterns section has aria-labelledby landmark', async ({ page }) => {
    await page.goto('/en/patterns');
    await expect(
      page.locator('section[aria-labelledby="active-patterns-heading"]'),
    ).toBeVisible();
  });
});

test.describe('Pattern detail page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/patterns/p1');
  });

  test('renders pattern detail heading', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });

  test('renders breadcrumb back to patterns', async ({ page }) => {
    const backBtn = page.locator('nav[aria-label="Breadcrumb"] button');
    await expect(backBtn).toBeVisible();
  });

  test('renders InsightCard with body', async ({ page }) => {
    await expect(page.locator('[data-testid="insight-body"]').first()).toBeVisible();
  });

  test('crisis link is visible', async ({ page }) => {
    const crisisLink = page.locator('a[href="/en/crisis"]').first();
    await expect(crisisLink).toBeVisible();
  });

  test('PHI audit fires on pattern detail mount', async ({ page }) => {
    const auditRequests: string[] = [];
    await page.route('**/api/audit/phi-read', (route) => {
      auditRequests.push(route.request().url());
      void route.fulfill({ status: 200, body: JSON.stringify({ ok: true }) });
    });
    await page.goto('/en/patterns/p1');
    await page.waitForTimeout(500);
    expect(auditRequests.length).toBeGreaterThanOrEqual(1);
  });
});
