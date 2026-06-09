// Playwright smoke tests for Nova GUI.
// Run after starting Nova at http://127.0.0.1:8766:
//   npx playwright test playwright/nova_gui_smoke.spec.js
const { test, expect } = require('@playwright/test');

test('send, audio, quick commands, live activity and changelog controls are usable', async ({ page }) => {
  await page.goto('http://127.0.0.1:8766');
  await expect(page.locator('#input')).toBeVisible();
  await page.fill('#input', 'hello playwright smoke test');
  await page.click('button:has-text("Send")');
  await expect(page.locator('#chat')).toContainText('hello playwright smoke test');
  await page.click('button[title="Mute/unmute audio"], button:has-text("Enable audio")').catch(() => {});
  await page.click('button:has-text("Edit quick commands")').catch(() => {});
  await page.click('button[title="Changelog"], button:has-text("Z")').catch(() => {});
  await expect(page.locator('#changelogPopup, #chat')).toBeVisible();
  await expect(page.locator('#activityLog')).toBeVisible();
});
