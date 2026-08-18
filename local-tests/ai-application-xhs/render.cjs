/**
 * render.cjs — Playwright screenshot renderer for bold-contrast-design cards.
 *
 * Usage:
 *   1. Copy this file into your task folder (same dir as index.html).
 *   2. Edit the `targets` array below: [CSS selector, output filename].
 *   3. Run:  node render.cjs
 *
 * Requirements:
 *   npm install playwright  (and: npx playwright install chromium)
 *
 * Output: 2× resolution PNGs into ./output/
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// ─── EDIT THIS ───────────────────────────────────────────────
const targets = [
  ['#xhs-01', 'xhs-01-cover.png'],
  ['#xhs-02', 'xhs-02-scene.png'],
  ['#xhs-03', 'xhs-03-pricing.png'],
  ['#xhs-04', 'xhs-04-safety.png'],
  ['#xhs-05', 'xhs-05-rules.png'],
  ['#xhs-06', 'xhs-06-formula.png'],
];
// ─────────────────────────────────────────────────────────────

const outDir = path.join(__dirname, 'output');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1200, height: 1600 },
    deviceScaleFactor: 2,
  });

  const htmlPath = path.join(__dirname, 'index.html');
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle' });

  // Wait for web fonts to load
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);

  for (const [selector, filename] of targets) {
    const el = await page.$(selector);
    if (!el) {
      console.error(`SKIP: ${selector} not found`);
      continue;
    }
    await el.screenshot({ path: path.join(outDir, filename) });
    console.log('OK:', filename);
  }

  await browser.close();
  console.log('Done.');
})();
