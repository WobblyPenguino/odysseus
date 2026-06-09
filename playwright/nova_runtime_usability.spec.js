const { test, expect } = require('@playwright/test');

const baseURL = process.env.NOVA_TEST_BASE_URL || 'http://127.0.0.1:8766';

async function composerIsUsable(page) {
  const input = page.locator('#msg');
  await expect(input).toBeVisible();
  await input.click();
  await input.fill('what can you do?');
  const value = await input.inputValue();
  expect(value).toContain('what can you do');
  const box = await input.boundingBox();
  expect(box).toBeTruthy();
  const topElement = await page.evaluate(({x,y}) => {
    const el = document.elementFromPoint(x, y);
    return el ? { id: el.id, tag: el.tagName, classes: el.className } : null;
  }, { x: box.x + Math.min(20, box.width / 2), y: box.y + Math.min(10, box.height / 2) });
  expect(topElement).toBeTruthy();
}

function overlaps(a, b) {
  return a && b && a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

test('chat help drawers activity cannot cover composer', async ({ page }, testInfo) => {
  const html = await fetch(baseURL).then(r => r.text());
  await page.setContent(html, { waitUntil: 'domcontentloaded' });
  const input = page.locator('#msg');
  await expect(input).toBeVisible();
  await input.fill('hi');
  const chatResponse = await fetch(baseURL + '/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: 'hi' }) }).then(r => r.json());
  expect(chatResponse.reply || chatResponse.ok).toBeTruthy();
  const chatText = JSON.stringify(chatResponse);
  expect(chatText).toMatch(/Nova|Hi|hello|chat/i);
  await page.evaluate((text) => {
    const chat = document.querySelector('#chat, .chat, .messages');
    if (chat) { const div = document.createElement('div'); div.className = 'msg'; div.textContent = text; chat.appendChild(div); }
  }, chatText);

  const help = page.locator('#novaCommandHelpButton').first();
  if (await help.count()) {
    await help.click();
    await expect(page.locator('#novaCommandHelpOverlay')).toBeVisible();
    await page.locator('#novaCommandHelpSearch').fill('code');
    await expect(page.locator('#novaCommandHelpOverlay')).toContainText('/code');
    await page.locator('#novaCommandHelpOverlay button:has-text("Close")').click();
  }

  await page.evaluate(() => {
    const activity = document.getElementById('liveActivityPanel');
    if (activity) activity.classList.remove('is-minimized', 'collapsed', 'hidden');
    document.body.classList.add('orbit-open', 'orbit-drawer-open', 'nova-interaction-overhaul-v1');
    const drawer = document.getElementById('orbitDrawer');
    if (drawer) drawer.style.display = 'block';
    const right = document.getElementById('orbitRightDrawer');
    if (right) right.style.display = 'block';
    if (window.NovaInteractionOverhaul?.scanPanels) window.NovaInteractionOverhaul.scanPanels();
  });

  await composerIsUsable(page);
  const inputBox = await input.boundingBox();
  const panels = await page.locator('#liveActivityPanel, #orbitDrawer, #orbitRightDrawer').evaluateAll(nodes => nodes.map(n => {
    const style = getComputedStyle(n);
    const r = n.getBoundingClientRect();
    return { id: n.id, visible: style.display !== 'none' && style.visibility !== 'hidden' && r.width > 0 && r.height > 0, x: r.x, y: r.y, width: r.width, height: r.height };
  }));
  for (const panel of panels.filter(p => p.visible)) {
    expect(overlaps(inputBox, panel), `${panel.id} overlaps composer`).toBeFalsy();
  }
  await page.screenshot({ path: 'logs/runtime_usability_playwright.png', fullPage: true });
});
