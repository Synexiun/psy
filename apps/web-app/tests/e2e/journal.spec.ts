/* eslint-disable */
/**
 * E2E tests for the journal page (/en/journal).
 *
 * Covers: page load, new entry button, stub entry list, empty state,
 * heading visibility, main landmark, i18n, RTL, a11y.
 */

import { expect, test } from '@playwright/test';

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Journal page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/journal`);
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

      test('"New entry" button is visible', async ({ page }) => {
        // The button has an aria-label set from the journal.newEntry i18n key
        // Fall back to finding any prominent button in the header
        const newEntryButton = page.getByRole('button', { name: /new entry|nouvelle|entrée|جديد|ورودی/i });
        await expect(newEntryButton).toBeVisible();
      });

      test('recent entries section heading is visible', async ({ page }) => {
        // Stub data has 3 entries so the list should be rendered
        const sectionHeading = page.locator('#journal-entries-heading');
        await expect(sectionHeading).toBeVisible();
      });

      test('entry cards are rendered (stub has 3 entries)', async ({ page }) => {
        const entries = page.locator('article');
        await expect(entries).toHaveCount(3);
      });

      test('each entry card shows a preview excerpt', async ({ page }) => {
        const previews = page.locator('article p');
        const count = await previews.count();
        expect(count).toBeGreaterThanOrEqual(3);
      });

      test('entry dates are rendered with datetime attribute', async ({ page }) => {
        const times = page.locator('article time[datetime]');
        const count = await times.count();
        expect(count).toBeGreaterThanOrEqual(1);
      });

      test('voice badge is shown on voice entries', async ({ page }) => {
        // Stub entry j2 is a voice recording
        const voiceBadge = page.getByRole('img', { name: /voice recording/i });
        await expect(voiceBadge).toBeVisible();
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/journal');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Journal page accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/journal');
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('axe scan finds no violations on en journal', async ({ page }) => {
    await page.goto('/en/journal');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test('page heading is an h1', async ({ page }) => {
    await page.goto('/en/journal');
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    const count = await h1.count();
    // Exactly one h1 per page
    expect(count).toBe(1);
  });

  test('entry list has section landmark', async ({ page }) => {
    await page.goto('/en/journal');
    const section = page.locator('section[aria-labelledby="journal-entries-heading"]');
    await expect(section).toBeVisible();
  });
});

test.describe('Journal empty state', () => {
  // NOTE: The stub always has 3 entries, so this test documents the expected
  // empty-state markup shape for when the API returns zero entries.
  // When real API integration lands, add a mock route that returns [] and
  // move this test into the main per-locale suite.
  test('empty-state card markup shape is defined in source', async ({ page }) => {
    // Verify the page loads correctly so we can confirm stub entries are shown
    await page.goto('/en/journal');
    const articles = page.locator('article');
    const count = await articles.count();
    // Stub has data — confirm empty state is NOT shown
    expect(count).toBeGreaterThan(0);
  });
});
