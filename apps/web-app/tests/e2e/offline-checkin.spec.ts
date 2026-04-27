'use client';
/**
 * E2E tests for offline check-in queue behavior.
 * Uses Playwright's context().setOffline() to make navigator.onLine === false,
 * which triggers the offline detection branch in the check-in form's catch block.
 */
import { expect, test } from '@playwright/test';

test.describe('Offline check-in queue', () => {
  test('renders check-in page correctly', async ({ page }) => {
    await page.goto('/en/check-in');
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('form')).toBeVisible();
  });

  test('queue badge not visible when queue is empty', async ({ page }) => {
    await page.goto('/en/check-in');
    const badge = page.locator('[data-testid="check-in-queue-badge"]');
    await expect(badge).not.toBeVisible();
  });

  test('shows offline-queued success card when device goes offline before submit', async ({
    page,
  }) => {
    await page.goto('/en/check-in');

    // Take the device offline — navigator.onLine becomes false, which is
    // sufficient for isOffline=true in the catch block regardless of error type.
    await page.context().setOffline(true);

    try {
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('[data-testid="submit-offline-queued"]')).toBeVisible();
    } finally {
      await page.context().setOffline(false);
    }
  });

  test('queue badge appears after offline submission and reset', async ({ page }) => {
    await page.goto('/en/check-in');

    await page.context().setOffline(true);

    try {
      // Submit while offline to enqueue the check-in
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('[data-testid="submit-offline-queued"]')).toBeVisible();

      // Click "Log another check-in" to go back to the form
      await page.getByRole('button', { name: /log another check-in/i }).click();

      // The form is visible again and the queue badge should now be shown
      // because queuedCount > 0 after the enqueue above
      await expect(page.locator('form')).toBeVisible();
      await expect(page.locator('[data-testid="check-in-queue-badge"]')).toBeVisible();
    } finally {
      await page.context().setOffline(false);
    }
  });
});
