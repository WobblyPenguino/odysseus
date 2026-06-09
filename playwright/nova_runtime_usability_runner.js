const { chromium } = require('playwright');
const fs = require('fs');

const baseURL = process.env.NOVA_TEST_BASE_URL || 'http://localhost:8766';
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || '/usr/lib/chromium/chromium';

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}
function overlaps(a, b) {
  return a && b && a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}
async function withTimeout(promise, ms, label) {
  let t;
  const timeout = new Promise((_, reject) => { t = setTimeout(() => reject(new Error(label + ' timed out after ' + ms + 'ms')), ms); });
  try { return await Promise.race([promise, timeout]); }
  finally { clearTimeout(t); }
}

(async () => {
  let browser;
  const evidence = { ok: false, baseURL, steps: [] };
  try {
    const html = await withTimeout(fetch(baseURL).then(r => r.text()), 10000, 'fetch html');
    evidence.steps.push('fetched server html');
    const chatResponse = await withTimeout(fetch(baseURL + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'hi' }),
    }).then(r => r.json()), 12000, 'server chat');
    const chatText = JSON.stringify(chatResponse);
    assert(chatResponse.reply && /Nova|Hi|hello|chat/i.test(chatText), 'server chat did not produce useful reply');
    evidence.steps.push('server chat returned useful reply');

    browser = await chromium.launch({
      executablePath,
      headless: true,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security', '--allow-insecure-localhost', '--disable-gpu', '--disable-software-rasterizer'],
    });
    const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
    await withTimeout(page.setContent(html, { waitUntil: 'domcontentloaded' }), 15000, 'setContent');
    evidence.steps.push('browser rendered Nova HTML');

    const input = page.locator('#msg');
    await withTimeout(input.waitFor({ state: 'visible' }), 10000, 'composer visible');
    await input.fill('what can you do?');
    assert((await input.inputValue()).includes('what can you do'), 'composer could not be edited');
    evidence.steps.push('composer editable before drawers');

    const hasHelp = await page.locator('#novaCommandHelpButton').count();
    if (hasHelp) {
      const helpButton = page.locator('#novaCommandHelpButton');
      if (await helpButton.isVisible().catch(() => false)) await helpButton.click();
      else await page.evaluate(() => window.NovaInteractionOverhaul?.commandHelp && window.NovaInteractionOverhaul.commandHelp());
      await withTimeout(page.locator('#novaCommandHelpOverlay').waitFor({ state: 'visible' }), 5000, 'help overlay visible');
      await page.locator('#novaCommandHelpSearch').fill('code');
      const overlayText = await page.locator('#novaCommandHelpOverlay').innerText();
      assert(overlayText.includes('/code'), 'command help search did not show /code');
      await page.locator('#novaCommandHelpOverlay button').filter({ hasText: 'Close' }).click();
      evidence.steps.push('searchable command help works');
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
    await input.fill('composer remains usable');
    assert((await input.inputValue()).includes('composer remains usable'), 'composer not editable after drawers/activity');
    const inputBox = await input.boundingBox();
    assert(inputBox, 'composer has no bounding box');
    const panels = await page.locator('#liveActivityPanel, #orbitDrawer, #orbitRightDrawer').evaluateAll(nodes => nodes.map(n => {
      const style = getComputedStyle(n); const r = n.getBoundingClientRect();
      return { id: n.id, visible: style.display !== 'none' && style.visibility !== 'hidden' && r.width > 0 && r.height > 0, x: r.x, y: r.y, width: r.width, height: r.height };
    }));
    for (const panel of panels.filter(p => p.visible)) assert(!overlaps(inputBox, panel), panel.id + ' overlaps composer');
    await page.screenshot({ path: 'logs/runtime_usability_playwright.png', fullPage: true });
    evidence.steps.push('drawer/activity geometry does not cover composer');
    evidence.ok = true;
    console.log(JSON.stringify(evidence, null, 2));
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
})().catch(err => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
