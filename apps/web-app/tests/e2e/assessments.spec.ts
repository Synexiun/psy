/* eslint-disable */
/**
 * E2E tests for the assessments page (/en/assessments).
 *
 * Covers: page load, validated instrument names (PHQ-9, GAD-7, WHO-5, AUDIT-C, PSS-10),
 * disclaimer note, "Take assessment" buttons, Latin-digit enforcement on clinical scores,
 * progress rings, i18n, RTL, a11y.
 *
 * Clinical-grade rules enforced here:
 *   - Instrument names must match published validated names (CLAUDE.md rule — no paraphrase)
 *   - Score values must be Latin digits (CLAUDE.md rule 9)
 *   - Disclaimer must be visible (regulatory requirement)
 */

import { expect, test } from '@playwright/test';

// Arabic-Indic digit range: U+0660–U+0669; Persian: U+06F0–U+06F9
const ARABIC_INDIC_DIGITS_PATTERN = /[٠-٩۰-۹]/;

const LOCALES = ['en', 'fr', 'ar', 'fa'] as const;

test.describe('Assessments page per locale', () => {
  for (const locale of LOCALES) {
    test.describe(`locale: ${locale}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto(`/${locale}/assessments`);
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

      test('PHQ-9 instrument card is present', async ({ page }) => {
        // The aria-label on the progress ring uses the instrument's validated short name
        const phq9Ring = page.locator('[aria-label*="PHQ-9"]').first();
        await expect(phq9Ring).toBeVisible();
      });

      test('GAD-7 instrument card is present', async ({ page }) => {
        const gad7Ring = page.locator('[aria-label*="GAD-7"]').first();
        await expect(gad7Ring).toBeVisible();
      });

      test('WHO-5 instrument card is present', async ({ page }) => {
        const who5Ring = page.locator('[aria-label*="WHO-5"]').first();
        await expect(who5Ring).toBeVisible();
      });

      test('AUDIT-C instrument card is present', async ({ page }) => {
        const auditRing = page.locator('[aria-label*="AUDIT-C"]').first();
        await expect(auditRing).toBeVisible();
      });

      test('PSS-10 instrument card is present', async ({ page }) => {
        const pss10Ring = page.locator('[aria-label*="PSS-10"]').first();
        await expect(pss10Ring).toBeVisible();
      });

      test('all 5 instrument cards are rendered', async ({ page }) => {
        // Each card is a <article>-less Card div — identify by the "Take assessment" buttons
        const takeButtons = page.getByRole('button', { name: /take assessment|passer|évaluation|أجر|ارزیابی/i });
        const count = await takeButtons.count();
        expect(count).toBe(5);
      });

      test('"Take assessment" button is present for at least one instrument', async ({ page }) => {
        const takeButton = page.getByRole('button', { name: /take assessment|passer|évaluation|أجر|ارزیابی/i }).first();
        await expect(takeButton).toBeVisible();
      });

      test('clinical disclaimer note is visible', async ({ page }) => {
        const disclaimer = page.locator('[role="note"][aria-label="Clinical disclaimer"]');
        await expect(disclaimer).toBeVisible();
      });

      test('disclaimer contains non-empty text', async ({ page }) => {
        const disclaimer = page.locator('[role="note"][aria-label="Clinical disclaimer"]');
        const text = await disclaimer.innerText();
        expect(text.trim().length).toBeGreaterThan(0);
      });
    });
  }

  test('invalid locale returns 404', async ({ page }) => {
    const response = await page.goto('/de/assessments');
    expect(response?.status()).toBe(404);
  });
});

test.describe('Assessments — Latin digit enforcement (CLAUDE.md rule 9)', () => {
  /**
   * Clinical scores must always be rendered as Latin digits regardless of locale.
   * This test checks that elements carrying clinical-number class (applied by
   * formatNumberClinical) do not contain Arabic-Indic or Extended Arabic-Indic digits.
   * Reference: Kroenke 2001, Spitzer 2006 — score totals are numeric and must be
   * readable identically across locales.
   */
  for (const locale of LOCALES) {
    test(`locale ${locale}: clinical score elements contain only Latin digits`, async ({ page }) => {
      await page.goto(`/${locale}/assessments`);

      // Collect all elements that hold clinical numeric values:
      // 1. Elements with .clinical-number class (applied by formatNumberClinical)
      // 2. aria-labels on progress rings that include the score
      const clinicalNumberEls = page.locator('.clinical-number');
      const count = await clinicalNumberEls.count();

      for (let i = 0; i < count; i++) {
        const text = await clinicalNumberEls.nth(i).innerText();
        expect(ARABIC_INDIC_DIGITS_PATTERN.test(text)).toBe(false);
      }
    });

    test(`locale ${locale}: progress ring aria-labels contain only Latin digits`, async ({ page }) => {
      await page.goto(`/${locale}/assessments`);

      // Progress rings carry aria-label="PHQ-9 score: 8 out of 27" — scores must be Latin
      const rings = page.locator('[aria-label*=" score: "]');
      const count = await rings.count();
      // We have stub scores for PHQ-9, GAD-7, AUDIT-C, WHO-5 (PSS-10 has no score yet)
      expect(count).toBeGreaterThanOrEqual(4);

      for (let i = 0; i < count; i++) {
        const label = await rings.nth(i).getAttribute('aria-label');
        expect(label).toBeTruthy();
        expect(ARABIC_INDIC_DIGITS_PATTERN.test(label!)).toBe(false);
      }
    });
  }
});

test.describe('Assessments page accessibility', () => {
  test('page has main landmark', async ({ page }) => {
    await page.goto('/en/assessments');
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('axe scan finds no violations on en assessments', async ({ page }) => {
    await page.goto('/en/assessments');
    const { default: AxeBuilder } = await import('@axe-core/playwright');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test('page has exactly one h1', async ({ page }) => {
    await page.goto('/en/assessments');
    const h1 = page.locator('h1');
    const count = await h1.count();
    expect(count).toBe(1);
  });

  test('instruments grid has accessible section landmark', async ({ page }) => {
    await page.goto('/en/assessments');
    const section = page.locator('section[aria-labelledby="assessments-grid-heading"]');
    await expect(section).toBeVisible();
  });

  test('instruments grid heading is visually hidden but present for screen readers', async ({ page }) => {
    await page.goto('/en/assessments');
    const heading = page.locator('#assessments-grid-heading');
    // The heading uses sr-only class — it exists in the DOM even if visually hidden
    await expect(heading).toBeAttached();
  });

  test('PSS-10 card shows "not yet taken" state without a score', async ({ page }) => {
    await page.goto('/en/assessments');
    // PSS-10 stub has no score — its ring shows dashed border, aria-label says "no score yet"
    const noScoreEl = page.locator('[aria-label*="PSS-10"][aria-label*="no score yet"]');
    await expect(noScoreEl).toBeVisible();
  });
});
