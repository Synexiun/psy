'use client';
/**
 * E2E tests for the coping tools page (/en/tools).
 *
 * Covers: page load, tools heading, featured Box Breathing card,
 * tool card count, anchor elements, crisis link via layout nav,
 * i18n, RTL, a11y.
 *
 * The tools catalogue is entirely static / deterministic (no API call,
 * works offline). TOOLS array has 8 items (1 featured + 7 in grid).
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Tools page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/tools`);
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

      test('featured tool section is visible', async ({ page }) => {
        const featuredSection = page.locator('section[aria-labelledby="featured-tool-heading"]');
        await expect(featuredSection).toBeVisible();
      });

      test('featured tool is Box Breathing (links to /tools/box-breathing)', async ({ page }) => {
        const boxBreathingLink = page.locator(`a[href="/${locale}/tools/box-breathing"]`).first();
        await expect(boxBreathingLink).toBeVisible();
      });

      test('featured tool anchor has aria-label mentioning the tool name', async ({ page }) => {
        const featuredSection = page.locator('section[aria-labelledby="featured-tool-heading"]');
        const featuredAnchor = featuredSection.locator('a').first();
        await expect(featuredAnchor).toBeVisible();
        const ariaLabel = await featuredAnchor.getAttribute('aria-label');
        expect(ariaLabel).toBeTruthy();
        expect(ariaLabel!.length).toBeGreaterThan(0);
      });

      test('all-tools grid renders at least 4 tool cards', async ({ page }) => {
        // 7 non-featured tools rendered as <a> elements inside the grid section
        const allToolsSection = page.locator('section[aria-labelledby="all-tools-heading"]');
        const toolAnchors = allToolsSection.locator('a');
        const count = await toolAnchors.count();
        expect(count).toBeGreaterThanOrEqual(4);
      });

      test('each tool card in the grid is an anchor element', async ({ page }) => {
        const allToolsSection = page.locator('section[aria-labelledby="all-tools-heading"]');
        const toolAnchors = allToolsSection.locator('a');
        const count = await toolAnchors.count();
        expect(count).toBeGreaterThan(0);
        for (let i = 0; i < count; i++) {
          const href = await toolAnchors.nth(i).getAttribute('href');
          expect(href).toBeTruthy();
          expect(href).toMatch(new RegExp(`^/${locale}/tools/`));
        }
      });

      test('tool cards have accessible aria-labels', async ({ page }) => {
        const allToolsSection = page.locator('section[aria-labelledby="all-tools-heading"]');
        const toolAnchors = allToolsSection.locator('a[aria-label]');
        const count = await toolAnchors.count();
        expect(count).toBeGreaterThanOrEqual(4);
        for (let i = 0; i < count; i++) {
          const label = await toolAnchors.nth(i).getAttribute('aria-label');
          expect(label).toBeTruthy();
          expect(label!.trim().length).toBeGreaterThan(0);
        }
      });

      test('crisis link is accessible via the Layout nav', async ({ page }) => {
        const crisisLink = page.locator(`a[href="/${locale}/crisis"]`).first();
        await expect(crisisLink).toBeVisible();
      });

      test('total tool anchors on page equals 8 (1 featured + 7 in grid)', async ({ page }) => {
        // Featured tool link + 7 grid cards = 8 total tool anchors
        const allToolAnchors = page.locator(`a[href^="/${locale}/tools/"]`);
        const count = await allToolAnchors.count();
        expect(count).toBe(8);
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/tools');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Tools page accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/tools');
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('axe scan finds no violations on en tools', async ({ page }) => {
    await page.goto('/en/tools');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test('page has exactly one h1', async ({ page }) => {
    await page.goto('/en/tools');
    const h1 = page.locator('h1');
    const count = await h1.count();
    expect(count).toBe(1);
  });

  test('tool categories render badge text for each card', async ({ page }) => {
    await page.goto('/en/tools');
    const allToolsSection = page.locator('section[aria-labelledby="all-tools-heading"]');
    // Each card has an h3 for the tool name
    const toolNames = allToolsSection.locator('h3');
    const count = await toolNames.count();
    expect(count).toBeGreaterThanOrEqual(4);
    for (let i = 0; i < count; i++) {
      const text = await toolNames.nth(i).innerText();
      expect(text.trim().length).toBeGreaterThan(0);
    }
  });
});

test.describe('Tool detail page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/tools/box-breathing');
  });

  test('renders tool name as h1', async ({ page }) => {
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
  });

  test('renders breadcrumb back link to /tools', async ({ page }) => {
    const backLink = page.locator('nav[aria-label="Breadcrumb"] a');
    await expect(backLink).toBeVisible();
    const href = await backLink.getAttribute('href');
    expect(href).toBe('/en/tools');
  });

  test('renders start button for box breathing', async ({ page }) => {
    const startBtn = page.getByRole('button', { name: /start/i });
    await expect(startBtn).toBeVisible();
  });

  test('crisis link is visible on detail page', async ({ page }) => {
    const crisisLink = page.locator('a[href="/en/crisis"]').first();
    await expect(crisisLink).toBeVisible();
  });

  test('invalid tool slug returns 404', async ({ page }) => {
    const response = await page.goto('/en/tools/not-a-real-tool');
    expect(response?.status()).toBe(404);
  });
});
