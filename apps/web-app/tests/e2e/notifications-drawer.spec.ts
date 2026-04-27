/**
 * E2E tests for the NotificationsDrawer (spec §5.4, §6.6).
 *
 * The drawer opens via the bell button in the TopBar. It renders stub
 * notifications in a Sheet panel that slides in from the right.
 *
 * Covers:
 * - Bell button is visible in the TopBar
 * - Clicking bell button opens the drawer
 * - Drawer has accessible title "Notifications"
 * - Drawer shows stub notification items
 * - Close button dismisses the drawer
 * - Drawer is not visible before bell click
 */

import { test, expect } from '@playwright/test';

test.describe('NotificationsDrawer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/en/');
  });

  test('bell button is visible in the TopBar', async ({ page }) => {
    const bell = page.getByRole('button', { name: /notification/i });
    await expect(bell).toBeVisible();
  });

  test('clicking bell button opens the notifications drawer', async ({ page }) => {
    await page.getByRole('button', { name: /notification/i }).click();
    const dialog = page.getByRole('dialog', { name: /notification/i });
    await expect(dialog).toBeVisible();
  });

  test('drawer has accessible title "Notifications"', async ({ page }) => {
    await page.getByRole('button', { name: /notification/i }).click();
    const title = page.getByRole('heading', { name: 'Notifications' });
    await expect(title).toBeVisible();
  });

  test('drawer shows stub notification items', async ({ page }) => {
    await page.getByRole('button', { name: /notification/i }).click();
    // Stub has 3 notifications — expect at least one list item
    const items = page.locator('[role="dialog"] li');
    await expect(items.first()).toBeVisible();
  });

  test('close button dismisses the drawer', async ({ page }) => {
    await page.getByRole('button', { name: /notification/i }).click();
    await page.getByRole('button', { name: /close notification/i }).click();
    const dialog = page.getByRole('dialog', { name: /notification/i });
    await expect(dialog).not.toBeVisible();
  });

  test('drawer is not visible before bell click', async ({ page }) => {
    const dialog = page.getByRole('dialog', { name: /notification/i });
    await expect(dialog).not.toBeVisible();
  });
});
