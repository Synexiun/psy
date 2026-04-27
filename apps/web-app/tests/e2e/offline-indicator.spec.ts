'use client';
/**
 * E2E tests for the OfflineIndicator component.
 *
 * Covers:
 *  1. No offline badge visible when online and queue empty
 *  2. Badge visible when the browser context is set offline
 *  3. Badge can be clicked to expand the status panel
 */

import { expect, test } from '@playwright/test';

test.describe('OfflineIndicator', () => {
  test('no offline badge visible when online and queue empty', async ({ page }) => {
    await page.goto('/en/');

    // The pill button carries aria-label containing "pending" or "Offline"
    // when it renders. When the queue is empty and we are online it must
    // not be in the DOM at all.
    const badge = page.locator('button[aria-label*="pending"], button[aria-label*="Offline"]');
    await expect(badge).toHaveCount(0);
  });

  test('offline badge is visible when context is offline', async ({ page, context }) => {
    await page.goto('/en/');

    // Take the browser context offline — Playwright emulates the 'offline'
    // network event and sets navigator.onLine = false.
    await context.setOffline(true);

    // Wait for the pill to appear. The component listens to the `offline`
    // window event and rerenders synchronously.
    const badge = page.locator('button[aria-label*="Offline"]');
    await expect(badge).toBeVisible({ timeout: 3000 });

    // Restore connectivity so subsequent tests start clean.
    await context.setOffline(false);
  });

  test('clicking the offline badge expands the status panel', async ({ page, context }) => {
    await page.goto('/en/');
    await context.setOffline(true);

    const badge = page.locator('button[aria-label*="Offline"]');
    await expect(badge).toBeVisible({ timeout: 3000 });

    // Panel should be hidden before click
    const panel = page.locator('#offline-indicator-panel');
    await expect(panel).toHaveCount(0);

    await badge.click();

    // Panel should now be visible with live region and status message
    await expect(panel).toBeVisible();
    await expect(panel).toHaveAttribute('role', 'status');
    await expect(panel).toHaveAttribute('aria-live', 'polite');
    await expect(panel).toContainText('Offline');

    await context.setOffline(false);
  });
});
