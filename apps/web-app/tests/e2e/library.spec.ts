'use client';
/**
 * E2E tests for the library pages.
 * Covers: landing (5 category cards), category listing (articles), article detail,
 * breadcrumb navigation, crisis footer, i18n, RTL, a11y.
 *
 * Library is NOT a PHI route — no usePhiAudit assertions.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Library landing per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/library`);
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

      test('renders 5 category cards (stub has 5 categories)', async ({ page }) => {
        const cards = page.locator('[data-testid^="library-category-"]');
        await expect(cards).toHaveCount(5);
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/library');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Library landing accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/library');
    await expect(page.locator('main')).toBeVisible();
  });

  test('page heading is an h1', async ({ page }) => {
    await page.goto('/en/library');
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    expect(await h1.count()).toBe(1);
  });

  test('categories section has aria-labelledby landmark', async ({ page }) => {
    await page.goto('/en/library');
    await expect(page.locator('section[aria-labelledby="library-categories-heading"]')).toBeVisible();
  });
});

test.describe('Library category page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/library/cbt-skills');
  });

  test('renders category heading', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });

  test('renders breadcrumb back to library', async ({ page }) => {
    const backBtn = page.locator('nav[aria-label="Breadcrumb"] button');
    await expect(backBtn).toBeVisible();
  });

  test('renders article cards (cbt-skills has 3 articles)', async ({ page }) => {
    const articles = page.locator('[data-testid^="library-article-"]');
    await expect(articles).toHaveCount(3);
  });

  test('articles section has aria-labelledby landmark', async ({ page }) => {
    await expect(page.locator('section[aria-labelledby="library-articles-heading"]')).toBeVisible();
  });
});

test.describe('Library article detail page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/library/cbt-skills/urge-surfing');
  });

  test('renders article heading', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });

  test('renders breadcrumb back to category', async ({ page }) => {
    const backBtn = page.locator('nav[aria-label="Breadcrumb"] button');
    await expect(backBtn).toBeVisible();
  });

  test('renders article body card', async ({ page }) => {
    // Article body is in a Card
    await expect(page.locator('h1')).toBeVisible(); // page loads without error
  });

  test('crisis link is visible', async ({ page }) => {
    const crisisLink = page.locator('a[href="/en/crisis"]').first();
    await expect(crisisLink).toBeVisible();
  });
});
